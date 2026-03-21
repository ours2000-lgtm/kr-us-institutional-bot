from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Tuple


@dataclass
class HardStopConfig:
    daily_realized_loss_limit_amount: Decimal = Decimal("100000")
    max_consecutive_losses: int = 3
    max_orders_per_day: int = 20


@dataclass
class HardStopState:
    daily_realized_pnl: Decimal = Decimal("0")
    consecutive_losses: int = 0
    orders_sent_today: int = 0
    hard_stop_latched: bool = False
    last_reason: Optional[str] = None
    last_evaluation_point: Optional[str] = None


@dataclass
class HardStopDecision:
    allowed: bool
    reason: str
    latched: bool


class AccountHardStop:
    """
    Account-level hard stop.

    책임:
    - 계좌 단위 손실/연속 손실/주문 횟수 기반 차단
    - latched 상태 유지
    - deterministic decision 반환
    - 외부 시스템(Reconciliation, KillSwitch 등) 강제 발동 지원
    """

    def __init__(self, config: Optional[HardStopConfig] = None):
        self.config = config or HardStopConfig()
        self.state = HardStopState()

    # ---------------------------------
    # public
    # ---------------------------------

    def evaluate(self, evaluation_point: str = "BEFORE_SEND") -> HardStopDecision:
        """
        주문 가능 여부 평가
        """

        self.state.last_evaluation_point = evaluation_point

        if self.state.hard_stop_latched:
            return HardStopDecision(
                allowed=False,
                reason="ALREADY_LATCHED",
                latched=True,
            )

        triggered, reason = self._check_trigger_rules()

        if triggered:
            self.state.hard_stop_latched = True
            self.state.last_reason = reason

            return HardStopDecision(
                allowed=False,
                reason=reason,
                latched=True,
            )

        return HardStopDecision(
            allowed=True,
            reason="OK",
            latched=False,
        )

    def trigger_external(self, reason: str, evaluation_point: str = "EXTERNAL") -> None:
        """
        외부 시스템(Reconciliation, KillSwitch 등)에서
        강제 Hard Stop 발동.

        Monotonic latch:
        이미 latched 상태면 해제하지 않으며,
        last_reason는 최초 또는 최신 외부 reason으로 유지할 수 있다.
        """
        self.state.hard_stop_latched = True
        self.state.last_reason = str(reason)
        self.state.last_evaluation_point = evaluation_point

    def record_order_sent(self) -> None:
        self.state.orders_sent_today += 1

    def record_realized_trade(self, realized_delta) -> None:
        """
        체결 후 실현손익 반영

        realized_delta:
            이번 청산으로 새롭게 발생한 손익 변화량
        """
        realized_delta = Decimal(str(realized_delta))
        self.state.daily_realized_pnl += realized_delta

        if realized_delta < 0:
            self.state.consecutive_losses += 1
        elif realized_delta > 0:
            self.state.consecutive_losses = 0

    def reset_for_new_trading_day(self) -> None:
        self.state.daily_realized_pnl = Decimal("0")
        self.state.consecutive_losses = 0
        self.state.orders_sent_today = 0
        self.state.hard_stop_latched = False
        self.state.last_reason = None
        self.state.last_evaluation_point = None

    def snapshot(self) -> dict:
        return {
            "daily_realized_pnl": str(self.state.daily_realized_pnl),
            "consecutive_losses": self.state.consecutive_losses,
            "orders_sent_today": self.state.orders_sent_today,
            "hard_stop_latched": self.state.hard_stop_latched,
            "last_reason": self.state.last_reason,
            "last_evaluation_point": self.state.last_evaluation_point,
            "config": {
                "daily_realized_loss_limit_amount": str(
                    self.config.daily_realized_loss_limit_amount
                ),
                "max_consecutive_losses": self.config.max_consecutive_losses,
                "max_orders_per_day": self.config.max_orders_per_day,
            },
        }

    # ---------------------------------
    # internal
    # ---------------------------------

    def _check_trigger_rules(self) -> Tuple[bool, str]:
        if self.state.daily_realized_pnl <= -self.config.daily_realized_loss_limit_amount:
            return True, "DAILY_LOSS_LIMIT_EXCEEDED"

        if self.state.consecutive_losses >= self.config.max_consecutive_losses:
            return True, "MAX_CONSECUTIVE_LOSSES_EXCEEDED"

        if self.state.orders_sent_today >= self.config.max_orders_per_day:
            return True, "MAX_ORDERS_PER_DAY_EXCEEDED"

        return False, "OK"