# =====================================================================
# MetaLearningEngine V15 — PER + EMA + Momentum + Session-Aware Updates
# =====================================================================

from __future__ import annotations
import numpy as np
from typing import Dict, Any, List
import time


class MetaLearningEngine:

    def __init__(
        self,
        reward_fn,
        meta_params: Dict[str, float] | None = None,
        lr: float = 0.02,
        momentum: float = 0.9,
        grad_clip: float = 5.0,
        ema_alpha: float = 0.01,
    ):
        # 메타 파라미터 초기화
        self.params = meta_params if meta_params else {
            "signal_weight": 1.0,
            "regime_weight": 1.0,
            "vol_penalty": 1.0,
            "spread_penalty": 1.0,
            "candidate_boost": 1.0,
        }

        self.reward_fn = reward_fn

        # 학습 하이퍼파라미터
        self.lr = lr
        self.base_lr = lr
        self.momentum = momentum
        self.grad_clip = grad_clip

        # 모멘텀 버퍼
        self.grad_momentum = {k: 0.0 for k in self.params}

        # EMA 기반 reward scale stabilization
        self.reward_ema = 1.0
        self.ema_alpha = ema_alpha

        # debug
        self.history = []

    # -------------------------------------------------------------
    # Session-aware LR
    # -------------------------------------------------------------
    def adjust_lr_by_session(self, session: str):
        """
        session: "ASIA", "EUROPE", "US"
        """
        if session == "ASIA":
            self.lr = self.base_lr * 0.6   # 변동성 낮음 → 안정적으로 미세 조정
        elif session == "EUROPE":
            self.lr = self.base_lr * 0.9   # 중간 변동성
        elif session == "US":
            self.lr = self.base_lr * 1.2   # 변동성 최고 → 빠르게 적응
        else:
            self.lr = self.base_lr

    # -------------------------------------------------------------
    # Compute gradients
    # -------------------------------------------------------------
    def _compute_gradients(self, experiences, weights):
        grads = {k: 0.0 for k in self.params}

        for exp, w in zip(experiences, weights):

            r, dbg = self.reward_fn.compute(
                pnl=exp.reward,
                vol=exp.state.get("vol", 0.01),
                max_dd=exp.state.get("dd", 0.0),
                recent_vol=exp.state.get("recent_vol", 0.01),
                market=exp.market,
                loss_streak=exp.state.get("loss_streak", 0),
            )

            # prevent NaN
            if np.isnan(r) or np.isinf(r):
                continue

            # EMA for scaling
            self.reward_ema = (1 - self.ema_alpha) * self.reward_ema + self.ema_alpha * abs(r)
            scaled_r = r / (self.reward_ema + 1e-6)

            # gradient signal
            g = scaled_r * w

            grads["signal_weight"] += g * exp.meta_score
            grads["regime_weight"] += g * exp.state.get("regime_score", 0)
            grads["vol_penalty"] += g * (-exp.state.get("vol", 0))
            grads["spread_penalty"] += g * (-exp.state.get("spread", 0))
            grads["candidate_boost"] += g * (1 if exp.state.get("is_candidate") else 0)

        return grads

    # -------------------------------------------------------------
    # Gradient clipping
    # -------------------------------------------------------------
    def _clip(self, g: float):
        if abs(g) > self.grad_clip:
            return np.sign(g) * self.grad_clip
        return g

    # -------------------------------------------------------------
    # Update meta-parameters
    # -------------------------------------------------------------
    def update(self, experiences, is_weights, session="US"):

        if not experiences:
            return {"status": "no_data"}

        # LR 조정
        self.adjust_lr_by_session(session)

        # gradient 계산
        grads = self._compute_gradients(experiences, is_weights)

        # momentum 적용 및 파라미터 업데이트
        for k in self.params:

            # momentum buffer update
            self.grad_momentum[k] = (
                self.momentum * self.grad_momentum[k]
                + (1 - self.momentum) * grads[k]
            )

            g = self._clip(self.grad_momentum[k])

            # update
            self.params[k] += self.lr * g

        # debug 저장
        dbg = {
            "timestamp": time.time(),
            "lr": self.lr,
            "params": dict(self.params),
            "grads": dict(grads),
            "reward_ema": self.reward_ema,
        }
        self.history.append(dbg)

        return dbg

    # -------------------------------------------------------------
    # Export meta params
    # -------------------------------------------------------------
    def get_params(self):
        return dict(self.params)
