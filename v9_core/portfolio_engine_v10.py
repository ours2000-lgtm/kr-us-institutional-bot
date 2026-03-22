# =====================================================================
# Portfolio Engine V10 — Institutional-Grade Risk-Based Allocator
# =====================================================================

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple
from datetime import datetime

from regime_engine_v10 import RegimeResult, RegimeState
from utils_v10 import safe_log


# =====================================================================
# Position 구조체 (브로커 독립적 자료구조)
# =====================================================================
@dataclass
class Position:
    symbol: str
    qty: float
    avg_price: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =====================================================================
# Portfolio Engine V10 본체
# =====================================================================
class PortfolioEngineV10:
    """
    Portfolio Engine V10
    ----------------------------------------------------------------
    ✔ 변동성 기반 포지션 사이징 (Volatility Targeting)
    ✔ Regime 기반 노출 배수 조절 (Bull / Neutral / Bear / Crash)
    ✔ 자산별 최대 노출 비중 제한
    ✔ 최소 현금 비중 강제
    ✔ Fail-Safe (DD / 연속 손실)
    ✔ 목표 포지션 계산 + 리밸런싱 신호 생성
    ----------------------------------------------------------------
    """

    def __init__(self, config: Dict[str, Any], broker):
        self.cfg = config.get("PORTFOLIO", {})
        self.broker = broker

        # --- 변동성 기반 ---
        self.vol_target = float(self.cfg.get("vol_target", 0.02))
        self.vol_window = int(self.cfg.get("vol_window", 30))
        self.annualize = bool(self.cfg.get("annualize_vol", False))

        # --- 포트폴리오 한도 ---
        self.max_leverage = float(self.cfg.get("max_leverage", 1.0))
        self.max_position_pct = float(self.cfg.get("max_position_pct", 0.15))
        self.min_cash_ratio = float(self.cfg.get("min_cash_ratio", 0.10))

        # --- Fail-safe ---
        self.crash_reduce_ratio = float(self.cfg.get("crash_reduce_ratio", 0.50))
        self.dd_soft = float(self.cfg.get("dd_soft", 0.08))
        self.dd_hard = float(self.cfg.get("dd_hard", 0.12))
        self.loss_streak_soft = int(self.cfg.get("loss_streak_soft", 5))

        # --- 글로벌 익스포저 배수 ---
        self.global_exposure_multiplier = 1.0

    # =====================================================================
    # 계좌 상태
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

        px = prices[-self.vol_window:]
        returns = np.diff(px) / px[:-1]
        vol = float(np.std(returns))

        if self.annualize:
            vol *= np.sqrt(252)

        return vol

    # =====================================================================
    # 변동성 기반 달러 익스포저 계산
    # =====================================================================
    def calc_volatility_dollar_exposure(self, prices: np.ndarray) -> float:
        vol = self._estimate_vol(prices)
        if vol <= 0:
            return 0.0
        equity = self.get_equity()
        exposure = (equity * self.vol_target) / vol
        return max(exposure, 0.0)

    # =====================================================================
    # 달러 익스포저 → 수량 변환
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
        score = float(regime.score)  # [-1, +1]

        if regime.state == RegimeState.BULL:
            m = 1.0 + 0.30 * max(0, score)
        elif regime.state == RegimeState.BEAR:
            m = 0.9 - 0.3 * max(0, score)
            m = max(m, 0.6)
        elif regime.state == RegimeState.LOW_LIQUIDITY:
            m = 0.5
        elif regime.state == RegimeState.MICROSTRUCTURE_RISK:
            m = 0.7
        elif regime.state == RegimeState.CRASH_WARNING:
            m = self.crash_reduce_ratio
        else:
            m = 1.0

        m *= self.global_exposure_multiplier
        return float(np.clip(m, 0.0, self.max_leverage))

    # =====================================================================
    # 노출 제한 (Asset-level, Portfolio-level)
    # =====================================================================
    def clamp_asset_limit(self, exposure: float) -> float:
        equity = self.get_equity()
        return float(min(exposure, equity * self.max_position_pct))

    def enforce_min_cash(self, exposure: float) -> float:
        equity = self.get_equity()
        max_exposure = equity * (1.0 - self.min_cash_ratio)
        return float(min(exposure, max_exposure))

    # =====================================================================
    # 최종 목표 수량 계산
    # =====================================================================
    def calc_final_position_qty(
        self,
        symbol: str,
        prices: np.ndarray,
        regime: RegimeResult
    ) -> float:

        if prices is None or len(prices) < 2:
            return 0.0

        last_price = float(prices[-1])

        # (1) 변동성 기반 달러 노출
        exposure = self.calc_volatility_dollar_exposure(prices)

        # (2) Regime 기반 배수
        exposure *= self.regime_multiplier(regime)

        # (3) 자산별 상한
        exposure = self.clamp_asset_limit(exposure)

        # (4) 최소 현금 비중
        exposure = self.enforce_min_cash(exposure)

        # (5) 수량 변환
        qty = self.dollar_to_qty(exposure, last_price)

        return float(max(qty, 0.0))

    # =====================================================================
    # 리밸런싱 계획
    # =====================================================================
    def plan_rebalance(self, symbol: str, target_qty: float) -> List[Tuple[str, float]]:
        pos_map = {p.symbol: p for p in self.broker.list_positions()}
        current = float(pos_map[symbol].qty) if symbol in pos_map else 0.0

        delta = target_qty - current

        if abs(delta) < max(1, current * 0.01):
            return [("HOLD", 0.0)]

        if delta > 0:
            return [("BUY", delta)]
        else:
            return [("SELL", -delta)]

    # =====================================================================
    # Fail-Safe 시스템 (DD + 손실 연속)
    # =====================================================================
    def apply_fail_safes(self, portfolio_dd: float, loss_streak: int):
        if portfolio_dd >= self.dd_hard:
            self.global_exposure_multiplier = 0.0
            safe_log("[FAIL-SAFE] FULL CASH MODE")
        elif portfolio_dd >= self.dd_soft or loss_streak >= self.loss_streak_soft:
            self.global_exposure_multiplier = 0.5
            safe_log("[FAIL-SAFE] Exposure Reduced 50%")
        else:
            self.global_exposure_multiplier = 1.0

    # =====================================================================
    # Regime 기반 전체 축소
    # =====================================================================
    def auto_rebalance(self, regime: RegimeResult):
        if regime.state == RegimeState.CRASH_WARNING:
            self.reduce_all_positions(self.crash_reduce_ratio)
        elif regime.state == RegimeState.LOW_LIQUIDITY:
            self.reduce_all_positions(0.3)
        elif regime.state == RegimeState.MICROSTRUCTURE_RISK:
            self.reduce_all_positions(0.5)

    def reduce_all_positions(self, ratio: float = 1.0):
        for p in self.broker.list_positions():
            qty = p.qty * ratio
            if qty > 0:
                self.broker.sell(p.symbol, qty)

    def full_liquidation(self):
        for p in self.broker.list_positions():
            if p.qty > 0:
                self.broker.sell(p.symbol, p.qty)

