# ======================================================================
# Reward Function V14 — Nonlinear + Robust + Market-Aware
# ----------------------------------------------------------------------
# - Sharpe softplus 안정화
# - Liquidity normalization (depth/avg_depth)
# - Drawdown sigmoid penalty
# - Loss streak soft floor
# - Median + MAD robust normalization
# - Session-aware tuning
# - Market-aware adaptive scaling (KR/US/CRYPTO)
# ======================================================================

import numpy as np
from dataclasses import dataclass


@dataclass
class RewardContext:
    pnl: float
    vol: float
    max_dd: float
    recent_vol: float
    spread: float
    depth: float
    loss_streak: int
    session: str          # ASIA / EU / US
    market: str           # KR / US / CRYPTO


class RewardFunctionV14:
    def __init__(self):
        self.history = []

        # 시장별 튜닝값
        self.market_scale = {
            "KR": 1.0,
            "US": 1.2,
            "CRYPTO": 1.5,    # 변동성 높은 시장일수록 scale↑
        }

        # 세션별 가중치
        self.session_weight = {
            "ASIA": 0.9,      # 저변동
            "EU": 1.0,
            "US": 1.2,        # 고변동 → 수익 기회↑
        }

    # ------------------------------------------------------------------
    # 내부: Robust MAD Normalization
    # ------------------------------------------------------------------
    def _normalize(self, value):
        hist = self.history[-500:] if len(self.history) > 500 else self.history
        if len(hist) < 20:
            return value  # 학습 초기에는 normalization 없음

        median = np.median(hist)
        mad = np.median(np.abs(hist - median)) + 1e-6

        return (value - median) / mad

    # ------------------------------------------------------------------
    # Reward Core Logic
    # ------------------------------------------------------------------
    def compute(self, ctx: RewardContext):

        # 시장/세션 기반 scale
        scale = self.market_scale.get(ctx.market, 1.0) \
              * self.session_weight.get(ctx.session, 1.0)

        # 1) Sharpe softplus 보상 (안정화)
        sharpe = ctx.pnl / np.sqrt(ctx.vol**2 + 1e-4)
        sharpe *= scale

        # 2) Volatility penalty (normalized)
        vol_penalty = 1.0 / (1.0 + (ctx.recent_vol * scale))

        # 3) Drawdown penalty (sigmoid)
        dd_penalty = 1.0 / (1.0 + np.exp(ctx.max_dd * scale))

        # 4) Liquidity penalty (depth normalized)
        depth_factor = ctx.depth / (ctx.depth + ctx.spread + 1e-6)
        liq_penalty = np.tanh(depth_factor * scale)

        # 5) Loss streak penalty (soft floor)
        loss_penalty = max(0.2, 1.0 / (1.0 + (ctx.loss_streak ** 1.3) * scale))

        # --------------------------
        # 최종 보상 합성
        # --------------------------
        raw_reward = (
            sharpe
            * vol_penalty
            * dd_penalty
            * liq_penalty
            * loss_penalty
        )

        # --------------------------
        # Robust normalization
        # --------------------------
        reward = self._normalize(raw_reward)

        # 기록
        self.history.append(raw_reward)

        # 디버깅 정보
        debug = {
            "sharpe": sharpe,
            "vol_penalty": vol_penalty,
            "dd_penalty": dd_penalty,
            "liq_penalty": liq_penalty,
            "loss_penalty": loss_penalty,
            "raw_reward": raw_reward,
            "normalized_reward": reward,
            "scale": scale,
        }

        return reward, debug
