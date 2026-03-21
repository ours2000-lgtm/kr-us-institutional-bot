from dataclasses import dataclass


@dataclass(frozen=True)
class PositionKey:

    account_id: str
    symbol: str
    exchange: str
    currency: str
    instrument_type: str

    def __post_init__(self):

        object.__setattr__(self, "account_id", self.account_id.strip())
        object.__setattr__(self, "symbol", self.symbol.upper().strip())
        object.__setattr__(self, "exchange", self.exchange.upper().strip())
        object.__setattr__(self, "currency", self.currency.upper().strip())
        object.__setattr__(self, "instrument_type", self.instrument_type.upper().strip())

        if not self.account_id:
            raise ValueError("account_id required")

        if not self.symbol:
            raise ValueError("symbol required")

        if len(self.currency) != 3:
            raise ValueError("currency must be ISO-4217 code")

    def to_serial(self) -> str:

        return (
            f"{self.account_id}|"
            f"{self.symbol}|"
            f"{self.exchange}|"
            f"{self.currency}|"
            f"{self.instrument_type}"
        )

    def __str__(self):

        return self.to_serial()