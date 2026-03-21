# path: core/execution/execution_controller.py

from logging import getLogger

logger = getLogger(__name__)


class ExecutionController:
    def __init__(self, adapter, order_factory, risk_manager, account_type="paper"):
        self.adapter = adapter
        self.order_factory = order_factory
        self.risk_manager = risk_manager
        self.account_type = str(account_type).strip().lower()

    # ---------------------------------
    # Signal 실행
    # ---------------------------------

    def execute_signal(self, signal):
        # ---------------------------------
        # Order 생성
        # ---------------------------------

        if self.order_factory is None:
            raise RuntimeError("order_factory is required in production")

        order = self.order_factory.build_from_signal(signal)

        order_id = getattr(order, "intent_id", None)
        strategy_id = getattr(signal, "strategy_id", None)

        logger.debug(
            "ORDER_BUILT order_id=%s strategy_id=%s symbol=%s qty=%s price=%s account_type=%s",
            order_id,
            strategy_id,
            getattr(order, "symbol", None),
            getattr(order, "qty", None),
            getattr(order, "price", None),
            self.account_type,
        )

        # ---------------------------------
        # 기본 order 유효성 검사
        # ---------------------------------

        symbol = getattr(order, "symbol", None)
        qty = getattr(order, "qty", None)

        if not symbol:
            logger.error(
                "INVALID_ORDER symbol_missing order_id=%s strategy_id=%s account_type=%s",
                order_id,
                strategy_id,
                self.account_type,
            )
            return False

        try:
            qty_int = int(qty)
        except (TypeError, ValueError):
            logger.error(
                "INVALID_ORDER qty_parse_failed order_id=%s strategy_id=%s raw_qty=%r account_type=%s",
                order_id,
                strategy_id,
                qty,
                self.account_type,
            )
            return False

        if qty_int <= 0:
            logger.error(
                "INVALID_ORDER qty_non_positive order_id=%s strategy_id=%s qty=%s account_type=%s",
                order_id,
                strategy_id,
                qty_int,
                self.account_type,
            )
            return False

        # ---------------------------------
        # Recovery 상태 1차 방어선
        # ---------------------------------

        recovery_state = getattr(self.adapter, "recovery_state", "UNKNOWN")

        if recovery_state != "CONNECTED":
            logger.warning(
                "ORDER_BLOCKED_BY_RECOVERY_STATE order_id=%s strategy_id=%s recovery_state=%s account_type=%s",
                order_id,
                strategy_id,
                recovery_state,
                self.account_type,
            )
            return False

        # ---------------------------------
        # Risk 체크
        # ---------------------------------

        allowed, reason = self.risk_manager.evaluate(order)
        block_state = self.risk_manager.get_block_state()

        if not allowed:
            logger.warning(
                "ORDER_BLOCKED order_id=%s strategy_id=%s reason=%s trading_blocked=%s block_reason=%s evaluation_point=%s account_type=%s",
                order_id,
                strategy_id,
                reason,
                block_state.get("trading_blocked"),
                block_state.get("block_reason"),
                "BEFORE_SEND",
                self.account_type,
            )
            return False

        logger.info(
            "RISK_CHECK_PASSED order_id=%s strategy_id=%s symbol=%s qty=%s reason=%s account_type=%s",
            order_id,
            strategy_id,
            symbol,
            qty_int,
            reason,
            self.account_type,
        )

        # ---------------------------------
        # Broker 주문
        # ---------------------------------

        ret = self.adapter.send_order(
            order,
            account_type=self.account_type,
        )

        # Kiwoom 성공 코드는 보통 0
        if ret != 0:
            logger.error(
                "ORDER_SEND_FAILED order_id=%s strategy_id=%s ret=%s account_type=%s",
                order_id,
                strategy_id,
                ret,
                self.account_type,
            )

            # fail-closed: 주문 전송 실패는 시스템 이상 신호로 간주
            try:
                self.risk_manager.block_trading(f"ORDER_SEND_FAILED:{ret}")
            except Exception:
                logger.exception(
                    "RISK_BLOCK_ON_SEND_FAIL_FAILED order_id=%s strategy_id=%s ret=%s",
                    order_id,
                    strategy_id,
                    ret,
                )

            return False

        # ---------------------------------
        # 주문 성공 → RiskManager에 알림 (optional)
        # ---------------------------------

        on_order_sent = getattr(self.risk_manager, "on_order_sent", None)
        if callable(on_order_sent):
            try:
                on_order_sent(order)
            except Exception:
                logger.exception(
                    "RISK_ON_ORDER_SENT_FAILED order_id=%s strategy_id=%s",
                    order_id,
                    strategy_id,
                )
                # 주문은 이미 나갔으므로 실패로 되돌리지 않음

        logger.info(
            "ORDER_SENT order_id=%s strategy_id=%s symbol=%s qty=%s account_type=%s",
            order_id,
            strategy_id,
            symbol,
            qty_int,
            self.account_type,
        )

        return True