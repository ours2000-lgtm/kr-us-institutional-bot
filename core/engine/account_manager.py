from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging import getLogger

logger = getLogger(__name__)


@dataclass
class AccountState:

    deposit: float = 0.0
    available_cash: float = 0.0
    equity: float = 0.0

    last_update: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class AccountManager:

    def __init__(self):

        self.state = AccountState()

    # ---------------------------------
    # 조회
    # ---------------------------------

    def get_deposit(self):

        return self.state.deposit

    def get_available_cash(self):

        return self.state.available_cash

    def get_equity(self):

        return self.state.equity

    # ---------------------------------
    # 업데이트
    # ---------------------------------

    def update_account_snapshot(
        self,
        deposit: float,
        available_cash: float,
        equity: float,
    ):

        self.state.deposit = float(deposit)
        self.state.available_cash = float(available_cash)
        self.state.equity = float(equity)

        self.state.last_update = datetime.now(timezone.utc)

        logger.info(
            "Account snapshot updated deposit=%s available=%s equity=%s",
            self.state.deposit,
            self.state.available_cash,
            self.state.equity,
        )

    # ---------------------------------
    # 주문 가능 여부
    # ---------------------------------

    def can_afford(self, order_price, qty):

        required = float(order_price) * int(qty)

        if required > self.state.available_cash:

            logger.warning(
                "Insufficient cash required=%s available=%s",
                required,
                self.state.available_cash,
            )

            return False

        return True