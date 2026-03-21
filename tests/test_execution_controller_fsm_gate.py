import types

from core.engine.execution_controller import ExecutionController
from engine.recovery_fsm import (
    STATE_CONNECTED,
    STATE_READY,
    STATE_EXIT_ONLY,
)


class DummyAdapter:
    def __init__(self, recovery_state=None, send_ret=0):
        self.recovery_state = recovery_state
        self.send_ret = send_ret
        self.sent_orders = []

    def send_order(self, order, account_type="paper"):
        self.sent_orders.append((order, account_type))
        return self.send_ret


class DummyOrderFactory:
    def __init__(self, order):
        self.order = order

    def build_from_signal(self, signal):
        return self.order


class DummyRiskDecision:
    def __init__(self, allowed=True):
        self.allowed = allowed
        self.decision = "ALLOW" if allowed else "REJECT"
        self.reasons = []
        self.block_reason = None
        self.current_position_qty = None
        self.projected_position_qty = None


class DummyRiskManager:
    def __init__(self, allowed=True):
        self.allowed = allowed
        self.block_calls = []
        self.sent_orders = []
        self.failed_orders = []

    def evaluate_decision(self, order):
        return DummyRiskDecision(allowed=self.allowed)

    def block_trading(self, reason):
        self.block_calls.append(reason)

    def on_order_sent(self, order):
        self.sent_orders.append(order)

    def on_order_failed(self, order):
        self.failed_orders.append(order)


def make_order(symbol="005930", side="BUY", intent_id="intent-1"):
    return types.SimpleNamespace(
        intent_id=intent_id,
        symbol=symbol,
        side=side,
        qty=1,
        order_type="MARKET",
        price=70000,
        broker_order_id=None,
    )


def make_signal(symbol="005930"):
    return types.SimpleNamespace(symbol=symbol)


def test_buy_blocked_in_connected_state():
    order = make_order(side="BUY", intent_id="intent-buy-connected")
    adapter = DummyAdapter(recovery_state=STATE_CONNECTED)
    order_factory = DummyOrderFactory(order)
    risk_manager = DummyRiskManager(allowed=True)

    controller = ExecutionController(
        adapter=adapter,
        order_factory=order_factory,
        risk_manager=risk_manager,
    )

    result = controller.execute_signal(make_signal())

    assert result is False
    assert len(adapter.sent_orders) == 0


def test_sell_blocked_in_connected_state():
    order = make_order(side="SELL", intent_id="intent-sell-connected")
    adapter = DummyAdapter(recovery_state=STATE_CONNECTED)
    order_factory = DummyOrderFactory(order)
    risk_manager = DummyRiskManager(allowed=True)

    controller = ExecutionController(
        adapter=adapter,
        order_factory=order_factory,
        risk_manager=risk_manager,
    )

    result = controller.execute_signal(make_signal())

    assert result is False
    assert len(adapter.sent_orders) == 0


def test_buy_allowed_in_ready_state():
    order = make_order(side="BUY", intent_id="intent-buy-ready")
    adapter = DummyAdapter(recovery_state=STATE_READY, send_ret=0)
    order_factory = DummyOrderFactory(order)
    risk_manager = DummyRiskManager(allowed=True)

    controller = ExecutionController(
        adapter=adapter,
        order_factory=order_factory,
        risk_manager=risk_manager,
    )

    result = controller.execute_signal(make_signal())

    assert result is True
    assert len(adapter.sent_orders) == 1
    assert len(risk_manager.sent_orders) == 1


def test_sell_allowed_in_exit_only_state():
    order = make_order(side="SELL", intent_id="intent-sell-exit-only")
    adapter = DummyAdapter(recovery_state=STATE_EXIT_ONLY, send_ret=0)
    order_factory = DummyOrderFactory(order)
    risk_manager = DummyRiskManager(allowed=True)

    controller = ExecutionController(
        adapter=adapter,
        order_factory=order_factory,
        risk_manager=risk_manager,
    )

    result = controller.execute_signal(make_signal())

    assert result is True
    assert len(adapter.sent_orders) == 1
    assert len(risk_manager.sent_orders) == 1


def test_unknown_state_fail_closed_when_supplier_and_adapter_missing():
    order = make_order(side="BUY", intent_id="intent-unknown")
    adapter = DummyAdapter(recovery_state=None)
    order_factory = DummyOrderFactory(order)
    risk_manager = DummyRiskManager(allowed=True)

    controller = ExecutionController(
        adapter=adapter,
        order_factory=order_factory,
        risk_manager=risk_manager,
        recovery_state_supplier=None,
    )

    result = controller.execute_signal(make_signal())

    assert result is False
    assert len(adapter.sent_orders) == 0