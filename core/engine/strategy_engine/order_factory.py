from uuid import uuid4
from runtime.order_state import Order


class OrderFactory:

    def build_from_signal(self, signal) -> Order:

        return Order(
            intent_id=f"ord-{uuid4().hex[:12]}",
            symbol=signal.symbol,
            qty=signal.qty,
            price=float(signal.price),
        )