# =====================================================================
# Reward Function V13 — Market-Aware + Risk-Adjusted + Adaptive Penalty
# =====================================================================

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List


# -----------------------------------------------------------
# 💡 Reward에 필요한 전체 입력 구조
# -----------------------------------------------------------
@dataclass
class RewardContext:
    pnl: float                  # 실제 손익 (수익률 또는 달러 기준)
    vol: float                  # 전략 변동성 (신호 변화량 또는 포트폴리오 변동성)
    max_dd: float               # 전략 또는 포트폴리오 최대 낙폭
    recent_vol: float           # 단기 시장 변동성
    avg_spread: float           # 스프레드 수준
    avg_depth: float            # 호가 깊이(유동성)
    loss_streak: int            # 연속 손실 횟수
    market: str                 # KR / US / CRYPTO
    session: str                # open / close / asia / eu / us 등
    sharpe_window: float = 1.0  # Sharpe-like scaling factor


class RewardFunctionV13:
    """
    ***V13 Reward Engine — 핵심 특징***
    --------------------------------------
    ✔ 시장별 자동 튜닝 (KR/US/CRYPTO)
    ✔ Sharpe-like risk-adjusted reward
    ✔ Drawdown 중력 패널티 (DD ↑ → Reward 폭락)
    ✔ Volatility penalty (시장 변동성 기반 자동 조절)
    ✔ Liquidity penalty (스프레드+호가 깊이)
    ✔ Rolling normalization (Reward 안정화)
    ✔ Loss-streak penalty (연속 손실 시 급격한 감점)
    ✔ Stability clamp (Reward 폭주 방지)
    """

    def __init__(self):
        self.reward_history: List[float] = []
        self.history_window = 500

    # -----------------------------------------------------------
    # ⚙️ 시장별 튜닝 자동화
    # -----------------------------------------------------------
    def market_params(self, market: str) -> Dict[str, float]:
        if market == "KR":
            return {
                "risk_scale": 1.0,
                "vol_scale": 1.0,
                "spread_scale": 0.7,
                "dd_scale": 1.2,
                "loss_streak_scale": 1.0
            }
        elif market == "US":
            return {
                "risk_scale": 1.1,
                "vol_scale": 1.2,
                "spread_scale": 1.0,
                "dd_scale": 1.0,
                "loss_streak_scale": 1.2
            }
        elif market == "CRYPTO":
            return {
                "risk_scale": 1.4,
                "vol_scale": 1.6,
                "spread_scale": 1.3,
                "dd_scale": 1.5,
                "loss_streak_scale": 1.5
            }
        else:
            return {
                "risk_scale": 1.0,
                "vol_scale": 1.0,
                "spread_scale": 1.0,
                "dd_scale": 1.0,
                "loss_streak_scale": 1.0
            }

    # -----------------------------------------------------------
    # 📌 Sharpe-like Risk Adjusted PnL
    # -----------------------------------------------------------
    def sharpe_reward(self, pnl: float, vol: float, scale: float) -> float:
        if vol <= 1e-8:
            return pnl * scale
        return (pnl / (vol + 1e-8)) * scale

    # -----------------------------------------------------------
    # 📌 Volatility Penalty (시장 변동성이 높을수록 감점)
    # -----------------------------------------------------------
    def volatility_penalty(self, recent_vol: float, scale: float) -> float:
        # recent_vol이 클수록 reward 감소
        return 1.0 / (1.0 + scale * recent_vol)

    # -----------------------------------------------------------
    # 📌 Liquidity Penalty (스프레드 + 호가 깊이)
    # -----------------------------------------------------------
    def liquidity_penalty(self, spread: float, depth: float, scale: float) -> float:
        # 유동성 부족 → reward 급감
        depth_factor = np.tanh(depth * 0.0001)  # depth 높을수록 penalty 감소
        liquid_factor = 1.0 / (1.0 + scale * spread)
        return liquid_factor * depth_factor

    # -----------------------------------------------------------
    # 📌 Drawdown Penalty (중력처럼 작용)
    # -----------------------------------------------------------
    def drawdown_penalty(self, max_dd: float, scale: float) -> float:
        # dd 커질수록 급격히 감소하는 커브
        return np.exp(-max_dd * (3.0 * scale))

    # -----------------------------------------------------------
    # 📌 Loss Streak Penalty
    # -----------------------------------------------------------
    def loss_streak_penalty(self, loss_streak: int, scale: float) -> float:
        if loss_streak <= 0:
            return 1.0
        return 1.0 / (1.0 + (loss_streak ** 1.3) * scale)

    # -----------------------------------------------------------
    # ⚡ Reward raw 조립
    # -----------------------------------------------------------
    def compute_raw(self, ctx: RewardContext) -> float:

        m = self.market_params(ctx.market)

        # 1) 샤프형 보상
        rw_sharpe = self.sharpe_reward(ctx.pnl, ctx.vol, m["risk_scale"])

        # 2) 변동성 패널티
        rw_vol = self.volatility_penalty(ctx.recent_vol, m["vol_scale"])

        # 3) 유동성 패널티
        rw_liq = self.liquidity_penalty(ctx.avg_spread, ctx.avg_depth, m["spread_scale"])

        # 4) Drawdown 중력
        rw_dd = self.drawdown_penalty(ctx.max_dd, m["dd_scale"])

        # 5) Loss streak
        rw_ls = self.loss_streak_penalty(ctx.loss_streak, m["loss_streak_scale"])

        # 합산
        combined = rw_sharpe * rw_vol * rw_liq * rw_dd * rw_ls

        return combined

    # -----------------------------------------------------------
    # 📌 Rolling Normalization (stabilizer)
    # -----------------------------------------------------------
    def normalize(self, reward: float) -> float:
        self.reward_history.append(reward)

        if len(self.reward_history) < 50:
            # 학습 초기엔 normalization 하지 않음
            return reward

        # window 정리
        hist = self.reward_history[-self.history_window:]

        mu = np.mean(hist)
        sd = np.std(hist) + 1e-6

        norm = (reward - mu) / sd
        return norm

    # -----------------------------------------------------------
    # 📌 최종 Reward 계산
    # -----------------------------------------------------------
    def compute(self, ctx: RewardContext) -> float:
        raw = self.compute_raw(ctx)
        normalized = self.normalize(raw)

        # Stability clamp (폭주 방지)
        final = float(np.clip(normalized, -5.0, 5.0))
        return final
