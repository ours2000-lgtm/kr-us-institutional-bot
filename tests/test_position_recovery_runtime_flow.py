# path: tests/test_position_recovery_runtime_flow.py

import pytest

from engine.position_manager import PositionManager
from engine.recovery_fsm import (
    RecoveryFSM,
    STATE_READY,
    STATE_READY_PENDING,
    STATE_RECOVERING,
    EVENT_SNAPSHOT_OK,
    EVENT_COOLDOWN_ELAPSED,
)


class DummyFill:
    def __init__(self, symbol, side, fill_qty, fill_price):
        self.symbol = symbol
        self.side = side
        self.fill_qty = fill_qty
        self.fill_price = fill_price


def test_buy_fill_blocked_until_ready_then_allowed():
    fsm = RecoveryFSM(initial_state=STATE_RECOVERING)

    pm = PositionManager()
    pm.set_recovery_state_supplier(fsm.get_state)

    buy_fill = DummyFill(
        symbol="005930",
        side="BUY",
        fill_qty=1,
        fill_price=70000,
    )

    # ---------------------------------
    # RECOVERING: BUY blocked
    # ---------------------------------
    with pytest.raises(ValueError, match="fill application returned no result"):
        pm.apply_fill(buy_fill)

    assert pm.get_position_snapshot("005930") is None
    assert fsm.get_state() == STATE_RECOVERING

    # ---------------------------------
    # RECOVERING -> READY_PENDING
    # ---------------------------------
    transition1 = fsm.transition(
        STATE_READY_PENDING,
        event=EVENT_SNAPSHOT_OK,
        reason="snapshot and reconciliation passed",
    )

    assert transition1.from_state == STATE_RECOVERING
    assert transition1.to_state == STATE_READY_PENDING
    assert fsm.get_state() == STATE_READY_PENDING

    # ---------------------------------
    # READY_PENDING: BUY still blocked
    # ---------------------------------
    with pytest.raises(ValueError, match="fill application returned no result"):
        pm.apply_fill(buy_fill)

    assert pm.get_position_snapshot("005930") is None

    # ---------------------------------
    # READY_PENDING -> READY
    # ---------------------------------
    transition2 = fsm.transition(
        STATE_READY,
        event=EVENT_COOLDOWN_ELAPSED,
        reason="cooldown elapsed and stream stable",
    )

    assert transition2.from_state == STATE_READY_PENDING
    assert transition2.to_state == STATE_READY
    assert fsm.get_state() == STATE_READY

    # ---------------------------------
    # READY: BUY allowed
    # ---------------------------------
    result = pm.apply_fill(buy_fill)

    assert result is not None
    assert result["side"] == "BUY"
    assert result["new_qty"] == 1
    assert result["avg_price"] == 70000.0

    snapshot = pm.get_position_snapshot("005930")
    assert snapshot is not None
    assert snapshot["qty"] == 1
    assert snapshot["avg_price"] == "70000.0"


def test_ready_pending_to_ready_requires_cooldown_event_in_runtime_flow():
    fsm = RecoveryFSM(initial_state=STATE_READY_PENDING)

    pm = PositionManager()
    pm.set_recovery_state_supplier(fsm.get_state)

    buy_fill = DummyFill(
        symbol="005930",
        side="BUY",
        fill_qty=1,
        fill_price=70000,
    )

    # READY_PENDING에서는 BUY 불가
    with pytest.raises(ValueError, match="fill application returned no result"):
        pm.apply_fill(buy_fill)

    # 잘못된 이벤트로 READY 진입 시도 -> 차단
    with pytest.raises(ValueError, match="invalid event for transition"):
        fsm.transition(
            STATE_READY,
            event=EVENT_SNAPSHOT_OK,
            reason="wrong event",
        )

    assert fsm.get_state() == STATE_READY_PENDING

    # 올바른 이벤트 -> READY
    fsm.transition(
        STATE_READY,
        event=EVENT_COOLDOWN_ELAPSED,
        reason="cooldown complete",
    )

    assert fsm.get_state() == STATE_READY

    # 이제 BUY 허용
    result = pm.apply_fill(buy_fill)
    assert result is not None
    assert result["new_qty"] == 1