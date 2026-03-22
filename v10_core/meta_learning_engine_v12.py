# ======================================================================
# MetaLearningEngine V12
# PER + EMA Scaling + Momentum + Session-aware LR + Gradient Clipping
# ----------------------------------------------------------------------
# Works with:
#   - RewardFunctionV14
#   - ExperienceReplayV11 (PER-enabled)
# ======================================================================

from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Optional


# ======================================================================
# Parameter Container
# ======================================================================
@dataclass
class MetaParams:
    signal_weight: float = 1.0
    regime_weight: float = 1.0
    vol_weight: float = 1.0
    liquidity_weight: float = 1.0
    dd_weight: float = 1.0
    ls_weight: float = 1.0


# ======================================================================
# Meta Learning Engine V12
# ======================================================================
class MetaLearningEngineV12:
    """
    Meta-learning engine with:
    - PER sampling (prioritized)
    - EMA-based reward scaling
    - Momentum-based parameter updates
    - Session-aware learning rate
    - Gradient clipping & NaN/Inf protection
    """

    def __init__(self,
                 params: MetaParams,
                 reward_fn,
                 replay_buffer,
                 lr: float = 0.01,
                 momentum: float = 0.9,
                 grad_clip: float = 5.0,
                 ema_decay: float = 0.995):

        self.params = params
        self.reward_fn = reward_fn
        self.replay = replay_buffer

        # Learning dynamics
        self.lr = lr
        self.momentum = momentum
        self.grad_clip = grad_clip

        # EMA for reward scale
        self.reward_scale = 1.0
        self.ema_decay = ema_decay

        # Velocity for momentum update
        self.vel = {
            "signal": 0.0,
            "regime": 0.0,
            "vol": 0.0,
            "liq": 0.0,
            "dd": 0.0,
            "ls": 0.0
        }

        # Logging
        self.update_history = []

    # ------------------------------------------------------------------
    # Session-aware LR Adjustment
    # ------------------------------------------------------------------
    def _session_lr_scale(self, session: str) -> float:
        """
        Market-sensitive LR:
        - KR open (09:00~09:10) → lower LR
        - US open (23:30~23:50) → lower LR
        - Crypto US session → higher LR
        """

        session = (session or "").lower()

        if session in ["kr_open"]:
            return 0.3
        if session in ["us_open"]:
            return 0.4
        if session in ["crypto_us"]:
            return 1.3
        if session in ["crypto_asia"]:
            return 0.7

        return 1.0

    # ------------------------------------------------------------------
    # Meta Learning Update
    # ------------------------------------------------------------------
    def update(self, batch_size: int = 16):
        """
        Sample from replay buffer using PER,
        compute reward via RewardFunctionV14,
        apply nonlinear gradient update.
        """

        samples, is_weights, idxs = self.replay.sample(batch_size)

        if len(samples) == 0:
            return

        grads = {
            "signal": 0.0,
            "regime": 0.0,
            "vol": 0.0,
            "liq": 0.0,
            "dd": 0.0,
            "ls": 0.0
        }

        new_priorities = []

        # --------------------------------------------------------------
        # 1. Compute gradients from each experience
        # --------------------------------------------------------------
        for exp, w in zip(samples, is_weights):

            try:
                # Compute reward using reward function V14
                rw, dbg = self.reward_fn.compute(
                    pnl=exp.pnl,
                    vol=exp.vol,
                    max_dd=exp.max_dd,
                    recent_vol=exp.recent_vol,
                    liquidity=exp.liquidity,
                    loss_streak=exp.loss_streak,
                    session=exp.session
                )

                # PER priority = absolute TD-error-like measure
                new_priorities.append(abs(rw) + 1e-6)

                # EMA reward scaling update
                self.reward_scale = (
                    self.ema_decay * self.reward_scale
                    + (1 - self.ema_decay) * abs(rw)
                )

                scaled_rw = rw / (self.reward_scale + 1e-8)

                # Session LR adjust
                lr_scale = self._session_lr_scale(exp.session)
                local_lr = self.lr * lr_scale

                # Gradient contributions
                grads["signal"] += scaled_rw * exp.meta_signal * w * local_lr
                grads["regime"] += scaled_rw * exp.meta_regime * w * local_lr
                grads["vol"] += scaled_rw * dbg.get("rw_vol", 0.0) * w * local_lr
                grads["liq"] += scaled_rw * dbg.get("rw_liq", 0.0) * w * local_lr
                grads["dd"] += scaled_rw * dbg.get("rw_dd", 0.0) * w * local_lr
                grads["ls"] += scaled_rw * dbg.get("rw_ls", 0.0) * w * local_lr

            except Exception as e:
                print(f"[MetaLearning] Error computing reward: {e}")
                new_priorities.append(1.0)
                continue

        # --------------------------------------------------------------
        # 2. Gradient clipping & NaN handling
        # --------------------------------------------------------------
        for k, v in grads.items():
            if np.isnan(v) or np.isinf(v):
                grads[k] = 0.0
            grads[k] = np.clip(v, -self.grad_clip, self.grad_clip)

        # --------------------------------------------------------------
        # 3. Momentum update
        # --------------------------------------------------------------
        for k in grads:
            self.vel[k] = self.momentum * self.vel[k] + grads[k]

        # --------------------------------------------------------------
        # 4. Apply updates
        # --------------------------------------------------------------
        self.params.signal_weight += self.vel["signal"]
        self.params.regime_weight += self.vel["regime"]
        self.params.vol_weight += self.vel["vol"]
        self.params.liquidity_weight += self.vel["liq"]
        self.params.dd_weight += self.vel["dd"]
        self.params.ls_weight += self.vel["ls"]

        # --------------------------------------------------------------
        # 5. PER priority update
        # --------------------------------------------------------------
        self.replay.update_priorities(idxs, new_priorities)

        # --------------------------------------------------------------
        # 6. Logging
        # --------------------------------------------------------------
        self.update_history.append({
            "grads": grads,
            "vel": self.vel.copy(),
            "params": self.params,
            "reward_scale": float(self.reward_scale)
        })


# ======================================================================
# END OF FILE
# ======================================================================
