from dataclasses import dataclass
from datetime import datetime, timezone
from engine.position_key import PositionKey


@dataclass(frozen=True)
class FillEvent:

    key: PositionKey
    side: str
    qty: int
    price: float
    timestamp: datetime

    def __post_init__(self):

        if self.qty <= 0:
            raise ValueError("qty must be positive")

        if self.price <= 0:
            raise ValueError("price must be positive")

        side = self.side.upper()

        if side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")

        object.__setattr__(self, "side", side)

        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be tz-aware UTC")

    @staticmethod
    def now(key, side, qty, price):

        return FillEvent(
            key=key,
            side=side,
            qty=qty,
            price=price,
            timestamp=datetime.now(timezone.utc),
        )