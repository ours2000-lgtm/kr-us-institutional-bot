from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging import getLogger


logger = getLogger(__name__)


@dataclass
class Position:
    symbol: str
    qty: int = 0
    avg_price: float = 0.0
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PositionManager:

    def __init__(self):

        # symbol -> Position
        self.positions = {}

    # ---------------------------------
    # 조회
    # ---------------------------------

    def get_position(self, symbol):

        return self.positions.get(symbol)

    def get_qty(self, symbol):

        position = self.positions.get(symbol)
        if not position:
            return 0
        return position.qty

    def has_position(self, symbol):

        return self.get_qty(symbol) > 0

    # ---------------------------------
    # 체결 반영
    # ---------------------------------

    def apply_buy_fill(self, symbol, fill_qty, fill_price):

        if fill_qty <= 0:
            logger.warning(
                "Invalid buy fill qty symbol=%s fill_qty=%s",
                symbol,
                fill_qty,
            )
            return

        position = self.positions.get(symbol)

        if position is None:
            position = Position(symbol=symbol)
            self.positions[symbol] = position

        old_qty = position.qty
        new_qty = old_qty + fill_qty

        if new_qty <= 0:
            logger.warning(
                "Unexpected new_qty after buy fill symbol=%s old_qty=%s fill_qty=%s",
                symbol,
                old_qty,
                fill_qty,
            )
            return

        if old_qty == 0:
            new_avg = float(fill_price)
        else:
            new_avg = (
                (position.avg_price * old_qty) + (float(fill_price) * fill_qty)
            ) / new_qty

        position.qty = new_qty
        position.avg_price = new_avg
        position.last_update = datetime.now(timezone.utc)

        logger.info(
            "Position BUY applied symbol=%s qty=%s avg_price=%s",
            symbol,
            position.qty,
            position.avg_price,
        )

    def apply_sell_fill(self, symbol, fill_qty, fill_price):

        if fill_qty <= 0:
            logger.warning(
                "Invalid sell fill qty symbol=%s fill_qty=%s",
                symbol,
                fill_qty,
            )
            return

        position = self.positions.get(symbol)

        if position is None:
            logger.warning(
                "Sell fill on empty position symbol=%s fill_qty=%s",
                symbol,
                fill_qty,
            )
            return

        if fill_qty > position.qty:
            logger.warning(
                "Sell fill exceeds position symbol=%s pos_qty=%s fill_qty=%s",
                symbol,
                position.qty,
                fill_qty,
            )
            return

        new_qty = position.qty - fill_qty

        position.qty = new_qty
        position.last_update = datetime.now(timezone.utc)

        if new_qty == 0:
            position.avg_price = 0.0

        logger.info(
            "Position SELL applied symbol=%s qty=%s avg_price=%s",
            symbol,
            position.qty,
            position.avg_price,
        )

    # ---------------------------------
    # 범용 체결 반영
    # ---------------------------------

    def apply_fill(self, symbol, side, fill_qty, fill_price):

        side = str(side).upper().strip()

        if side == "BUY":
            self.apply_buy_fill(symbol, fill_qty, fill_price)
            return

        if side == "SELL":
            self.apply_sell_fill(symbol, fill_qty, fill_price)
            return

        logger.warning(
            "Unknown fill side symbol=%s side=%s qty=%s price=%s",
            symbol,
            side,
            fill_qty,
            fill_price,
        )

    # ---------------------------------
    # 스냅샷
    # ---------------------------------

    def snapshot(self):

        result = {}

        for symbol, position in self.positions.items():
            result[symbol] = {
                "qty": position.qty,
                "avg_price": position.avg_price,
                "last_update": position.last_update,
            }

        return result