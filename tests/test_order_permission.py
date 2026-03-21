from core.execution.order_permission import evaluate_order_permission
from engine.recovery_fsm import (
    STATE_RECOVERING,
    STATE_EXIT_ONLY,
)


def test_buy_blocked_when_not_ready():
    allowed, reason = evaluate_order_permission(STATE_RECOVERING, "BUY")
    assert not allowed
    assert reason == "buy_not_allowed_in_state:RECOVERING"


def test_sell_allowed_in_exit_only():
    allowed, reason = evaluate_order_permission(STATE_EXIT_ONLY, "SELL")
    assert allowed
    assert reason == "ok"


def test_unknown_state_fail_closed():
    allowed, reason = evaluate_order_permission("UNKNOWN", "BUY")
    assert not allowed
    assert reason.startswith("unknown_state:")