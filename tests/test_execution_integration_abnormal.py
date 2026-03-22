# path: tests/test_execution_integration_abnormal.py

from datetime import timedelta

from core.execution.execution_controller import ExecutionController
from core.execution.order_lifecycle import OrderLifecycleManager, OrderState
from core.execution.order_watchdog import OrderWatchdog
from broker.order_event_bridge import OrderEventBridge
from core.engine.order_factory import OrderFactory


# -------------------------
# Dummy Components
# -------------------------

class DummyAdapter:
    def send_order(self, order, account_type=None):
        return {"ret": 0, "order_no": "B-INT-1"}


class DummyRiskManager:
    def __init__(self):
        self.blocked = []

    def evaluate(self, order):
        class R:
            allowed = True
        return R()

    def block_trading(self, reason):
        self.blocked.append(reason)


class DummySignal:
    def __init__(self):
        self.symbol = "005930"
        self.action = "BUY"
        self.qty = 10
        self.order_type = "LIMIT"
        self.price = 1000


class DummyEvidence:
    def write_event(self, *args, **kwargs):
        pass


# -------------------------
# Setup Helper
# -------------------------

def _build_system():
    adapter = DummyAdapter()
    risk = DummyRiskManager()
    lifecycle = OrderLifecycleManager()
    evidence = DummyEvidence()

    controller = ExecutionController(
        adapter=adapter,
        order_factory=OrderFactory(),
        risk_manager=risk,
        account_type="paper",
        recovery_state_supplier=lambda: "READY",
        evidence_writer=evidence,
        order_lifecycle_manager=lifecycle,
    )

    bridge = OrderEventBridge(
        order_lifecycle_manager=lifecycle,
        evidence_writer=evidence,
    )

    watchdog = OrderWatchdog(
        lifecycle_manager=lifecycle,
        risk_manager=risk,
        evidence_writer=evidence,
        ack_timeout_sec=5,
        check_interval_sec=1,
    )

    return controller, bridge, lifecycle, watchdog, risk


# -------------------------
# TESTS
# -------------------------

def test_full_flow_success():
    controller, bridge, lifecycle, _, _ = _build_system()

    signal = DummySignal()
    assert controller.execute_signal(signal) is True

    rec = list(lifecycle.get_active_records())[0]

    # ACK
    bridge.handle_order_ack(
        broker_order_id=rec.broker_order_id,
        intent_id=rec.intent_id,
        reason="ack",
    )

    # FULL
    bridge.handle_full_fill(
        broker_order_id=rec.broker_order_id,
        intent_id=rec.intent_id,
        filled_qty=10,
        reason="full",
    )

    final = lifecycle.get_record(rec.intent_id)
    assert final.state == OrderState.FILLED


def test_ack_timeout_flow():
    controller, _, lifecycle, watchdog, risk = _build_system()

    signal = DummySignal()
    controller.execute_signal(signal)

    rec = list(lifecycle.get_active_records())[0]

    # force timeout
    lifecycle._records[rec.intent_id].updated_at -= timedelta(seconds=10)

    watchdog._run_once()

    final = lifecycle.get_record(rec.intent_id)
    assert final.state == OrderState.EXPIRED
    assert len(risk.blocked) == 1


def test_out_of_order_full_then_ack():
    controller, bridge, lifecycle, _, _ = _build_system()

    signal = DummySignal()
    controller.execute_signal(signal)

    rec = list(lifecycle.get_active_records())[0]

    # FULL 먼저
    bridge.handle_full_fill(
        broker_order_id=rec.broker_order_id,
        intent_id=rec.intent_id,
        filled_qty=10,
        reason="full",
    )

    # ACK 나중
    bridge.handle_order_ack(
        broker_order_id=rec.broker_order_id,
        intent_id=rec.intent_id,
        reason="ack",
    )

    final = lifecycle.get_record(rec.intent_id)
    assert final.state == OrderState.FILLED


def test_duplicate_full_fill():
    controller, bridge, lifecycle, _, _ = _build_system()

    signal = DummySignal()
    controller.execute_signal(signal)

    rec = list(lifecycle.get_active_records())[0]

    bridge.handle_full_fill(
        broker_order_id=rec.broker_order_id,
        intent_id=rec.intent_id,
        filled_qty=10,
        reason="full",
    )

    # duplicate
    bridge.handle_full_fill(
        broker_order_id=rec.broker_order_id,
        intent_id=rec.intent_id,
        filled_qty=10,
        reason="full",
    )

    final = lifecycle.get_record(rec.intent_id)
    assert final.filled_qty == 10
    assert final.state == OrderState.FILLED


def test_runtime_block():
    adapter = DummyAdapter()

    class BlockRisk:
        def evaluate(self, order):
            class R:
                allowed = False
                block_reason = "risk_block"
            return R()

    lifecycle = OrderLifecycleManager()

    controller = ExecutionController(
        adapter=adapter,
        order_factory=OrderFactory(),
        risk_manager=BlockRisk(),
        account_type="paper",
        recovery_state_supplier=lambda: "READY",
        order_lifecycle_manager=lifecycle,
    )

    signal = DummySignal()

    assert controller.execute_signal(signal) is False

    rec = list(lifecycle.get_active_records())[0]
    assert rec.state == OrderState.REJECTED