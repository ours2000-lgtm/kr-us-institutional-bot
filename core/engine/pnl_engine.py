from logging import getLogger

logger = getLogger(__name__)


class PnLEngine:

    def __init__(self, position_manager):

        self.position_manager = position_manager

        # symbol -> realized pnl
        self.realized_pnl = {}

    # ---------------------------------
    # 평가손익
    # ---------------------------------

    def calculate_unrealized(self, symbol, current_price):

        position = self.position_manager.get_position(symbol)

        if not position:
            return 0.0

        qty = position.qty
        avg_price = position.avg_price

        pnl = (float(current_price) - float(avg_price)) * qty

        return pnl

    # ---------------------------------
    # 실현손익
    # ---------------------------------

    def apply_realized(self, symbol, sell_price, qty):

        position = self.position_manager.get_position(symbol)

        if not position:
            return

        avg_price = position.avg_price

        pnl = (float(sell_price) - float(avg_price)) * qty

        current = self.realized_pnl.get(symbol, 0.0)

        self.realized_pnl[symbol] = current + pnl

        logger.info(
            "Realized PnL updated symbol=%s pnl=%s total=%s",
            symbol,
            pnl,
            self.realized_pnl[symbol],
        )

    # ---------------------------------
    # 종목 실현손익 조회
    # ---------------------------------

    def get_realized(self, symbol):

        return self.realized_pnl.get(symbol, 0.0)

    # ---------------------------------
    # 전체 실현손익
    # ---------------------------------

    def get_total_realized(self):

        return sum(self.realized_pnl.values())