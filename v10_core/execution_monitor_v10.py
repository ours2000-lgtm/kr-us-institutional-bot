# =====================================================================
# Execution Monitor V10 — Fail-Safe & Fill Tracking Engine (Stable)
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Callable
import time


@dataclass
class FillStatus:
    filled_qty: float = 0.0
    remaining_qty: float = 0.0
    avg_fill_price: float = 0.0
    last_update: float = field(default_factory=time.time)


class ExecutionMonitorV10:
    """
    체결 모니터 + Fail-Safe 엔진 V10 (Al실전 안정판)

    기능:
    - 주문 체결률 실시간 모니터링
    - 호가 급변 감지 → fail-safe
    - 슬리피지 초과 감지 → fail-safe
    - 시간 초과 → 자동 취소
    """

    def __init__(self, config: dict):
        self.cfg = config.get("EXECUTOR", {})

        self.max_wait = float(self.cfg.get("max_wait", 6.0))            # 최대 대기 시간
        self.max_slippage = float(self.cfg.get("max_slippage", 0.004))  # 0.4%
        self.price_jump_cut = float(self.cfg.get("price_jump_cut", 0.006))
        self.poll_delay = float(self.cfg.get("poll_delay", 0.15))       # 모니터링 주기

    # -----------------------------------------------------------------
    # 메인 감시 루프
    # -----------------------------------------------------------------
    def monitor_order(
        self,
        order_id: str,
        symbol: str,
        ref_price: float,
        broker,
        price_feed_fn: Callable,
        logger: Optional[Callable] = None
    ) -> FillStatus:

        start_t = time.time()

        while True:
            elapsed = time.time() - start_t

            # ---------------------------------------------------------
            # (1) 시간 초과 → 주문 취소
            # ---------------------------------------------------------
            if elapsed > self.max_wait:
                if logger:
                    logger(f"[TIMEOUT] Order {order_id} exceeded max_wait → cancel")
                try:
                    broker.cancel_order(order_id)
                except:
                    pass
                return FillStatus()

            # ---------------------------------------------------------
            # (2) 가격 급등락 감지 → fail-safe
            # ---------------------------------------------------------
            last_price = price_feed_fn()
            if ref_price > 0:
                jump = abs(last_price - ref_price) / ref_price
                if jump > self.price_jump_cut:
                    if logger:
                        logger(f"[FAIL-SAFE] Price jump {jump:.4f} → cancel")
                    try:
                        broker.cancel_order(order_id)
                    except:
                        pass
                    return FillStatus()

            # ---------------------------------------------------------
            # (3) 슬리피지 감지 → fail-safe
            # ---------------------------------------------------------
            slippage = abs(last_price - ref_price) / ref_price
            if slippage > self.max_slippage:
                if logger:
                    logger(f"[FAIL-SAFE] Slippage {slippage:.4f} > limit → cancel")
                try:
                    broker.cancel_order(order_id)
                except:
                    pass
                return FillStatus()

            # ---------------------------------------------------------
            # (4) 체결 상태 조회
            # ---------------------------------------------------------
            try:
                status = broker.get_order_status(order_id)
            except:
                if logger:
                    logger("[ERROR] get_order_status failed → retry")
                time.sleep(self.poll_delay)
                continue

            filled = float(status.get("filled_qty", 0.0))
            remaining = float(status.get("remaining_qty", 0.0))
            avg_price = float(status.get("avg_fill_price", ref_price))

            # ---------------------------------------------------------
            # (5) 체결 완료
            # ---------------------------------------------------------
            if remaining <= 1e-9:
                return FillStatus(
                    filled_qty=filled,
                    remaining_qty=0.0,
                    avg_fill_price=avg_price
                )

            # ---------------------------------------------------------
            # (6) 계속 모니터링
            # ---------------------------------------------------------
            time.sleep(self.poll_delay)
