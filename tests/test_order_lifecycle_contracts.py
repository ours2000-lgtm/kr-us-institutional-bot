# path: tests/test_order_lifecycle_contracts.py

import pytest

from core.execution.order_lifecycle import OrderLifecycleManager, OrderState


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


def _new_manager():
    return OrderLifecycleManager(evidence_writer=DummyEvidenceWriter())


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
        metadata={"source": "pytest"},
    )
    manager.mark_sent(
        intent_id=intent_id,
        broker_order_id=broker_order_id,
        metadata_update={"source": "pytest"},
    )
    return intent_id, broker_order_id


def test_bind_broker_order_id_resolves_intent_id():
    manager = _new_manager()

    manager.register_new_intent(
        intent_id="intent-bind-1",
        symbol="005930",
        side="BUY",
        qty=10,
    )

    manager.bind_broker_order_id(
        intent_id="intent-bind-1",
        broker_order_id="B-BIND-1",
    )

    resolved = manager.resolve_intent_id("B-BIND-1")
    assert resolved == "intent-bind-1"

    rec = manager.get_record_by_broker_order_id("B-BIND-1")
    assert rec is not None
    assert rec.intent_id == "intent-bind-1"
    assert rec.broker_order_id == "B-BIND-1"


def test_get_record_returns_copy_not_mutable_reference():
    manager = _new_manager()

    manager.register_new_intent(
        intent_id="intent-copy-1",
        symbol="005930",
        side="BUY",
        qty=10,
    )

    rec1 = manager.get_record("intent-copy-1")
    assert rec1 is not None

    # 외부에서 복사본을 수정해도 내부 원본이 바뀌면 안 된다
    rec1.state = OrderState.FILLED
    rec1.filled_qty = 999
    rec1.metadata["tampered"] = True

    rec2 = manager.get_record("intent-copy-1")
    assert rec2 is not None
    assert rec2.state == OrderState.NEW
    assert rec2.filled_qty == 0
    assert rec2.metadata.get("tampered") is None


def test_partial_fill_rejects_inconsistent_remaining_qty():
    manager = _new_manager()
    intent_id, broker_order_id = _register_sent_order(
        manager,
        intent_id="intent-partial-inconsistent",
        qty=10,
        broker_order_id="B-PARTIAL-1",
    )

    # 1차 partial: delta=3, remaining=7 -> 정상
    rec1 = manager.mark_partially_filled(
        intent_id=intent_id,
        broker_order_id=broker_order_id,
        filled_qty=3,       # delta
        remaining_qty=7,
        reason="partial_fill",
        metadata_update={"step": 1},
    )
    assert rec1.state == OrderState.PARTIALLY_FILLED
    assert rec1.filled_qty == 3
    assert rec1.remaining_qty == 7

    # 2차 partial: 기존 filled=3, 이번 delta=2 이면 next_filled=5
    # 그런데 remaining=9를 주면 5+9 != 10 이므로 실패해야 한다.
    with pytest.raises(ValueError, match="filled_qty \\+ remaining_qty must equal original order qty"):
        manager.mark_partially_filled(
            intent_id=intent_id,
            broker_order_id=broker_order_id,
            filled_qty=2,       # delta
            remaining_qty=9,    # 불일치
            reason="partial_fill",
            metadata_update={"step": 2},
        )

    rec_final = manager.get_record(intent_id)
    assert rec_final is not None
    assert rec_final.state == OrderState.PARTIALLY_FILLED
    assert rec_final.filled_qty == 3
    assert rec_final.remaining_qty == 7


def test_partial_fill_rejects_overfill():
    manager = _new_manager()
    intent_id, broker_order_id = _register_sent_order(
        manager,
        intent_id="intent-partial-overfill",
        qty=10,
        broker_order_id="B-PARTIAL-OVER-1",
    )

    rec1 = manager.mark_partially_filled(
        intent_id=intent_id,
        broker_order_id=broker_order_id,
        filled_qty=8,       # delta
        remaining_qty=2,
        reason="partial_fill",
    )
    assert rec1.state == OrderState.PARTIALLY_FILLED
    assert rec1.filled_qty == 8
    assert rec1.remaining_qty == 2

    # 기존 filled=8 에서 delta=3 이면 11 > 10
    with pytest.raises(ValueError, match="filled_qty exceeds original order qty"):
        manager.mark_partially_filled(
            intent_id=intent_id,
            broker_order_id=broker_order_id,
            filled_qty=3,       # delta
            remaining_qty=1,
            reason="partial_fill",
        )

    rec_final = manager.get_record(intent_id)
    assert rec_final is not None
    assert rec_final.state == OrderState.PARTIALLY_FILLED
    assert rec_final.filled_qty == 8
    assert rec_final.remaining_qty == 2


def test_full_fill_requires_exact_total_qty():
    manager = _new_manager()
    intent_id, broker_order_id = _register_sent_order(
        manager,
        intent_id="intent-full-exact",
        qty=10,
        broker_order_id="B-FULL-EXACT-1",
    )

    # 먼저 partial 6
    rec1 = manager.mark_partially_filled(
        intent_id=intent_id,
        broker_order_id=broker_order_id,
        filled_qty=6,      # delta
        remaining_qty=4,
        reason="partial_fill",
    )
    assert rec1.state == OrderState.PARTIALLY_FILLED
    assert rec1.filled_qty == 6
    assert rec1.remaining_qty == 4

    # full fill인데 delta=3이면 결과가 9라서 부족 -> 실패
    with pytest.raises(ValueError, match="full fill requires resulting filled_qty >= original order qty"):
        manager.mark_filled(
            intent_id=intent_id,
            broker_order_id=broker_order_id,
            filled_qty=3,   # delta -> 6+3=9
            reason="filled",
        )

    rec_mid = manager.get_record(intent_id)
    assert rec_mid is not None
    assert rec_mid.state == OrderState.PARTIALLY_FILLED
    assert rec_mid.filled_qty == 6
    assert rec_mid.remaining_qty == 4

    # 정확히 남은 4를 채우면 성공
    rec2 = manager.mark_filled(
        intent_id=intent_id,
        broker_order_id=broker_order_id,
        filled_qty=4,   # delta -> 6+4=10
        reason="filled",
    )
    assert rec2.state == OrderState.FILLED
    assert rec2.filled_qty == 10
    assert rec2.remaining_qty == 0


def test_full_fill_rejects_overfill():
    manager = _new_manager()
    intent_id, broker_order_id = _register_sent_order(
        manager,
        intent_id="intent-full-overfill",
        qty=10,
        broker_order_id="B-FULL-OVER-1",
    )

    rec1 = manager.mark_partially_filled(
        intent_id=intent_id,
        broker_order_id=broker_order_id,
        filled_qty=8,      # delta
        remaining_qty=2,
        reason="partial_fill",
    )
    assert rec1.state == OrderState.PARTIALLY_FILLED
    assert rec1.filled_qty == 8
    assert rec1.remaining_qty == 2

    # full fill인데 delta=5면 결과가 13이라서 초과 -> 실패
    with pytest.raises(ValueError, match="full fill exceeds original order qty"):
        manager.mark_filled(
            intent_id=intent_id,
            broker_order_id=broker_order_id,
            filled_qty=5,   # delta -> 8+5=13
            reason="filled",
        )

    rec_final = manager.get_record(intent_id)
    assert rec_final is not None
    assert rec_final.state == OrderState.PARTIALLY_FILLED
    assert rec_final.filled_qty == 8
    assert rec_final.remaining_qty == 2