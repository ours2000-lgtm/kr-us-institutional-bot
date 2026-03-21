from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from engine.position_key import PositionKey


_ALLOWED_SIDES = {"BUY", "SELL"}


def _to_decimal(value) -> Decimal:
    try:
        d = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid decimal value: {value!r}")

    if not d.is_finite():
        raise ValueError(f"non-finite decimal value: {value!r}")

    return d


@dataclass(frozen=True)
class FillEvent:
    key: PositionKey
    order_no: str
    side: str
    fill_qty: int
    fill_price: Decimal
    exchange_time: datetime
    ingest_time: datetime

    def __post_init__(self):
        side = str(self.side).upper().strip()
        object.__setattr__(self, "side", side)

        order_no = str(self.order_no).strip()
        object.__setattr__(self, "order_no", order_no)

        if side not in _ALLOWED_SIDES:
            raise ValueError(f"invalid side: {side}")

        if int(self.fill_qty) <= 0:
            raise ValueError(f"fill_qty must be positive: {self.fill_qty}")

        object.__setattr__(self, "fill_qty", int(self.fill_qty))

        price = _to_decimal(self.fill_price)
        if price <= 0:
            raise ValueError(f"fill_price must be positive: {price}")

        object.__setattr__(self, "fill_price", price)

        if self.exchange_time.tzinfo is None:
            raise ValueError("exchange_time must be timezone-aware")

        if self.ingest_time.tzinfo is None:
            raise ValueError("ingest_time must be timezone-aware")

    def to_dict(self) -> dict:
        return {
            "schema_version": "fill_event_v2",
            "position_key": self.key.to_dict(),
            "position_key_serial": self.key.to_serial(),
            "order_no": self.order_no,
            "side": self.side,
            "fill_qty": self.fill_qty,
            "fill_price": str(self.fill_price),
            "exchange_time": self.exchange_time.isoformat(),
            "ingest_time": self.ingest_time.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FillEvent":

        if "position_key" in data:
            key = PositionKey.from_dict(data["position_key"])

        elif "position_key_serial" in data:
            key = PositionKey.from_serial(data["position_key_serial"])

        else:
            key = PositionKey(
                account_id=data.get("account_id"),
                symbol=data.get("symbol"),
                exchange=data.get("exchange", "KRX"),
                currency=data.get("currency", "KRW"),
                instrument_type=data.get("instrument_type", "EQUITY"),
            )

        return cls(
            key=key,
            order_no=data["order_no"],
            side=data["side"],
            fill_qty=int(data["fill_qty"]),
            fill_price=Decimal(str(data["fill_price"])),
            exchange_time=datetime.fromisoformat(data["exchange_time"]),
            ingest_time=datetime.fromisoformat(data["ingest_time"]),
        )

    def to_serial(self) -> str:
        return (
            f"{self.key.to_serial()}|"
            f"{self.order_no}|"
            f"{self.side}|"
            f"{self.fill_qty}|"
            f"{self.fill_price}|"
            f"{self.exchange_time.isoformat()}"
        )

    def __str__(self) -> str:
        return self.to_serial()