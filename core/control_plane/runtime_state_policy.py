# path: core/control_plane/runtime_state_policy.py

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RuntimeStatePolicy:
    buy_order_allowed: bool
    sell_order_allowed: bool
    buy_fill_allowed: bool
    sell_fill_allowed: bool
    description: str


RUNTIME_STATE_POLICY = {
    "CONNECTED": RuntimeStatePolicy(
        buy_order_allowed=False,
        sell_order_allowed=False,
        buy_fill_allowed=False,
        sell_fill_allowed=False,
        description="connected only; trading not yet allowed",
    ),
    "DISCONNECTED": RuntimeStatePolicy(
        buy_order_allowed=False,
        sell_order_allowed=False,
        buy_fill_allowed=False,
        sell_fill_allowed=False,
        description="disconnected; fail-closed",
    ),
    "RECONNECTING": RuntimeStatePolicy(
        buy_order_allowed=False,
        sell_order_allowed=False,
        buy_fill_allowed=False,
        sell_fill_allowed=False,
        description="reconnecting; fail-closed",
    ),
    "RECOVERING": RuntimeStatePolicy(
        buy_order_allowed=False,
        sell_order_allowed=False,
        buy_fill_allowed=False,
        sell_fill_allowed=True,
        description="recovery in progress; sell fill only for reconciliation safety",
    ),
    "READY_PENDING": RuntimeStatePolicy(
        buy_order_allowed=False,
        sell_order_allowed=False,
        buy_fill_allowed=False,
        sell_fill_allowed=True,
        description="cooldown after recovery; late sell fills allowed",
    ),
    "READY": RuntimeStatePolicy(
        buy_order_allowed=True,
        sell_order_allowed=True,
        buy_fill_allowed=True,
        sell_fill_allowed=True,
        description="normal trading allowed",
    ),
    "EXIT_ONLY": RuntimeStatePolicy(
        buy_order_allowed=False,
        sell_order_allowed=True,
        buy_fill_allowed=False,
        sell_fill_allowed=True,
        description="new entry blocked; exit only",
    ),
    "BLOCKED": RuntimeStatePolicy(
        buy_order_allowed=False,
        sell_order_allowed=False,
        buy_fill_allowed=False,
        sell_fill_allowed=False,
        description="blocked; manual intervention required",
    ),
}


def normalize_runtime_state(state: str) -> str:
    return str(state).strip().upper()


def get_runtime_policy(state: str) -> Optional[RuntimeStatePolicy]:
    return RUNTIME_STATE_POLICY.get(normalize_runtime_state(state))