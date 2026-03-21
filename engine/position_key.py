# path: engine/position_key.py

from dataclasses import dataclass


@dataclass(frozen=True)
class PositionKey:
    account_id: str
    symbol: str
    exchange: str
    currency: str
    instrument_type: str

    def __post_init__(self):
        object.__setattr__(self, "account_id", str(self.account_id).strip())
        object.__setattr__(self, "symbol", str(self.symbol).strip())
        object.__setattr__(self, "exchange", str(self.exchange).strip().upper())
        object.__setattr__(self, "currency", str(self.currency).strip().upper())
        object.__setattr__(
            self,
            "instrument_type",
            str(self.instrument_type).strip().upper(),
        )

        if not self.account_id:
            raise ValueError("account_id is required")
        if not self.symbol:
            raise ValueError("symbol is required")
        if not self.exchange:
            raise ValueError("exchange is required")
        if not self.currency:
            raise ValueError("currency is required")
        if not self.instrument_type:
            raise ValueError("instrument_type is required")

    def to_serial(self) -> str:
        return (
            f"{self.account_id}|"
            f"{self.symbol}|"
            f"{self.exchange}|"
            f"{self.currency}|"
            f"{self.instrument_type}"
        )

    def to_dict(self) -> dict:
        return {
            "account_id": self.account_id,
            "symbol": self.symbol,
            "exchange": self.exchange,
            "currency": self.currency,
            "instrument_type": self.instrument_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PositionKey":
        if not isinstance(data, dict):
            raise ValueError("data must be dict")

        return cls(
            account_id=data["account_id"],
            symbol=data["symbol"],
            exchange=data["exchange"],
            currency=data["currency"],
            instrument_type=data["instrument_type"],
        )

    @classmethod
    def from_serial(cls, serial: str) -> "PositionKey":
        text = str(serial).strip()
        if not text:
            raise ValueError("serial is required")

        parts = text.split("|")
        if len(parts) != 5:
            raise ValueError(f"invalid position key serial: {serial!r}")

        account_id, symbol, exchange, currency, instrument_type = parts

        return cls(
            account_id=account_id,
            symbol=symbol,
            exchange=exchange,
            currency=currency,
            instrument_type=instrument_type,
        )

    def __str__(self) -> str:
        return self.to_serial()