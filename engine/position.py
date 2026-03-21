from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from engine.position_key import PositionKey


@dataclass
class Position:
    key: PositionKey
    qty: int = 0
    avg_price: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    last_update: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "position_key_serial": self.key.to_serial(),
            "position_key": self.key.to_dict(),
            "qty": self.qty,
            "avg_price": str(self.avg_price),
            "realized_pnl": str(self.realized_pnl),
            "last_update": self.last_update.isoformat() if self.last_update else None,
        }