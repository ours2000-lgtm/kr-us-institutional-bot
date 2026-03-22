# =====================================================================
# Portfolio Engine V10 — Risk-Based Position Sizing & Allocation Engine
# 고급 기능:
#  - 변동성 타깃팅 (Volatility Targeting)
#  - Regime 기반 레버리지 조절 (BULL / BEAR / CRASH 등)
#  - 글로벌 Fail-safe (DD / Loss Streak)
#  - 현금 비중 강제 / 포트폴리오 캡
#  - 리밸런싱 목표 계산
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple
import numpy as np
from datetime import datetime

from regime_engine_v10 import RegimeResult, RegimeState


# =====================================================================
# Position 구조체
# =====================================================================
@dataclass
class Position:
    symbol: str
    qty: float
    avg_price: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =====================================================================
# Portfolio Engine 본체
# =====================================================================
class PortfolioEngineV10:
    """
    V10 Risk-Based Portfolio Engine

    기능:
    - 변동성 기반 포지션 사이징
    - Regime 기반 익스포저 확장/축소
    - 최소 현금 확보
    - 자산별/포트폴리오 별 최대 노출 비중 통제
    - Fail-safe: DD/HARD/LOSS-STREAK
    - 리밸런싱 목표 계산 기능
    """

    def __init__(self, config: Dict[str, Any], broker):

        self.cfg = config.get("PORTFOLIO", {})
        self.broker = broker

        # ---------------------------
        # 변동성 관련 설정
        # ---------------------------
        self.vol_target = float(self.cfg.get("vol_target", 0.02))    # 일간 목표 변동성 2%
        self.vol_window = int(self.cfg.get("vol_window", 30))
        self.annualize = bool(self.cfg.get("annualize_vol", False))

        # ---------------------------
        # 포트폴리오 노출 제한
        # ---------------------------
        self.max_leverage = float(self.cfg.get("max_leverage", 1.0))
        self.max_position_pct = float(self.cfg.get("max_position_pct", 0.15))
        self.min_cash_ratio = float(self.cfg.get("min_cash_ratio", 0.10))

        # ---------------------------
        # FAIL-SAFE
        # ---------------------------
        self.crash_reduce_ratio = float(self.cfg.get("crash_reduce_ratio", 0.50))
        self.dd_soft = float(self.cfg.get("dd_soft", 0.08))
        self.dd_hard = float(self.cfg.get("dd_hard", 0.12))
        self.loss_streak_soft = int(self.cfg.get("loss_streak_soft", 5))

        self.global_exposure_multiplier = 1.0  # fail-safe가 변경함

    # =====================================================================
    # 계좌 상태 가져오기
    # =====================================================================
    def get_equity(self) -> float:
        try:
            return float(self.broker.get_equity())
        except:
            return 0.0

    def get_cash(self) -> float:
        try:
            return float(self.broker.get_cash())
        except:
            return 0.0

    # =====================================================================
    # 변동성 추정
    # =====================================================================
    def _estimate_vol(self, prices: np.ndarray) -> float:
        if prices is None or len(prices) < max(self.vol_window, 10):
            return 0.0

        window = prices[-self.vol_window:]
        returns = np.diff(window) / window[:-1]

        vol = float(np.std(returns))
        if self.annualize:
            vol *= np.sqrt(252)

        return vol

    # =====================================================================
    # 변동성 타깃 기반 달러 익스포저
    # =====================================================================
    def calc_volatility_dollar_exposure(self, prices: np.ndarray) -> float:
        vol = self._estimate_vol(prices)

        if vol <= 0:
            return 0.0

        equity = self.get_equity()
        # 위험 = equity × vol_target, → 달러노출 = 위험 / 현재 변동성
        return (equity * self.vol_target) / vol

    # =====================================================================
    # 달러 → 수량 변환
    # =====================================================================
    @staticmethod
    def dollar_to_qty(dollar: float, price: float) -> float:
        if price <= 0:
            return 0.0
        return max(dollar / price, 0.0)

    # =====================================================================
    # Regime 기반 익스포저 배수
    # =====================================================================
    def regime_multiplier(self, regime: RegimeResult) -> float:
        base = 1.0
        score = float(regime.score)  # [-1, +1]

        if regime.state == RegimeState.BULL:
            m = base * (1.0 + 0.3 * max(0, score))        # 최대 1.3배
        elif regime.state == RegimeState.BEAR:
            m = max(base * (0.9 - 0.3 * max(0, score)), 0.6)
        elif regime.state == RegimeState.LOW_LIQUIDITY:
            m = 0.5
        elif regime.state == RegimeState.MICROSTRUCTURE_RISK:
            m = 0.7
        elif regime.state == RegimeState.CRASH_WARNING:
            m = self.crash_reduce_ratio
        else:
            m = base

        # fail-safe 글로벌 multiplier 적용
        m *= self.global_exposure_multiplier

        # 레버리지 제한
        return float(np.clip(m, 0.0, self.max_leverage))

    # =====================================================================
    # 자산별 노출 클램프
    # =====================================================================
    def clamp_by_equity_limit(self, dollar: float) -> float:
        equity = self.get_equity()
        max_asset = equity * self.max_position_pct
        return min(dollar, max_asset)

    # =====================================================================
    # 현금 비중 유지 (대규모 진입 방지)
    # =====================================================================
    def enforce_min_cash(self, dollar_exposure: float) -> float:
        equity = self.get_equity()
        max_exposure_allowed = equity * (1.0 - self.min_cash_ratio)
        return min(dollar_exposure, max_exposure_allowed)

    # =====================================================================
    # 최종 수량 계산
    # =====================================================================
    def calc_final_position_qty(self,
                                symbol: str,
                                prices: np.ndarray,
                                regime: RegimeResult) -> float:

        if prices is None or len(prices) < 2:
            return 0.0

        last_price = float(prices[-1])

        # (1) 변동성 기반 달러 익스포저
        dollar = self.calc_volatility_dollar_exposure(prices)

        # (2) Regime 배수
        dollar *= self.regime_multiplier(regime)

        # (3) 자산별 cap
        dollar = self.clamp_by_equity_limit(dollar)

        # (4) 최소 현금 비중 강제
        dollar = self.enforce_min_cash(dollar)

        # (5) 수량 환산
        qty = self.dollar_to_qty(dollar, last_price)
        return float(max(qty, 0.0))

    # =====================================================================
    # 리밸런싱 목표 생성
    # =====================================================================
    def plan_rebalance(self,
                       symbol: str,
                       target_qty: float,
                       slippage_buffer: float = 0.01) -> List[Tuple[str, float]]:

        positions = {p.symbol: p for p in self.broker.list_positions()}
        current_qty = float(positions[symbol].qty) if symbol in positions else 0.0

        # 변경 비율이 작으면 HOLD
        if current_qty > 0:
            change_ratio = abs(target_qty - current_qty) / max(current_qty, 1e-9)
            if change_ratio < slippage_buffer:
                return [("HOLD", 0.0)]

        delta = target_qty - current_qty

        if delta > 0:
            return [("BUY", delta)]
        elif delta < 0:
            return [("SELL", -delta)]
        return [("HOLD", 0.0)]

    # =====================================================================
    # FAIL-SAFE
    # =====================================================================
    def apply_fail_safes(self, portfolio_dd: float, loss_streak: int):

        if portfolio_dd >= self.dd_hard:
            self.global_exposure_multiplier = 0.0  # FULL CASH
        elif portfolio_dd >= self.dd_soft or loss_streak >= self.loss_streak_soft:
            self.global_exposure_multiplier = 0.5
        else:
            self.global_exposure_multiplier = 1.0

    # =====================================================================
    # 포지션 전체 축소 / 청산
    # =====================================================================
    def reduce_all_positions(self, ratio: float = 1.0):
        for pos in self.broker.list_positions():
            qty = pos.qty * ratio
            if qty > 0:
                self.broker.sell(pos.symbol, qty)

    def full_liquidation(self):
        self.reduce_all_positions(1.0)
