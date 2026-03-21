# path: core/engine/execution_controller.py

from datetime import datetime, timezone
from logging import getLogger

from core.execution.order_permission import evaluate_order_permission


logger = getLogger(__name__)


class ExecutionController:
    def __init__(
        self,
        adapter,
        order_factory,
        risk_manager,
        account_type="paper",
        recovery_state_supplier=None,
    ):
        self.adapter = adapter
        self.order_factory = order_factory
        self.risk_manager = risk_manager
        self.account_type = str(account_type).lower().strip()
        self.recovery_state_supplier = recovery_state_supplier

        # intent_id -> tracking info
        self.open_intents = {}

    def execute_signal(self, signal):
        logger.info(
            "EXECUTE_SIGNAL_START symbol=%s",
            getattr(signal, "symbol", None),
        )

        try:
            # ---------------------------------
            # 0) Dependency guard (fail-closed)
            # ---------------------------------
            if self.adapter is None:
                logger.error("EXECUTION_BLOCKED adapter is not configured")
                return False

            if self.risk_manager is None:
                logger.error("EXECUTION_BLOCKED risk_manager is not configured")
                return False

            if self.order_factory is None:
                logger.error("EXECUTION_BLOCKED order_factory is not configured")
                return False

            # ---------------------------------
            # 1) Order 생성
            # ---------------------------------
            order = self.order_factory.build_from_signal(signal)

            intent_id = getattr(order, "intent_id", None)
            if not intent_id:
                logger.error("EXECUTION_BLOCKED missing intent_id on order")
                return False

            symbol = str(getattr(order, "symbol", "")).strip()
            side = str(getattr(order, "side", "")).strip().upper()

            logger.info(
                "ORDER_BUILT intent=%s sym=%s side=%s qty=%s type=%s price=%s",
                intent_id,
                symbol,
                side,
                getattr(order, "qty", None),
                getattr(order, "order_type", None),
                getattr(order, "price", None),
            )

            if not symbol:
                logger.error("EXECUTION_BLOCKED intent=%s missing symbol", intent_id)
                return False

            if side not in {"BUY", "SELL"}:
                logger.error(
                    "EXECUTION_BLOCKED intent=%s invalid side=%s",
                    intent_id,
                    side,
                )
                return False

            # ---------------------------------
            # 2) Control-plane / FSM gate
            # 정책:
            # - READY 에서만 BUY 허용
            # - READY / EXIT_ONLY 에서만 SELL 주문 허용
            # - 나머지는 fail-closed 차단
            #
            # 우선순위:
            # 1) recovery_state_supplier (FSM SSOT 권장)
            # 2) adapter.recovery_state (legacy fallback)
            # ---------------------------------
            raw_state = self._get_runtime_control_state()
            control_state = self._normalize_control_state(raw_state)

            allowed, reason = evaluate_order_permission(control_state, side)

            if not allowed:
                logger.warning(
                    "ORDER_BLOCKED_BY_FSM intent=%s symbol=%s side=%s raw_state=%s control_state=%s reason=%s",
                    intent_id,
                    symbol,
                    side,
                    raw_state,
                    control_state,
                    reason,
                )
                return False

            logger.info(
                "ORDER_PERMISSION_ALLOWED intent=%s symbol=%s side=%s raw_state=%s control_state=%s",
                intent_id,
                symbol,
                side,
                raw_state,
                control_state,
            )

            # ---------------------------------
            # 3) 중복 주문 방지
            # 현재 단계: 같은 종목 + 같은 방향 차단
            # ---------------------------------
            existing_symbol_sides = {
                (info["symbol"], info["side"])
                for info in self.open_intents.values()
            }

            if (symbol, side) in existing_symbol_sides:
                logger.warning(
                    "DUPLICATE_ORDER_PREVENTED intent=%s symbol=%s side=%s",
                    intent_id,
                    symbol,
                    side,
                )
                return False

            # ---------------------------------
            # 4) Risk Gate
            # 반드시 RiskDecision 경로 사용
            # ---------------------------------
            decision = self.risk_manager.evaluate_decision(order)

            logger.info(
                "RISK_DECISION intent=%s allowed=%s decision=%s reasons=%s block_reason=%s current_qty=%s projected_qty=%s",
                intent_id,
                getattr(decision, "allowed", None),
                getattr(decision, "decision", None),
                getattr(decision, "reasons", None),
                getattr(decision, "block_reason", None),
                getattr(decision, "current_position_qty", None),
                getattr(decision, "projected_position_qty", None),
            )

            if not getattr(decision, "allowed", False):
                logger.warning(
                    "RISK_BLOCKED intent=%s decision=%s reasons=%s block_reason=%s",
                    intent_id,
                    getattr(decision, "decision", None),
                    getattr(decision, "reasons", None),
                    getattr(decision, "block_reason", None),
                )
                return False

            # ---------------------------------
            # 5) Broker 전송
            # ---------------------------------
            ret = self.adapter.send_order(
                order,
                account_type=self.account_type,
            )

            logger.info(
                "SEND_ORDER_RESULT intent=%s ret=%s account_type=%s raw_state=%s control_state=%s",
                intent_id,
                ret,
                self.account_type,
                raw_state,
                control_state,
            )

            if ret != 0:
                logger.error(
                    "SEND_FAILED intent=%s ret=%s",
                    intent_id,
                    ret,
                )

                try:
                    self.risk_manager.block_trading(f"SEND_FAILED:{ret}")
                except Exception:
                    logger.exception("RISK_BLOCK_ON_SEND_FAILED")

                self._notify_order_failed(order)
                return False

            # ---------------------------------
            # 6) 상태 추적 시작
            # ---------------------------------
            self._track_open_order(order, symbol, side, intent_id)

            # ---------------------------------
            # 7) Risk hook: order sent
            # ---------------------------------
            on_order_sent = getattr(self.risk_manager, "on_order_sent", None)
            if callable(on_order_sent):
                try:
                    on_order_sent(order)
                except Exception:
                    logger.exception(
                        "RISK_ON_ORDER_SENT_FAILED intent=%s",
                        intent_id,
                    )

            logger.info(
                "ORDER_SENT intent=%s broker_id=%s at=%s",
                intent_id,
                getattr(order, "broker_order_id", None),
                datetime.now(timezone.utc).isoformat(),
            )

            return True

        except Exception as exc:
            logger.error(
                "SIGNAL_EXECUTION_FAILED symbol=%s error=%s",
                getattr(signal, "symbol", None),
                exc,
                exc_info=True,
            )
            return False

    # ---------------------------------
    # tracking
    # ---------------------------------

    def _track_open_order(self, order, symbol, side, intent_id):
        self.open_intents[intent_id] = {
            "symbol": symbol,
            "side": side,
            "broker_order_id": getattr(order, "broker_order_id", None),
            "submitted_at": datetime.now(timezone.utc),
        }

    def bind_broker_order_id(self, intent_id, broker_order_id):
        info = self.open_intents.get(intent_id)

        if not info:
            return

        normalized_broker_order_id = str(broker_order_id).strip()
        if not normalized_broker_order_id:
            return

        info["broker_order_id"] = normalized_broker_order_id

        logger.debug(
            "BROKER_ORDER_ID_BOUND intent=%s broker_id=%s",
            intent_id,
            normalized_broker_order_id,
        )

    def mark_order_closed_by_intent(self, intent_id, symbol):
        info = self.open_intents.get(intent_id)

        if not info:
            return

        expected_symbol = str(info.get("symbol", "")).strip()
        actual_symbol = str(symbol).strip()

        if expected_symbol != actual_symbol:
            logger.warning(
                "ORDER_CLOSE_SYMBOL_MISMATCH intent=%s expected=%s actual=%s",
                intent_id,
                expected_symbol,
                actual_symbol,
            )
            return

        del self.open_intents[intent_id]

        logger.info(
            "ORDER_LIFECYCLE_CLOSED symbol=%s intent=%s",
            actual_symbol,
            intent_id,
        )

    def mark_order_closed_by_broker_order_id(self, broker_order_id, symbol):
        normalized_broker_order_id = str(broker_order_id).strip()
        actual_symbol = str(symbol).strip()

        if not normalized_broker_order_id:
            logger.warning(
                "ORDER_CLOSE_SKIPPED blank broker_order_id symbol=%s",
                actual_symbol,
            )
            return

        if not actual_symbol:
            logger.warning(
                "ORDER_CLOSE_SKIPPED blank symbol broker_order_id=%s",
                normalized_broker_order_id,
            )
            return

        matched_intent_id = None

        for intent_id, info in list(self.open_intents.items()):
            expected_symbol = str(info.get("symbol", "")).strip()
            tracked_broker_order_id = str(info.get("broker_order_id", "")).strip()

            if tracked_broker_order_id != normalized_broker_order_id:
                continue

            if expected_symbol != actual_symbol:
                logger.warning(
                    "ORDER_CLOSE_SYMBOL_MISMATCH_BY_BROKER_ID intent=%s broker_id=%s expected=%s actual=%s",
                    intent_id,
                    normalized_broker_order_id,
                    expected_symbol,
                    actual_symbol,
                )
                return

            matched_intent_id = intent_id
            break

        if matched_intent_id is None:
            logger.debug(
                "ORDER_CLOSE_BY_BROKER_ID_NO_MATCH broker_id=%s symbol=%s",
                normalized_broker_order_id,
                actual_symbol,
            )
            return

        del self.open_intents[matched_intent_id]

        logger.info(
            "ORDER_LIFECYCLE_CLOSED_BY_BROKER_ID symbol=%s intent=%s broker_id=%s",
            actual_symbol,
            matched_intent_id,
            normalized_broker_order_id,
        )

    # ---------------------------------
    # internals
    # ---------------------------------

    def _get_runtime_control_state(self):
        # 1) explicit supplier (FSM SSOT 권장)
        supplier = self.recovery_state_supplier
        if callable(supplier):
            try:
                state = supplier()
                if state is not None:
                    return str(state).strip().upper()
            except Exception:
                logger.exception("READ_RECOVERY_STATE_SUPPLIER_FAILED")

        # 2) legacy adapter fallback
        try:
            state = getattr(self.adapter, "recovery_state", None)
            if state is None:
                return None
            return str(state).strip().upper()
        except Exception:
            logger.exception("READ_ADAPTER_RECOVERY_STATE_FAILED")
            return None

    def _normalize_control_state(self, state):
        if state is None:
            return "UNKNOWN"
        return str(state).strip().upper()

    def _notify_order_failed(self, order):
        on_order_failed = getattr(self.risk_manager, "on_order_failed", None)
        if callable(on_order_failed):
            try:
                on_order_failed(order)
            except Exception:
                logger.exception("RISK_MANAGER_ON_ORDER_FAILED_HOOK_FAILED")