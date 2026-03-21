from dataclasses import dataclass
from typing import Any, Optional

from core.execution.trading_mode import (
    can_send_live_order,
    get_trading_mode,
)


@dataclass
class OrderGuardDecision:
    allowed: bool
    status: str
    reason: str
    mode: str
    account_type: str


class BrokerOrderGuard:
    """
    브로커 주문 전송 직전의 최종 보호 레이어.

    정책:
    - paper account: 허용
    - live account: live gate 통과 시만 허용
    - unknown account: 차단
    """

    def evaluate(self, account_type: str) -> OrderGuardDecision:
        mode = get_trading_mode()
        normalized_account_type = str(account_type).strip().lower()

        # ----------------------------------
        # paper account -> 허용
        # ----------------------------------
        if normalized_account_type == "paper":
            return OrderGuardDecision(
                allowed=True,
                status="ALLOWED",
                reason="PAPER_ACCOUNT_ALLOWED",
                mode=mode,
                account_type=normalized_account_type,
            )

        # ----------------------------------
        # live account -> 엄격한 gate 적용
        # ----------------------------------
        if normalized_account_type == "live":
            allowed, reason = can_send_live_order(normalized_account_type)

            if not allowed:
                return OrderGuardDecision(
                    allowed=False,
                    status="BLOCKED",
                    reason=reason,
                    mode=mode,
                    account_type=normalized_account_type,
                )

            return OrderGuardDecision(
                allowed=True,
                status="ALLOWED",
                reason="LIVE_ALLOWED",
                mode=mode,
                account_type=normalized_account_type,
            )

        # ----------------------------------
        # unknown account type -> 차단
        # ----------------------------------
        return OrderGuardDecision(
            allowed=False,
            status="BLOCKED",
            reason="UNKNOWN_ACCOUNT_TYPE",
            mode=mode,
            account_type=normalized_account_type,
        )

    def build_block_response(
        self,
        decision: OrderGuardDecision,
        order: Optional[Any] = None,
    ) -> dict:
        return {
            "status": decision.status,
            "reason": decision.reason,
            "mode": decision.mode,
            "account_type": decision.account_type,
            "order_repr": repr(order) if order is not None else None,
        }