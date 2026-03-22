# =====================================================================
#  LR Scheduler V19 — Market × Session × Reward Adaptive LR Engine
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import numpy as np
from typing import Dict, Any, Optional


# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------
def safe_float(x, default=0.0):
    """Convert to float safely."""
    try:
        v = float(x)
        if np.isnan(v) or np.isinf(v):
            return default
        return v
    except:
        return default


# ---------------------------------------------------------------------
# LR Scheduler V19
# ---------------------------------------------------------------------
@dataclass
class LRSchedulerV19:
    """
    학습률 스케줄러 V19
    - 시장/세션/보상 기반 적응형 LR
    - EMA + MAD 혼합 정규화
    - Joint Multiplier (시장 × 세션)
    - Reward 안전성 강화
    - Warm-up 단계 지원
    - Debug 정보 완전 강화
    """

    cfg: Dict[str, Any]
    reward_history: deque = field(default_factory=lambda: deque(maxlen=5000))
    reward_ema: float = 0.0
    last_reward: float = 0.0

    # 세션 정규화
    def _normalize_session(self, s: Optional[str]) -> str:
        if s is None:
            return "other"
        return str(s).lower().strip()

    # 보상 업데이트 (EMA + history 기록)
    def _update_reward(self, r: float, alpha: float = 0.1):
        r = safe_float(r, 0.0)
        self.reward_history.append(r)
        self.reward_ema = (1 - alpha) * self.reward_ema + alpha * r
        self.last_reward = r

    # 최근 MAD 기반 정규화 값 계산
    def _mad_norm(self, window: int = 500) -> float:
        if len(self.reward_history) == 0:
            return 1.0
        hist = list(self.reward_history)[-window:]
        median = np.median(hist)
        mad = np.median(np.abs(hist - median)) + 1e-6
        norm_val = (self.last_reward - median) / mad
        return safe_float(norm_val, 0.0)

    # Joint Multiplier (시장 × 세션 조합)
    def _get_joint_mult(self, market: str, session: str) -> float:
        market = (market or "").upper()
        session = self._normalize_session(session)

        jm = self.cfg.get("joint_mult", {})
        return safe_float(jm.get(f"{market}-{session}", jm.get("DEFAULT", 1.0)))

    # 시장별 Warm-up
    def _warmup_factor(self, step: int, market: str) -> float:
        warm_cfg = self.cfg.get("warmup", {})
        warm_steps = int(warm_cfg.get(market.upper(), 100))

        if step < warm_steps:
            return 1.0  # warm-up 동안 LR 고정
        return 1.0  # warm-up 후 factor 변경 가능

    # 성능 기반 multiplier
    def _get_perf_scale(self, sharpe, drawdown, win_rate) -> Dict[str, float]:
        sharpe = safe_float(sharpe, 0.0)
        drawdown = safe_float(drawdown, 0.0)
        win_rate = safe_float(win_rate, 0.5)

        sharpe_scale = np.tanh(sharpe / 2.0)
        dd_scale = 1.0 / (1.0 + np.exp(5 * drawdown))
        win_scale = (win_rate - 0.5) * 2.0

        total = sharpe_scale * dd_scale * (1 + win_scale)
        total = np.clip(total, 0.5, 2.0)

        return {
            "perf_total": float(total),
            "sharpe_scale": float(sharpe_scale),
            "dd_scale": float(dd_scale),
            "win_scale": float(win_scale)
        }

    # ------------------------------------------------------------------
    # Main LR API
    # ------------------------------------------------------------------
    def get_lr(
        self,
        market: str,
        session: str,
        reward_raw: float,
        sharpe: float,
        drawdown: float,
        win_rate: float,
        step: int
    ) -> Dict[str, Any]:
        """
        학습률 계산
        반환: { lr, debug }
        """
        session = self._normalize_session(session)
        reward_raw = safe_float(reward_raw)

        # 보상 업데이트
        self._update_reward(reward_raw)

        # MAD normalization
        reward_norm = self._mad_norm()

        # Joint multiplier
        joint_mult = self._get_joint_mult(market, session)

        # 성능 기반 multiplier
        perf = self._get_perf_scale(sharpe, drawdown, win_rate)

        # Warmup factor
        warm = self._warmup_factor(step, market)

        # LR 계산
        base_lr = safe_float(self.cfg.get("base_lr", 1.0))
        lr = base_lr * (1 + reward_norm * 0.1)
        lr *= joint_mult
        lr *= perf["perf_total"]
        lr *= warm

        # 안정성 clamp
        lr = float(np.clip(lr, 0.1, 5.0))

        # Debug 정보
        debug = {
            "reward_raw": reward_raw,
            "reward_norm": reward_norm,
            "reward_ema": self.reward_ema,
            "joint_mult": joint_mult,
            "warmup": warm,
            "lr_preclip": lr,
            "perf": perf
        }

        return {"lr": lr, "debug": debug}
