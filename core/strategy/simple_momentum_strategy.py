from logging import getLogger

logger = getLogger(__name__)


class SimpleMomentumStrategy:

    def __init__(self):

        self.last_price = None

    def on_tick(self, state, tick):

        price = tick["price"]

        symbol = tick["symbol"]

        if self.last_price is None:

            self.last_price = price

            return None

        signal = None

        if price > self.last_price:

            signal = {
                "action": "BUY",
                "symbol": symbol,
                "qty": 1,
                "price": price,
            }

        elif price < self.last_price:

            signal = {
                "action": "SELL",
                "symbol": symbol,
                "qty": 1,
                "price": price,
            }

        self.last_price = price

        if signal:

            logger.debug("Signal generated %s", signal)

        return signal