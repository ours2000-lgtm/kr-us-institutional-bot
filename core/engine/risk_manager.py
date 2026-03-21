from logging import getLogger
from typing import Tuple, List, Optional

from core.execution.account_hard_stop import AccountHardStop


logger = getLogger(__name__)


class RiskManager:

    def __init__(self):
        self.account_hard_stop = AccountHardStop()

    # ---------------------------------
    # main
    # ---------------------------------

    def evaluate(self, order) -> Tuple[bool, List[str]]:
        """
        주문 실행 가능 여부 평가
        """

        reasons: List[str] = []

        order_id = getattr(order, "intent_id", None)
        strategy_id = getattr(order, "strategy_id", None)

        # ---------------------------------
        # Account Hard Stop (최우선)
        # ---------------------------------

        decision = self.account_hard_stop.evaluate(
            evaluation_point="BEFORE_SEND"
        )

        if not decision.allowed:
            reasons.append(decision.reason)

            logger.error(
                "RISK_BLOCK_HARD_STOP order_id=%s strategy_id=%s evaluation_point=%s reason=%s hard_stop_latched=%s snapshot=%s",
                order_id,
                strategy_id,
                "BEFORE_SEND",
                decision.reason,
                self.account_hard_stop.state.hard_stop_latched,
                self.account_hard_stop.snapshot(),
            )

            return False, reasons

        # ---------------------------------
        # (추후 확장) 기타 리스크 규칙
        # ---------------------------------
        # 예:
        # - symbol cooldown
        # - max position size
        # - reconciliation block
        # - account exposure rule

        return True, reasons

    # ---------------------------------
    # hooks (execution / fill 연동)
    # ---------------------------------

    def on_order_sent(self, order: Optional[object] = None):
        """
        주문 전송 성공 시 호출
        """
        self.account_hard_stop.record_order_sent()

        logger.info(
            "RISK_ORDER_SENT order_id=%s strategy_id=%s evaluation_point=%s snapshot=%s",
            getattr(order, "intent_id", None) if order else None,
            getattr(order, "strategy_id", None) if order else None,
            "AFTER_SEND",
            self.account_hard_stop.snapshot(),
        )

    def on_fill(
        self,
        realized_delta: float,
        order_id: Optional[str] = None,
        strategy_id: Optional[str] = None,
    ):
        """
        체결 후 손익 반영

        realized_delta:
            이번 체결로 발생한 실현 손익 변화량
        """
        self.account_hard_stop.record_realized_trade(realized_delta)

        # 체결 직후 Hard Stop 재평가 (AFTER_FILL)
        decision = self.account_hard_stop.evaluate(
            evaluation_point="AFTER_FILL"
        )

        if not decision.allowed:
            logger.error(
                "RISK_HARD_STOP_TRIGGERED_AFTER_FILL order_id=%s strategy_id=%s trigger_point=%s reason=%s hard_stop_latched=%s snapshot=%s",
                order_id,
                strategy_id,
                "AFTER_FILL",
                decision.reason,
                self.account_hard_stop.state.hard_stop_latched,
                self.account_hard_stop.snapshot(),
            )

    # ---------------------------------
    # external latch hook
    # ---------------------------------

    def trigger_external_block(self, reason: str, evaluation_point: str = "EXTERNAL"):
        """
        Reconciliation, Kill Switch 등 외부 시스템에 의해
        Hard Stop을 강제 발동
        """
        self.account_hard_stop.trigger_external(
            reason=reason,
            evaluation_point=evaluation_point,
        )

        logger.error(
            "RISK_EXTERNAL_BLOCK reason=%s evaluation_point=%s hard_stop_latched=%s snapshot=%s",
            reason,
            evaluation_point,
            self.account_hard_stop.state.hard_stop_latched,
            self.account_hard_stop.snapshot(),
        )