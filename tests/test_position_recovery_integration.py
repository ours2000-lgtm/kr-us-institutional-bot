# path: tests/test_position_recovery_integration.py

import pytest

from engine.position_manager import PositionManager
from engine.recovery_fsm import (
    RecoveryFSM,
    STATE_READY,
    STATE_RECOVERING,
)


class DummyFill:
    def __init__(self, symbol, side, fill_qty, fill_price):
        self.symbol = symbol
        self.side = side
        self.fill_qty = fill_qty
        self.fill_price = fill_price


def test_buy_fill_blocked_during_recovering():
    fsm = RecoveryFSM(initial_state=STATE_RECOVERING)

    pm = PositionManager()
    pm.set_recovery_state_supplier(fsm.get_state)

    fill = DummyFill(
        symbol="005930",
        side="BUY",
        fill_qty=10,
        fill_price=70000,
    )

    with pytest.raises(ValueError, match="fill application returned no result"):
        pm.apply_fill(fill)

    assert pm.get_position_snapshot("005930") is None


def test_sell_fill_allowed_during_recovering_for_existing_position():
    fsm = RecoveryFSM(initial_state=STATE_RECOVERING)

    pm = PositionManager()
    pm.set_recovery_state_supplier(fsm.get_state)

    broker_snapshot = {
        "positions": {
            "acc|005930|KRX|KRW|EQUITY": {
                "symbol": "005930",
                "qty": 10,
                "avg_price": "70000",
            }
        }
    }

    pm.replace_active_positions_from_broker_snapshot(broker_snapshot)

    fill = DummyFill(
        symbol="005930",
        side="SELL",
        fill_qty=4,
        fill_price=71000,
    )

    result = pm.apply_fill(fill)

    assert result is not None
    assert result["side"] == "SELL"
    assert result["new_qty"] == 6
    assert result["avg_price"] == 70000.0

    snapshot = pm.get_position_snapshot("005930")
    assert snapshot is not None
    assert snapshot["qty"] == 6
    assert snapshot["avg_price"] == "70000.0"


def test_sell_fill_rejected_during_recovering_without_existing_position():
    fsm = RecoveryFSM(initial_state=STATE_RECOVERING)

    pm = PositionManager()
    pm.set_recovery_state_supplier(fsm.get_state)

    fill = DummyFill(
        symbol="005930",
        side="SELL",
        fill_qty=4,
        fill_price=71000,
    )

    with pytest.raises(ValueError, match="fill application returned no result"):
        pm.apply_fill(fill)

    assert pm.get_position_snapshot("005930") is None


def test_buy_fill_allowed_in_ready():
    fsm = RecoveryFSM(initial_state=STATE_READY)

    pm = PositionManager()
    pm.set_recovery_state_supplier(fsm.get_state)

    fill = DummyFill(
        symbol="005930",
        side="BUY",
        fill_qty=3,
        fill_price=70000,
    )

    result = pm.apply_fill(fill)

    assert result is not None
    assert result["side"] == "BUY"
    assert result["new_qty"] == 3

    snapshot = pm.get_position_snapshot("005930")
    assert snapshot is not None
    assert snapshot["qty"] == 3