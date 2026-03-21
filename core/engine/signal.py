from dataclasses import dataclass


@dataclass
class Signal:
    action: str
    symbol: str
    qty: int
    price: float