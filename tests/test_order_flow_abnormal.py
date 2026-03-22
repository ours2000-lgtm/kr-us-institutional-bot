# path: tests/test_order_flow_abnormal.py

from datetime import timedelta

import pytest

from broker.order_event_bridge import OrderEventBridge
from core.execution.order_lifecycle import OrderLifecycleManager, OrderState
from core.execution.order_watchdog import OrderWatchdog


class DummyEvidenceWriter:
    def __init__(self):
        self.events = []

    def write_event(self, category, component, event_type, payload):
        self.events.append(
            {
                "category": category,
                "component": component,
                "event_type": event_type,
                "payload": payload,
            }
        )

    def find(self, event_type):
        return [e for e in self.events if e["event_type"] == event_type]


class DummyRiskManager:
    def __init__(self):
        self.block_calls = []

    def block_trading(self, reason):
        self.block_calls.append(reason)


def _register_sent_order(
    manager: OrderLifecycleManager,
    intent_id: str = "intent-1",
    symbol: str = "005930",
    side: str = "BUY",
    qty: int = 10,
    broker_order_id: str = "B-1001",
):
    manager.register_new_intent(
        intent_id=intent_id,
        symbol=symbol,
        side=side,
        qty=qty,
        metadata={"source": "test"},
    )
    manager.mark_sent(
        intent_id=intent_id,
        broker_order_id=broker_order_id,
        metadata_update={"source": "test"},
    )
    return intent_id, broker_order_id


def test_ack_timeout_expires_sent_order_and_blocks_trading():
    evidence = DummyEvidenceWriter()
    risk = DummyRiskManager()
    manager = OrderLifecycleManager(evidence_writer=evidence)

    intent_id, broker_order_id = _register_sent_order(manager)

    # white-box: watchdog timeout 재현을 위해 내부 updated_at을 과거로 민다
    manager._records[intent_id].updated_at = (
        manager._records[intent_id].updated_at - timedelta(seconds=10)
    )

    watchdog = OrderWatchdog(
        lifecycle_manager=manager,
        risk_manager=risk,
        evidence_writer=evidence,
        ack_timeout_sec=5,
        check_interval_sec=1,
    )

    watchdog._run_once()

    rec = manager.get_record(intent_id)
    assert rec is not None
    assert rec.state == OrderState.EXPIRED
    assert rec.last_reason == "ack_timeout"

    timeout_events = evidence.find("order_ack_timeout")
    assert len(timeout_events) == 1
    assert timeout_events[0]["payload"]["intent_id"] == intent_id
    assert timeout_events[0]["payload"]["broker_order_id"] == broker_order_id

    assert len(risk.block_calls) == 1
    assert risk.block_calls[0] == f"ORDER_ACK_TIMEOUT:{intent_id}"


def test_ack_timeout_is_handled_only_once_even_if_run_twice():
    evidence = DummyEvidenceWriter()
    risk = DummyRiskManager()
    manager = OrderLifecycleManager(evidence_writer=evidence)

    intent_id, _ = _register_sent_order(manager)

    manager._records[intent_id].updated_at = (
        manager._records[intent_id].updated_at - timedelta(seconds=10)
    )

    watchdog = OrderWatchdog(
        lifecycle_manager=manager,
        risk_manager=risk,
        evidence_writer=evidence,
        ack_timeout_sec=5,
        check_interval_sec=1,
    )

    watchdog._run_once()
    watchdog._run_once()

    timeout_events = evidence.find("order_ack_timeout")
    assert len(timeout_events) == 1
    assert len(risk.block_calls) == 1


def test_unknown_context_ack_emits_evidence_and_returns_false():
    evidence = DummyEvidenceWriter()
    manager = OrderLifecycleManager(evidence_writer=evidence)
    bridge = OrderEventBridge(
        order_lifecycle_manager=manager,
        evidence_writer=evidence,
    )

    ok = bridge.handle_order_ack(
        broker_order_id="UNKNOWN-ACK-1",
        intent_id=None,
        reason="broker_ack",
        payload={"source": "pytest"},
    )

    assert ok is False

    events = evidence.find("order_ack_unknown_context")
    assert len(events) == 1
    assert events[0]["payload"]["broker_order_id"] == "UNKNOWN-ACK-1"
    assert events[0]["payload"]["reason"] == "unknown_order_context"
    assert events[0]["payload"]["event_reason"] == "broker_ack"


