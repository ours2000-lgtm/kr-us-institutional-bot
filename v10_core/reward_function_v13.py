# =====================================================================
# Reward Function V13 — Market-Aware Adaptive Version
# - 시장별 자동 튜닝
# - 변동성/유동성/DD 감지
# - Reward normalization 유지
# =====================================================================

from __future__ import annotations
import numpy as np
from dataclasses import dataclass


@dataclass
class MarketContext:
    market: str               # "KR" / "US" / "CRYPTO"
    recent_vol: float         # 최근 단기 변동성
    long_vol: float           # 장기 변동성
    avg_spread: float         # 평균 스프레드
    avg_depth: float          # 호가 깊이
    max_dd: float             # 최근 드로다운
    loss_streak: int          # 손실 연속 발생 횟수


class RewardFunctionV13:
    def __init__(self):
        self.reward_history = []

        # 기본 가중치
        self.base_weights = {
            "pnl": 1.0,
            "vol_penalty": 0.5,
            "dd_penalty": 0.7,
            "recent_vol_penalty": 0.3,
        }

    # -----------------------------------------------------------------
    # Normalization for stable learning
    # -----------------------------------------------------------------
    def normalize(self, r: float) -> float:
        self.reward_history.append(r)
        if len(self.reward_history) > 3000:
            self.reward_history.pop(0)

        mu = np.mean(self.reward_history)
        sd = np.std(self.reward_history) + 1e-6
        return (r - mu) / sd

    # -----------------------------------------------------------------
    # 시장별 auto-tuning
    # -----------------------------------------------------------------
    def compute_market_weights(self, ctx: MarketContext):
        weights = self.base_weights.copy()

        # 변동성 비율
        vol_ratio = ctx.recent_vol / (ctx.long_vol + 1e-6)

        # 유동성 점수
        liquidity = max(ctx.avg_spread * 10, 0.1)

        # -----------------------------------------
        # Korean Market (KR)
        # -----------------------------------------
        if ctx.market == "KR":
            # KR은 변동성이 낮아 risk penalty 강화
            weights["vol_penalty"] *= (1.0 + vol_ratio * 0.5)
            weights["dd_penalty"] *= (1.0 + ctx.max_dd * 1.2)

        # -----------------------------------------
        # US Market
        # -----------------------------------------
        elif ctx.market == "US":
            # 유동성이 높으므로 P&L 비중 확대
            weights["pnl"] *= (1.0 + 0.5 / liquidity)
            # 과도한 DD시 penalty 강화
            weights["dd_penalty"] *= (1.0 + ctx.max_dd)

        # -----------------------------------------
        # Crypto Market
        # -----------------------------------------
        elif ctx.market == "CRYPTO":
            # 극단적 변동성 → DD penalty & vol penalty 크게 강화
            weights["dd_penalty"] *= (1.5 + ctx.max_dd * 2.0)
            weights["vol_penalty"] *= (1.2 + vol_ratio)

            # 손실 연속 발생 시 패널티 가중치 증가
            if ctx.loss_streak >= 3:
                weights["dd_penalty"] *= 1.5
                weights["vol_penalty"] *= 1.3

        return weights

    # -----------------------------------------------------------------
    # Reward calculation with market-aware weights
    # -----------------------------------------------------------------
    def compute(self, pnl: float, vol: float, ctx: MarketContext):
        # 시장별 가중치 자동 계산
        W = self.compute_market_weights(ctx)

        reward = (
            W["pnl"] * pnl
            - W["vol_penalty"] * vol
            - W["dd_penalty"] * ctx.max_dd
            - W["recent_vol_penalty"] * ctx.recent_vol
        )

        return self.normalize(reward)
