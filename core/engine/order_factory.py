# path: core/engine/order_factory.py

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


class OrderFactoryError(Exception):
    pass


@dataclass
class Order:
    intent_id: str
    symbol: str
    side: str
    qty: int
    price: object
    order_type: str = "LIMIT"
    status: str = "CREATED"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    broker_order_id: str = None

    def __post_init__(self):
        self.intent_id = str(self.intent_id).strip()
        self.symbol = str(self.symbol).strip()
        self.side = str(self.side).strip().upper()
        self.order_type = str(self.order_type).strip().upper()
        self.status = str(self.status).strip().upper()
        self.broker_order_id = (
            None if self.broker_order_id is None
            else str(self.broker_order_id).strip()
        )

        if not self.intent_id:
            raise ValueError("intent_id is required")

        if not self.symbol:
            raise ValueError("symbol is required")

        if self.side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")

        if isinstance(self.qty, bool):
            raise ValueError("qty must not be bool")

        try:
            self.qty = int(self.qty)
        except (TypeError, ValueError):
            raise ValueError("qty must be int-convertible")

        if self.qty <= 0:
            raise ValueError("qty must be > 0")

        if self.order_type not in {"MARKET", "LIMIT"}:
            raise ValueError("order_type must be MARKET or LIMIT")

        if self.order_type == "MARKET":
            self.price = 0
        else:
            if isinstance(self.price, bool):
                raise ValueError("price must not be bool")

            try:
                price = float(self.price)
            except (TypeError, ValueError):
                raise ValueError("price must be numeric for LIMIT order")

            if price <= 0:
                raise ValueError("price must be > 0 for LIMIT order")

            self.price = price

        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")


class OrderFactory:
    """
    Signal -> Order 변환기

    OrderFactory guarantees:
    - symbol: non-empty string
    - side: BUY | SELL (uppercase)
    - qty: int > 0
    - order_type: MARKET | LIMIT (uppercase)
    - price: numeric (LIMIT) or 0 (MARKET)
    """

    def build_from_signal(self, signal):
        symbol = str(getattr(signal, "symbol", "")).strip()
        if not symbol:
            raise OrderFactoryError("signal.symbol is required")

        side = str(getattr(signal, "action", "")).strip().upper()
        if side not in {"BUY", "SELL"}:
            raise OrderFactoryError("signal.action must be BUY or SELL")

        qty_raw = getattr(signal, "qty", None)
        if isinstance(qty_raw, bool):
            raise OrderFactoryError("signal.qty must not be bool")

        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            raise OrderFactoryError("signal.qty must be int-convertible")

        if qty <= 0:
            raise OrderFactoryError("signal.qty must be > 0")

        order_type = str(getattr(signal, "order_type", "LIMIT")).strip().upper()
        if order_type not in {"MARKET", "LIMIT"}:
            raise OrderFactoryError("signal.order_type must be MARKET or LIMIT")

        price_raw = getattr(signal, "price", None)

        if order_type == "MARKET":
            price = 0
        else:
            if price_raw is None:
                raise OrderFactoryError("signal.price is required for LIMIT order")

            if isinstance(price_raw, bool):
                raise OrderFactoryError("signal.price must not be bool")

            try:
                price = float(price_raw)
            except (TypeError, ValueError):
                raise OrderFactoryError("signal.price must be numeric for LIMIT order")

            if price <= 0:
                raise OrderFactoryError("signal.price must be > 0 for LIMIT order")

        return Order(
            intent_id=str(uuid4()),
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            order_type=order_type,
        )