def test_out_of_order_full_then_partial_does_not_break_terminal_state():
    evidence = DummyEvidenceWriter()
    manager = OrderLifecycleManager(evidence_writer=evidence)
    bridge = OrderEventBridge(
        order_lifecycle_manager=manager,
        evidence_writer=evidence,
    )

    intent_id, broker_order_id = _register_sent_order(
        manager,
        intent_id="intent-out-of-order",
        broker_order_id="B-OUT-1",
    )

    # out-of-order: ACK 없이 full fill 먼저
    ok_full = bridge.handle_full_fill(
        broker_order_id=broker_order_id,
        filled_qty=10,  # delta
        intent_id=intent_id,
        reason="full_fill",
        payload={"source": "pytest"},
    )
    assert ok_full is True

    rec_after_full = manager.get_record(intent_id)
    assert rec_after_full is not None
    assert rec_after_full.state == OrderState.FILLED
    assert rec_after_full.filled_qty == 10
    assert rec_after_full.remaining_qty == 0

    # 늦게 partial이 들어오면 상태가 깨지지 않아야 함
    ok_partial = bridge.handle_partial_fill(
        broker_order_id=broker_order_id,
        filled_qty=1,   # delta
        remaining_qty=9,
        intent_id=intent_id,
        reason="partial_fill",
        payload={"source": "pytest-late"},
    )

    # terminal 이후 partial은 no-op 성격으로 False/True 둘 다 구현 가능성이 있으나
    # 적어도 상태가 깨지면 안 된다.
    assert ok_partial in (False, True)

    rec_final = manager.get_record(intent_id)
    assert rec_final is not None
    assert rec_final.state == OrderState.FILLED
    assert rec_final.filled_qty == 10
    assert rec_final.remaining_qty == 0


def test_duplicate_full_fill_does_not_double_apply():
    evidence = DummyEvidenceWriter()
    manager = OrderLifecycleManager(evidence_writer=evidence)
    bridge = OrderEventBridge(
        order_lifecycle_manager=manager,
        evidence_writer=evidence,
    )

    intent_id, broker_order_id = _register_sent_order(
        manager,
        intent_id="intent-dup-full",
        broker_order_id="B-DUP-1",
    )

    ok_first = bridge.handle_full_fill(
        broker_order_id=broker_order_id,
        filled_qty=10,  # delta
        intent_id=intent_id,
        reason="full_fill",
        payload={"source": "pytest"},
    )
    assert ok_first is True

    rec1 = manager.get_record(intent_id)
    assert rec1 is not None
    assert rec1.state == OrderState.FILLED
    assert rec1.filled_qty == 10
    assert rec1.remaining_qty == 0

    ok_second = bridge.handle_full_fill(
        broker_order_id=broker_order_id,
        filled_qty=10,  # duplicate
        intent_id=intent_id,
        reason="full_fill",
        payload={"source": "pytest-duplicate"},
    )

    assert ok_second in (False, True)

    rec2 = manager.get_record(intent_id)
    assert rec2 is not None
    assert rec2.state == OrderState.FILLED
    assert rec2.filled_qty == 10
    assert rec2.remaining_qty == 0


def test_delayed_fill_after_ack_preserves_consistency():
    evidence = DummyEvidenceWriter()
    manager = OrderLifecycleManager(evidence_writer=evidence)
    bridge = OrderEventBridge(
        order_lifecycle_manager=manager,
        evidence_writer=evidence,
    )

    intent_id, broker_order_id = _register_sent_order(
        manager,
        intent_id="intent-delayed-fill",
        broker_order_id="B-DELAY-1",
    )

    ok_ack = bridge.handle_order_ack(
        broker_order_id=broker_order_id,
        intent_id=intent_id,
        reason="broker_ack",
        payload={"source": "pytest"},
    )
    assert ok_ack is True

    rec_after_ack = manager.get_record(intent_id)
    assert rec_after_ack is not None
    assert rec_after_ack.state == OrderState.ACKED

    # fill이 나중에 와도 정상 전이
    ok_full = bridge.handle_full_fill(
        broker_order_id=broker_order_id,
        filled_qty=10,  # delta
        intent_id=intent_id,
        reason="full_fill",
        payload={"source": "pytest-delayed-fill"},
    )
    assert ok_full is True

    rec_final = manager.get_record(intent_id)
    assert rec_final is not None
    assert rec_final.state == OrderState.FILLED
    assert rec_final.filled_qty == 10
    assert rec_final.remaining_qty == 0