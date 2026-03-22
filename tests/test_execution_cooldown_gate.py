# path: tests/test_execution_cooldown_gate.py

from datetime import datetime, timedelta, timezone

from core.execution.execution_controller import ExecutionController
from core.engine.order_factory import OrderFactory


# -------------------------------------------------
# Dummy components
# -------------------------------------------------

class DummyAdapter:
    def send_order(self, order, account_type=None):
        return 0  # 항상 성공


class DummyRiskManager:
    class Result:
        allowed = True
        block_reason = None

    def evaluate(self, order):
        return self.Result()

    def on_order_sent(self, order):
        pass

    def on_order_failed(self, order):
        pass


class DummyCooldownManager:
    def __init__(self, allowed=True, raise_error=False):
        self.allowed = allowed
        self.raise_error = raise_error

    def is_allowed(self, symbol):
        if self.raise_error:
            raise RuntimeError("cooldown error")
        return self.allowed


class DummySignal:
    def __init__(self, symbol="005930", action="BUY", qty=1):
        self.symbol = symbol
        self.action = action
        self.qty = qty
        self.order_type = "MARKET"


# -------------------------------------------------
# Tests
# -------------------------------------------------


def build_controller(cooldown_manager):
    return ExecutionController(
        adapter=DummyAdapter(),
        order_factory=OrderFactory(),
        risk_manager=DummyRiskManager(),
        account_type="paper",
        recovery_state_supplier=lambda: "READY",
        evidence_writer=None,
        order_lifecycle_manager=None,
        cooldown_manager=cooldown_manager,
    )


def test_order_allowed_when_no_cooldown():
    controller = build_controller(
        DummyCooldownManager(allowed=True)
    )

    signal = DummySignal()

    result = controller.execute_signal(signal)

    assert result is True


def test_order_blocked_when_cooldown_active():
    controller = build_controller(
        DummyCooldownManager(allowed=False)
    )

    signal = DummySignal()

    result = controller.execute_signal(signal)

    assert result is False


def test_order_blocked_when_cooldown_error_fail_closed():
    controller = build_controller(
        DummyCooldownManager(raise_error=True)
    )

    signal = DummySignal()

    result = controller.execute_signal(signal)

    assert result is False