from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


# ======================================
# Order State Enum
# ======================================

class OrderState(Enum):

    CREATED = "CREATED"

    VALIDATED = "VALIDATED"

    SUBMIT_REQUESTED = "SUBMIT_REQUESTED"

    SUBMIT_ACCEPTED = "SUBMIT_ACCEPTED"

    SUBMIT_REJECTED = "SUBMIT_REJECTED"

    OPEN = "OPEN"

    PARTIALLY_FILLED = "PARTIALLY_FILLED"

    FILLED = "FILLED"

    CANCEL_REQUESTED = "CANCEL_REQUESTED"

    CANCELED = "CANCELED"

    REPLACE_REQUESTED = "REPLACE_REQUESTED"

    REPLACED = "REPLACED"

    FAILED = "FAILED"

    UNKNOWN = "UNKNOWN"


# ======================================
# Order Event Enum
# ======================================

class OrderEvent(Enum):

    INTENT_CREATED = "INTENT_CREATED"

    PRETRADE_PASSED = "PRETRADE_PASSED"

    PRETRADE_BLOCKED = "PRETRADE_BLOCKED"

    SUBMIT_CALLED = "SUBMIT_CALLED"

    BROKER_ACK = "BROKER_ACK"

    BROKER_REJECT = "BROKER_REJECT"

    ORDER_OPENED = "ORDER_OPENED"

    PARTIAL_FILL = "PARTIAL_FILL"

    FULL_FILL = "FULL_FILL"

    CANCEL_CALLED = "CANCEL_CALLED"

    CANCEL_ACK = "CANCEL_ACK"

    REPLACE_CALLED = "REPLACE_CALLED"

    REPLACE_ACK = "REPLACE_ACK"

    BROKER_ERROR = "BROKER_ERROR"

    UNMAPPED_EVENT = "UNMAPPED_EVENT"


# ======================================
# Allowed State Transitions
# ======================================

ALLOWED_TRANSITIONS = {

    OrderState.CREATED: {
        OrderEvent.PRETRADE_PASSED: OrderState.VALIDATED,
        OrderEvent.PRETRADE_BLOCKED: OrderState.FAILED,
    },

    OrderState.VALIDATED: {
        OrderEvent.SUBMIT_CALLED: OrderState.SUBMIT_REQUESTED,
    },

    OrderState.SUBMIT_REQUESTED: {
        OrderEvent.BROKER_ACK: OrderState.SUBMIT_ACCEPTED,
        OrderEvent.BROKER_REJECT: OrderState.SUBMIT_REJECTED,
    },

    OrderState.SUBMIT_ACCEPTED: {
        OrderEvent.ORDER_OPENED: OrderState.OPEN,
    },

    OrderState.OPEN: {
        OrderEvent.PARTIAL_FILL: OrderState.PARTIALLY_FILLED,
        OrderEvent.FULL_FILL: OrderState.FILLED,
        OrderEvent.CANCEL_CALLED: OrderState.CANCEL_REQUESTED,
    },

    OrderState.PARTIALLY_FILLED: {
        OrderEvent.PARTIAL_FILL: OrderState.PARTIALLY_FILLED,
        OrderEvent.FULL_FILL: OrderState.FILLED,
        OrderEvent.CANCEL_CALLED: OrderState.CANCEL_REQUESTED,
    },

    OrderState.CANCEL_REQUESTED: {
        OrderEvent.CANCEL_ACK: OrderState.CANCELED,
    }

}


# ======================================
# Order Object
# ======================================

@dataclass
class Order:

    intent_id: str

    symbol: str

    qty: int

    price: float

    state: OrderState = OrderState.CREATED

    filled_qty: int = 0

    remaining_qty: int = 0

    avg_fill_price: float = 0.0

    reason_code: str = ""

    raw_broker_payload_ref: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)

    last_update: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):

        if self.remaining_qty == 0 and self.filled_qty == 0:
            self.remaining_qty = self.qty


# ======================================
# Fill Object
# ======================================

@dataclass
class Fill:

    fill_qty: int

    fill_price: float

    filled_at: datetime

    broker_fill_id: str = ""

    raw_broker_payload_ref: str = ""


# ======================================
# State Transition Engine
# ======================================

def apply_event(order: Order, event: OrderEvent,
                reason_code: str = "",
                raw_broker_payload_ref: str = ""):

    current_state = order.state

    allowed = ALLOWED_TRANSITIONS.get(current_state, {})

    if event not in allowed:

        print(
            f"[STATE WARNING] invalid transition "
            f"{current_state.value} + {event.value}"
        )

        order.state = OrderState.UNKNOWN

        order.reason_code = "INVALID_TRANSITION"

        return order

    new_state = allowed[event]

    order.state = new_state

    order.reason_code = reason_code

    order.raw_broker_payload_ref = raw_broker_payload_ref

    order.last_update = datetime.utcnow()

    print(
        f"[STATE] {current_state.value} -> {new_state.value} "
        f"(event={event.value})"
    )

    return order


# ======================================
# Fill Processing
# ======================================

def apply_fill(order: Order, fill: Fill):

    if fill.fill_qty <= 0:

        print("[FILL ERROR] invalid fill quantity")

        order.state = OrderState.UNKNOWN

        order.reason_code = "INVALID_FILL_QTY"

        return order

    if fill.fill_qty > order.remaining_qty:

        print("[FILL ERROR] fill exceeds remaining qty")

        order.state = OrderState.UNKNOWN

        order.reason_code = "FILL_EXCEEDS_REMAINING"

        return order

    old_filled = order.filled_qty

    new_filled = old_filled + fill.fill_qty

    if old_filled == 0:

        order.avg_fill_price = fill.fill_price

    else:

        order.avg_fill_price = (
            (order.avg_fill_price * old_filled)
            + (fill.fill_price * fill.fill_qty)
        ) / new_filled

    order.filled_qty = new_filled

    order.remaining_qty = order.qty - new_filled

    order.raw_broker_payload_ref = fill.raw_broker_payload_ref

    order.last_update = datetime.utcnow()

    if order.remaining_qty == 0:

        apply_event(order, OrderEvent.FULL_FILL)

    else:

        apply_event(order, OrderEvent.PARTIAL_FILL)

    return order