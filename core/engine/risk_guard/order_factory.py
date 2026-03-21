from uuid import uuid4


class Order:

    def __init__(self, intent_id, symbol, qty, price):

        self.intent_id = intent_id
        self.symbol = symbol
        self.qty = qty
        self.price = price


class OrderFactory:

    def build_from_signal(self, signal):

        return Order(
            intent_id=f"ord-{uuid4().hex[:12]}",
            symbol=signal.symbol,
            qty=signal.qty,
            price=float(signal.price),
        )