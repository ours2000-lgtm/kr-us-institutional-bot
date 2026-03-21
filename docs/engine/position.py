from dataclasses import dataclass
from datetime import datetime
from engine.position_key import PositionKey


@dataclass
class Position:

    key: PositionKey
    qty: int = 0
    avg_price: float = 0.0
    realized_pnl: float = 0.0
    last_update: datetime = None