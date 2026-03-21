# path: core/execution/order_permission.py

from typing import Tuple

from core.control_plane.runtime_state_policy import get_runtime_policy


def evaluate_order_permission(state: str, side: str) -> Tuple[bool, str]:
    state = str(state).strip().upper()
    side = str(side).strip().upper()

    policy = get_runtime_policy(state)
    if policy is None:
        return False, f"unknown_state:{state}"

    if side not in {"BUY", "SELL"}:
        return False, f"invalid_side:{side}"

    if side == "BUY":
        if not policy.buy_order_allowed:
            return False, f"buy_not_allowed_in_state:{state}"
        return True, "ok"

    if side == "SELL":
        if not policy.sell_order_allowed:
            return False, f"sell_not_allowed_in_state:{state}"
        return True, "ok"

    return False, "invalid_side"