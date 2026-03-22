# =====================================================================
# Price Optimizer V10 — Best Execution Price Calculator (Stable)
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Quote:
    """
    실시간 호가 정보 구조체
    """
    bid: float
    ask: float
    bid_size: float = 0.0
    ask_size: float = 0.0

    @property
    def mid(self) -> float:
        if self.bid <= 0 or self.ask <= 0:
            return 0.0
        return (self.bid + self.ask) * 0.5


class PriceOptimizerV10:
    """
    시장 미시구조 기반 최적 매수/매도 가격 산출 엔진.
    - 스프레드 좁을 때는 mid 근처
    - 스프레드 넓을 때는 bid/ask 근처
    - microstructure 위험 시 보수적 가격으로 조정
    """

    def __init__(self, config: dict):
        self.cfg = config.get("EXECUTOR", {})

        # 스프레드 threshold (0.2% 기본)
        self.spread_threshold = float(self.cfg.get("spread_threshold", 0.002))

        # microstructure 위험 시 보수적 가격 배수
        self.micro_risk_factor = float(self.cfg.get("micro_risk_factor", 1.2))

    # -----------------------------------------------------------------
    # 매수 최적 가격
    # -----------------------------------------------------------------
    def optimal_buy_price(self, last_price: float, quote: Optional[Quote] = None) -> float:
        """
        last_price 기반 fallback 동작 포함
        """
        if quote is None or quote.bid <= 0 or quote.ask <= 0:
            return round(last_price * 1.001, 4)

        spread = (quote.ask - quote.bid) / max(quote.bid, 1e-9)

        # 스프레드 좁음 → mid-price 근처에서 약간 위
        if spread < self.spread_threshold:
            return round(quote.mid * 1.0002, 4)

        # 넓은 스프레드 → bid 근처 보수적 접근
        return round(quote.bid * 1.001, 4)

    # -----------------------------------------------------------------
    # 매도 최적 가격
    # -----------------------------------------------------------------
    def optimal_sell_price(self, last_price: float, quote: Optional[Quote] = None) -> float:
        if quote is None or quote.bid <= 0 or quote.ask <= 0:
            return round(last_price * 0.999, 4)

        spread = (quote.ask - quote.bid) / max(quote.ask, 1e-9)

        # 스프레드 좁음 → mid 아래에서 팔기
        if spread < self.spread_threshold:
            return round(quote.mid * 0.9998, 4)

        # 넓은 스프레드 → ask 근처에서 매도
        return round(quote.ask * 0.999, 4)
