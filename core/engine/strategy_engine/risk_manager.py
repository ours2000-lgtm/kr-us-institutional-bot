from logging import getLogger

logger = getLogger(__name__)


class RiskManager:

    def __init__(self):

        # 종목별 최대 주문 수
        self.max_orders_per_symbol = 1

    def allows(self, signal, open_intents_by_symbol):

        # BUY만 허용 (초기 테스트)
        if signal.action != "BUY":
            return False

        # 중복 주문 방지
        if signal.symbol in open_intents_by_symbol:
            logger.info(
                "Risk block duplicate order symbol=%s",
                signal.symbol,
            )
            return False

        if signal.qty <= 0:
            return False

        if signal.price <= 0:
            return False

        return True