from logging import getLogger

logger = getLogger(__name__)


class KiwoomEventNormalizer:

    def __init__(self, execution_controller=None):

        self.execution_controller = execution_controller

        # broker_order_id -> intent_id
        self.order_map = {}

    # ---------------------------------
    # 주문 등록
    # ---------------------------------

    def register_order(self, intent_id, broker_order_id):

        if not broker_order_id:
            return

        self.order_map[str(broker_order_id).strip()] = intent_id

    # ---------------------------------
    # 주문 종료 처리
    # ---------------------------------

    def handle_order_closed(self, broker_order_id, symbol):

        intent_id = self.order_map.get(str(broker_order_id).strip())

        if not intent_id:
            return

        if self.execution_controller:

            self.execution_controller.mark_order_closed_by_intent(
                intent_id,
                symbol,
            )

        logger.info(
            "Order closed broker_order_id=%s intent_id=%s symbol=%s",
            broker_order_id,
            intent_id,
            symbol,
        )