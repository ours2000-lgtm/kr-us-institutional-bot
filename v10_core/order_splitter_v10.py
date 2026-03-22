# =====================================================================
# Order Splitter V10 — Adaptive Order Fragmentation Engine (Stable)
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import List
import random
import math
import time


@dataclass
class OrderFragment:
    qty: float
    price: float


class OrderSplitterV10:
    """
    주문 분할 엔진 V10 (Alpaca 실거래 기준 안정판)

    기능:
    - 전체 주문을 여러 조각으로 분할
    - 유동성 부족 종목도 안전하게 처리
    - 지나치게 작은 조각 제거
    - adaptive delay (시장 속도 따라 자동 조절)
    """

    def __init__(self, config: dict):
        self.cfg = config.get("EXECUTOR", {})

        # 분할 비율 (전체 수량의 X% ~ Y% 단위로 분할)
        self.min_frag = float(self.cfg.get("min_fragment", 0.12))   # 최소 12%
        self.max_frag = float(self.cfg.get("max_fragment", 0.28))   # 최대 28%

        # 딜레이 조절
        self.delay_base = float(self.cfg.get("delay_base", 0.45))
        self.delay_decay = float(self.cfg.get("delay_decay", 0.82))

        # 급등락 커트라인 (ex: 0.6% 이상 변동 시 FAIL-SAFE)
        self.volatility_cut = float(self.cfg.get("volatility_cut", 0.006))

        # 최소 분할 수량 (Alpaca fractional shares 기준)
        self.min_qty = float(self.cfg.get("min_qty", 0.0001))

    # -----------------------------------------------------------------
    # (1) 주문 분할 로직
    # -----------------------------------------------------------------
    def split_orders(self, total_qty: float) -> List[float]:
        """
        total_qty=10 → [2.4, 1.3, 3.1, 1.9, 1.3] 식으로 분할

        특징:
        - 분할 비율은 난수 기반 → 거래 흔적 최소화
        - 너무 작은 조각은 자동 제거
        """

        if total_qty <= 0:
            return []

        parts = []
        remains = total_qty

        while remains > 0:
            frag_ratio = random.uniform(self.min_frag, self.max_frag)
            frag = remains * frag_ratio

            # 최소 조각 보정
            frag = max(frag, self.min_qty)

            if frag > remains:
                frag = remains

            parts.append(frag)
            remains -= frag

            # 안전장치 — 너무 많은 조각 생성 방지
            if len(parts) > 20:
                # 남은 것을 한 번에
                if remains > 0:
                    parts.append(remains)
                break

        return parts

    # -----------------------------------------------------------------
    # (2) 가격 급등락 감지
    # -----------------------------------------------------------------
    @staticmethod
    def price_jump(last_price: float, ref_price: float, threshold: float) -> bool:
        if ref_price <= 0:
            return False
        return abs(last_price - ref_price) / ref_price > threshold

    # -----------------------------------------------------------------
    # (3) Adaptive 딜레이 계산
    # -----------------------------------------------------------------
    def calc_delay(self, index: int) -> float:
        """
        분할 횟수(index)에 따라 딜레이 자동 감소
        """
        delay = self.delay_base * (self.delay_decay ** index)
        return max(delay, 0.05)

