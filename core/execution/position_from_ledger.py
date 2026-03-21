from decimal import Decimal
from typing import Dict, Any


class Position:
    """
    Long-only position model.

    책임:
    - qty
    - avg_price
    """

    def __init__(self):
        self.qty = Decimal("0")
        self.avg_price = Decimal("0")


def apply_fill(position: Position, pnl, fill: Dict[str, Any]):
    """
    Fill → Position + PnL 업데이트

    position: Position
    pnl: PnLState
    """

    # ---------------------------
    # 필드 안전성
    # ---------------------------
    try:
        side = str(fill["side"]).strip().upper()
        qty = Decimal(str(fill["fill_qty"]))
        price = Decimal(str(fill["fill_price"]))
    except Exception:
        return

    # ---------------------------
    # 값 검증
    # ---------------------------
    if qty <= 0 or price <= 0:
        return

    # ---------------------------
    # BUY
    # ---------------------------
    if side == "BUY":
        total_cost = position.avg_price * position.qty + price * qty
        position.qty += qty

        if position.qty > 0:
            position.avg_price = total_cost / position.qty

    # ---------------------------
    # SELL (long-only)
    # ---------------------------
    elif side == "SELL":

        if position.qty <= 0:
            return

        # 초과 청산 방어
        sell_qty = min(qty, position.qty)

        realized = (price - position.avg_price) * sell_qty

        # 👉 PnL로 분리
        pnl.add_realized(realized)

        position.qty -= sell_qty

        if position.qty == 0:
            position.avg_price = Decimal("0")