import threading
from datetime import datetime, timezone

from engine.position import Position
from engine.fill_event import FillEvent


class PositionManager:

    def __init__(self, on_error=None):

        self._positions = {}
        self._lock = threading.Lock()
        self._on_error = on_error

    def get_position(self, key):

        return self._positions.get(key)

    def get_or_create_position(self, key):

        pos = self._positions.get(key)

        if pos is None:

            pos = Position(key=key)

            self._positions[key] = pos

        return pos

    def apply_fill(self, fill: FillEvent):

        with self._lock:

            pos = self.get_or_create_position(fill.key)

            try:

                if fill.side == "BUY":

                    self._apply_buy(pos, fill)

                else:

                    self._apply_sell(pos, fill)

                pos.last_update = datetime.now(timezone.utc)

            except Exception as e:

                if self._on_error:
                    self._on_error(fill, e)

                raise

    def _apply_buy(self, pos, fill):

        total_cost = pos.avg_price * pos.qty
        total_cost += fill.price * fill.qty

        pos.qty += fill.qty

        pos.avg_price = total_cost / pos.qty

    def _apply_sell(self, pos, fill):

        if pos.qty == 0:
            raise RuntimeError("sell without position")

        if fill.qty > pos.qty:
            raise RuntimeError("oversell")

        pnl = (fill.price - pos.avg_price) * fill.qty

        pos.realized_pnl += pnl

        pos.qty -= fill.qty

        if pos.qty == 0:
            pos.avg_price = 0.0

    def snapshot(self):

        result = {}

        for key, pos in self._positions.items():

            result[str(key)] = {

                "qty": pos.qty,
                "avg_price": pos.avg_price,
                "realized_pnl": pos.realized_pnl,
                "last_update": pos.last_update.isoformat()
                if pos.last_update
                else None,
            }

        return result