# path: core/execution/execution_controller.py

from __future__ import annotations

from logging import getLogger
from typing import Any, Dict, Optional
from uuid import uuid4

from core.control_plane.runtime_state_policy import RUNTIME_STATE_POLICY
from core.execution.order_lifecycle import OrderState


logger = getLogger(__name__)


class ExecutionController:
    """
    NOTE:
    REJECTED is used as an operational reject state.
    The reject cause is captured with:
    - reason: top-level classification
    - stage: where it happened
    - detail: fine-grained cause
    """

    def __init__(
        self,
        adapter,
        order_factory,
        risk_manager,
        account_type="paper",
        recovery_state_supplier=None,
        evidence_writer=None,
        order_lifecycle_manager=None,
        cooldown_manager=None,
    ):
        self.adapter = adapter
        self.order_factory = order_factory
        self.risk_manager = risk_manager
        self.account_type = str(account_type).strip().lower()
        self.recovery_state_supplier = recovery_state_supplier
        self.evidence_writer = evidence_writer
        self.order_lifecycle_manager = order_lifecycle_manager
        self.cooldown_manager = cooldown_manager

        if recovery_state_supplier is not None and not callable(recovery_state_supplier):
            raise ValueError("recovery_state_supplier must be callable")

        if callable(self.recovery_state_supplier):
            logger.info("EXECUTION_CONTROLLER_RECOVERY_STATE_SUPPLIER_ATTACHED")
            try:
                raw = self.recovery_state_supplier()
                norm = self._normalize_control_state(raw)
                logger.info("RECOVERY_STATE_INITIAL raw=%r normalized=%s", raw, norm)
            except Exception:
                logger.exception("RECOVERY_STATE_INITIAL_READ_FAILED")
        else:
            logger.warning("EXECUTION_CONTROLLER_RECOVERY_STATE_SUPPLIER_MISSING")

        if self.evidence_writer is not None:
            logger.info("EXECUTION_CONTROLLER_EVIDENCE_WRITER_ATTACHED")

        if self.order_lifecycle_manager is not None:
            logger.info("EXECUTION_CONTROLLER_ORDER_LIFECYCLE_ATTACHED")

        if self.cooldown_manager is not None:
            logger.info("EXECUTION_CONTROLLER_COOLDOWN_MANAGER_ATTACHED")

        logger.info(
            "EXECUTION_COMPONENTS_READY adapter=%s order_factory=%s risk_manager=%s supplier=%s evidence=%s lifecycle=%s cooldown=%s account_type=%s",
            "ok" if adapter is not None else "none",
            "ok" if order_factory is not None else "none",
            "ok" if risk_manager is not None else "none",
            "ok" if callable(recovery_state_supplier) else "none",
            "ok" if evidence_writer is not None else "none",
            "ok" if order_lifecycle_manager is not None else "none",
            "ok" if cooldown_manager is not None else "none",
            self.account_type,
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def execute_signal(self, signal) -> bool:
        try:
            return self._execute_signal_inner(signal)
        except Exception as exc:
            logger.exception("EXECUTE_SIGNAL_UNHANDLED_ERROR")
            self._write_execution_evidence(
                event_type="execution_controller_unhandled_error",
                symbol="",
                side="",
                reason="controller_error",
                stage="controller",
                detail="unhandled_exception",
                payload={
                    "intent_id": None,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            return False

    def bind_broker_order_id(self, intent_id: str, broker_order_id: str) -> bool:
        normalized_intent_id = None if intent_id is None else str(intent_id).strip()
        normalized_broker_order_id = (
            None if broker_order_id is None else str(broker_order_id).strip()
        )

        if not normalized_intent_id:
            logger.error("BIND_BROKER_ORDER_ID_FAILED missing intent_id")
            self._write_execution_evidence(
                event_type="order_bind_broker_id_failed",
                symbol="",
                side="",
                reason="controller_error",
                stage="lifecycle",
                detail="missing_intent_id",
                payload={
                    "intent_id": normalized_intent_id,
                    "broker_order_id": normalized_broker_order_id,
                },
            )
            return False

        if not normalized_broker_order_id:
            logger.error(
                "BIND_BROKER_ORDER_ID_FAILED missing broker_order_id intent_id=%s",
                normalized_intent_id,
            )
            self._write_execution_evidence(
                event_type="order_bind_broker_id_failed",
                symbol="",
                side="",
                reason="controller_error",
                stage="lifecycle",
                detail="missing_broker_order_id",
                payload={
                    "intent_id": normalized_intent_id,
                    "broker_order_id": normalized_broker_order_id,
                },
            )
            return False

        if self.order_lifecycle_manager is None:
            logger.info(
                "BIND_BROKER_ORDER_ID_SKIPPED lifecycle_manager missing intent_id=%s broker_order_id=%s",
                normalized_intent_id,
                normalized_broker_order_id,
            )
            return True

        try:
            self.order_lifecycle_manager.bind_broker_order_id(
                intent_id=normalized_intent_id,
                broker_order_id=normalized_broker_order_id,
            )
            logger.info(
                "BIND_BROKER_ORDER_ID_APPLIED intent_id=%s broker_order_id=%s",
                normalized_intent_id,
                normalized_broker_order_id,
            )
            self._write_execution_evidence(
                event_type="order_bind_broker_id_applied",
                symbol="",
                side="",
                reason="bind_applied",
                stage="lifecycle",
                detail="bind_broker_order_id",
                payload={
                    "intent_id": normalized_intent_id,
                    "broker_order_id": normalized_broker_order_id,
                },
            )
            return True
        except Exception as exc:
            logger.exception(
                "BIND_BROKER_ORDER_ID_FAILED intent_id=%s broker_order_id=%s",
                normalized_intent_id,
                normalized_broker_order_id,
            )
            self._write_execution_evidence(
                event_type="order_bind_broker_id_failed",
                symbol="",
                side="",
                reason="controller_error",
                stage="lifecycle",
                detail="bind_failed",
                payload={
                    "intent_id": normalized_intent_id,
                    "broker_order_id": normalized_broker_order_id,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            return False

    def mark_order_closed_by_broker_order_id(
        self,
        broker_order_id: str,
        symbol: str = "",
    ) -> bool:
        normalized_broker_order_id = (
            None if broker_order_id is None else str(broker_order_id).strip()
        )
        normalized_symbol = str(symbol or "").strip()

        if not normalized_broker_order_id:
            logger.error("ORDER_CLOSE_FAILED missing broker_order_id")
            self._write_execution_evidence(
                event_type="order_close_failed",
                symbol=normalized_symbol,
                side="",
                reason="controller_error",
                stage="lifecycle",
                detail="missing_broker_order_id",
                payload={
                    "broker_order_id": normalized_broker_order_id,
                },
            )
            return False

        if self.order_lifecycle_manager is None:
            logger.info(
                "ORDER_CLOSE_SKIPPED lifecycle_manager missing broker_order_id=%s",
                normalized_broker_order_id,
            )
            return True

        try:
            record = self.order_lifecycle_manager.get_record_by_broker_order_id(
                normalized_broker_order_id
            )
            if record is None:
                logger.warning(
                    "ORDER_CLOSE_UNKNOWN_CONTEXT broker_order_id=%s symbol=%s",
                    normalized_broker_order_id,
                    normalized_symbol,
                )
                self._write_execution_evidence(
                    event_type="order_close_unknown_context",
                    symbol=normalized_symbol,
                    side="",
                    reason="controller_error",
                    stage="lifecycle",
                    detail="unknown_broker_order_id",
                    payload={
                        "broker_order_id": normalized_broker_order_id,
                    },
                )
                return False

            if record.state == OrderState.FILLED:
                logger.info(
                    "ORDER_ALREADY_CLOSED broker_order_id=%s intent_id=%s",
                    normalized_broker_order_id,
                    record.intent_id,
                )
                return True

            filled_qty = int(record.qty)

            self.order_lifecycle_manager.mark_filled(
                intent_id=record.intent_id,
                broker_order_id=normalized_broker_order_id,
                filled_qty=filled_qty,
                reason="broker_order_closed",
                metadata_update={
                    "symbol": normalized_symbol,
                },
            )

            logger.info(
                "ORDER_CLOSE_APPLIED broker_order_id=%s intent_id=%s symbol=%s",
                normalized_broker_order_id,
                record.intent_id,
                normalized_symbol,
            )
            self._write_execution_evidence(
                event_type="order_close_applied",
                symbol=normalized_symbol or str(record.symbol).strip(),
                side=str(record.side).strip().upper(),
                reason="broker_rejected",
                stage="broker",
                detail="broker_order_closed",
                payload={
                    "intent_id": record.intent_id,
                    "broker_order_id": normalized_broker_order_id,
                },
            )
            return True

        except Exception as exc:
            logger.exception(
                "ORDER_CLOSE_FAILED broker_order_id=%s symbol=%s",
                normalized_broker_order_id,
                normalized_symbol,
            )
            self._write_execution_evidence(
                event_type="order_close_failed",
                symbol=normalized_symbol,
                side="",
                reason="controller_error",
                stage="lifecycle",
                detail="close_failed",
                payload={
                    "broker_order_id": normalized_broker_order_id,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            return False

    def register_symbol_exit_cooldown(self, symbol: str, exit_reason: str) -> None:
        if self.cooldown_manager is None:
            return

        try:
            self.cooldown_manager.register_exit(
                symbol=symbol,
                reason=exit_reason,
            )
            logger.info(
                "SYMBOL_EXIT_COOLDOWN_REGISTERED symbol=%s reason=%s",
                symbol,
                exit_reason,
            )
        except Exception:
            logger.exception(
                "SYMBOL_EXIT_COOLDOWN_REGISTER_FAILED symbol=%s reason=%s",
                symbol,
                exit_reason,
            )

    # =====================================================
    # MAIN
    # =====================================================

    def _execute_signal_inner(self, signal) -> bool:
        if self.adapter is None:
            logger.error("EXECUTION_BLOCKED adapter missing")
            self._write_execution_evidence(
                event_type="execution_dependency_missing",
                symbol="",
                side="",
                reason="controller_error",
                stage="validation",
                detail="adapter_missing",
                payload={"intent_id": None},
            )
            return False

        if self.order_factory is None:
            logger.error("EXECUTION_BLOCKED order_factory missing")
            self._write_execution_evidence(
                event_type="execution_dependency_missing",
                symbol="",
                side="",
                reason="controller_error",
                stage="validation",
                detail="order_factory_missing",
                payload={"intent_id": None},
            )
            return False

        if self.risk_manager is None:
            logger.error("EXECUTION_BLOCKED risk_manager missing")
            self._write_execution_evidence(
                event_type="execution_dependency_missing",
                symbol="",
                side="",
                reason="controller_error",
                stage="validation",
                detail="risk_manager_missing",
                payload={"intent_id": None},
            )
            return False

        order = self._build_order_from_signal(signal)

        validation_error = self._validate_order_basic(order)
        if validation_error:
            logger.error("ORDER_INVALID %s", validation_error)
            self._write_execution_evidence(
                event_type="order_invalid",
                symbol=str(getattr(order, "symbol", "")).strip(),
                side=str(getattr(order, "side", "")).strip().upper(),
                reason="invalid_order",
                stage="validation",
                detail=validation_error,
                payload={"intent_id": None},
            )
            return False

        symbol = str(getattr(order, "symbol", "")).strip()
        side = str(getattr(order, "side", "")).strip().upper()

        intent_id = self._build_intent_id(signal, order)

        # -------------------------------------------------
        # cooldown gate
        # -------------------------------------------------
        if not self._is_symbol_allowed_by_cooldown(symbol):
            logger.warning(
                "ORDER_BLOCKED_BY_COOLDOWN symbol=%s side=%s intent_id=%s",
                symbol,
                side,
                intent_id,
            )
            self._write_execution_evidence(
                event_type="order_blocked_cooldown",
                symbol=symbol,
                side=side,
                reason="runtime_policy_blocked",
                stage="cooldown",
                detail="symbol_cooldown_active",
                payload={
                    "intent_id": intent_id,
                },
            )
            return False

        if not self._register_order_intent(intent_id, signal, order):
            logger.error("ORDER_INTENT_REGISTER_FAILED_FAIL_CLOSED intent_id=%s", intent_id)
            self._write_execution_evidence(
                event_type="order_lifecycle_register_failed",
                symbol=symbol,
                side=side,
                reason="controller_error",
                stage="lifecycle",
                detail="lifecycle_register_failed",
                payload={"intent_id": intent_id},
            )
            return False

        raw_state = self._get_runtime_control_state()
        if raw_state is None:
            return self._fail_closed(
                intent_id=intent_id,
                order=order,
                reason="runtime_policy_blocked",
                stage="runtime_policy",
                detail="control_state_unavailable",
            )

        control_state = self._normalize_control_state(raw_state)
        if control_state == "UNKNOWN":
            return self._fail_closed(
                intent_id=intent_id,
                order=order,
                reason="runtime_policy_blocked",
                stage="runtime_policy",
                detail="control_state_unknown",
                extra={"raw_state": repr(raw_state)},
            )

        permission = self._evaluate_runtime_gate(order, control_state)
        if not permission["allowed"]:
            return self._block(
                intent_id=intent_id,
                order=order,
                reason="runtime_policy_blocked",
                stage="runtime_policy",
                detail=permission["detail"],
                extra={"control_state": control_state},
            )

        if self._has_active_duplicate(order, intent_id=intent_id):
            return self._block(
                intent_id=intent_id,
                order=order,
                reason="duplicate_blocked",
                stage="duplicate",
                detail="duplicate_active_order",
                extra={"control_state": control_state},
            )

        risk = self._evaluate_risk(order)
        if not getattr(risk, "allowed", False):
            return self._block(
                intent_id=intent_id,
                order=order,
                reason="risk_blocked",
                stage="risk",
                detail=getattr(risk, "block_reason", None) or "risk_blocked",
                extra={"control_state": control_state},
            )

        try:
            result = self._send_order(order)
        except Exception as exc:
            logger.exception("ORDER_SEND_EXCEPTION intent_id=%s", intent_id)
            self._lifecycle_reject(
                intent_id=intent_id,
                reason="send_exception",
                metadata_update={
                    "stage": "send",
                    "detail": "send_exception",
                },
            )
            self._notify_risk_order_failed(order)
            self._write_execution_evidence(
                event_type="order_send_failed",
                symbol=symbol,
                side=side,
                reason="send_exception",
                stage="send",
                detail="send_exception",
                payload={
                    "intent_id": intent_id,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "control_state": control_state,
                },
            )
            return False

        if not self._is_send_success(result):
            logger.error(
                "ORDER_SEND_FAILED_RESULT intent_id=%s result=%r",
                intent_id,
                result,
            )
            self._lifecycle_reject(
                intent_id=intent_id,
                reason="send_failed",
                metadata_update={
                    "stage": "send",
                    "detail": "send_failed",
                },
            )
            self._notify_risk_order_failed(order)
            self._write_execution_evidence(
                event_type="order_send_failed",
                symbol=symbol,
                side=side,
                reason="send_failed",
                stage="send",
                detail="send_failed",
                payload={
                    "intent_id": intent_id,
                    "result": repr(result),
                    "control_state": control_state,
                },
            )
            return False

        broker_order_id = self._extract_broker_order_id(result)

        mark_sent_ok = self._mark_sent(
            intent_id=intent_id,
            broker_order_id=broker_order_id,
            symbol=symbol,
            side=side,
            metadata_update={
                "control_state": control_state,
                "send_result": repr(result),
            },
        )

        if not mark_sent_ok:
            logger.error(
                "ORDER_LIFECYCLE_TRACKING_DEGRADED intent_id=%s broker_order_id=%s",
                intent_id,
                broker_order_id,
            )

        self._notify_risk_order_sent(order)

        logger.info(
            "ORDER_SEND_SUCCESS intent_id=%s symbol=%s side=%s broker_order_id=%s result=%r",
            intent_id,
            symbol,
            side,
            broker_order_id,
            result,
        )

        self._write_execution_evidence(
            event_type="order_sent",
            symbol=symbol,
            side=side,
            reason="send_success",
            stage="send",
            detail="send_success",
            payload={
                "intent_id": intent_id,
                "broker_order_id": broker_order_id,
                "control_state": control_state,
                "lifecycle_mark_sent_ok": mark_sent_ok,
                "send_result": repr(result),
            },
        )

        return True

    # =====================================================
    # GATE / POLICY
    # =====================================================

    def _evaluate_runtime_gate(self, order, control_state: str) -> Dict[str, Any]:
        policy = RUNTIME_STATE_POLICY.get(control_state)

        if policy is None:
            return {
                "allowed": False,
                "detail": f"unknown_state:{control_state}",
            }

        side = str(getattr(order, "side", "")).strip().upper()

        if side == "BUY":
            if not getattr(policy, "buy_order_allowed", False):
                return {
                    "allowed": False,
                    "detail": f"buy_blocked:{control_state}",
                }
            return {"allowed": True, "detail": "ok"}

        if side == "SELL":
            if not getattr(policy, "sell_order_allowed", False):
                return {
                    "allowed": False,
                    "detail": f"sell_blocked:{control_state}",
                }
            return {"allowed": True, "detail": "ok"}

        return {
            "allowed": False,
            "detail": f"invalid_side:{side}",
        }

    # =====================================================
    # FAIL / BLOCK
    # =====================================================

    def _fail_closed(
        self,
        intent_id,
        order,
        reason,
        stage,
        detail,
        extra=None,
    ) -> bool:
        symbol = str(getattr(order, "symbol", "")).strip()
        side = str(getattr(order, "side", "")).strip().upper()

        logger.error(
            "FAIL_CLOSED intent_id=%s reason=%s stage=%s detail=%s",
            intent_id,
            reason,
            stage,
            detail,
        )

        self._lifecycle_reject(
            intent_id=intent_id,
            reason=reason,
            metadata_update={
                "stage": stage,
                "detail": detail,
            },
        )

        self._write_execution_evidence(
            event_type="order_blocked",
            symbol=symbol,
            side=side,
            reason=reason,
            stage=stage,
            detail=detail,
            payload={"intent_id": intent_id, **(extra or {})},
        )
        return False

    def _block(
        self,
        intent_id,
        order,
        reason,
        stage,
        detail,
        extra=None,
    ) -> bool:
        symbol = str(getattr(order, "symbol", "")).strip()
        side = str(getattr(order, "side", "")).strip().upper()

        logger.warning(
            "ORDER_BLOCKED intent_id=%s stage=%s reason=%s detail=%s symbol=%s side=%s",
            intent_id,
            stage,
            reason,
            detail,
            symbol,
            side,
        )

        self._lifecycle_reject(
            intent_id=intent_id,
            reason=reason,
            metadata_update={
                "stage": stage,
                "detail": detail,
            },
        )

        self._write_execution_evidence(
            event_type=f"order_blocked_{stage}",
            symbol=symbol,
            side=side,
            reason=reason,
            stage=stage,
            detail=detail,
            payload={"intent_id": intent_id, **(extra or {})},
        )
        return False

    # =====================================================
    # LIFECYCLE
    # =====================================================

    def _register_order_intent(self, intent_id, signal, order) -> bool:
        if self.order_lifecycle_manager is None:
            return True

        try:
            metadata = {
                "strategy_name": getattr(signal, "strategy_name", None),
                "signal_type": getattr(signal, "signal_type", None),
                "account_type": self.account_type,
            }
            self.order_lifecycle_manager.register_new_intent(
                intent_id=intent_id,
                symbol=str(getattr(order, "symbol", "")).strip(),
                side=str(getattr(order, "side", "")).strip().upper(),
                qty=int(getattr(order, "qty", 0)),
                metadata=metadata,
            )
            return True
        except Exception:
            logger.exception("LIFECYCLE_REGISTER_FAILED intent_id=%s", intent_id)
            return False

    def _mark_sent(
        self,
        intent_id,
        broker_order_id,
        symbol: str,
        side: str,
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if self.order_lifecycle_manager is None:
            return True

        try:
            self.order_lifecycle_manager.mark_sent(
                intent_id=intent_id,
                broker_order_id=broker_order_id,
                metadata_update=metadata_update,
            )
            return True
        except Exception:
            logger.exception(
                "MARK_SENT_FAILED intent_id=%s broker_order_id=%s",
                intent_id,
                broker_order_id,
            )
            self._write_execution_evidence(
                event_type="order_lifecycle_mark_sent_failed",
                symbol=symbol,
                side=side,
                reason="controller_error",
                stage="lifecycle",
                detail="mark_sent_failed",
                payload={
                    "intent_id": intent_id,
                    "broker_order_id": broker_order_id,
                    "metadata_update": repr(metadata_update),
                },
            )
            return False

    def _lifecycle_reject(self, intent_id, reason, metadata_update=None) -> None:
        """
        pre-send / local blocked orders are downgraded to REJECTED here.
        post-send state transitions must be handled by broker ACK/fill/reject events.
        """
        if self.order_lifecycle_manager is None:
            return

        try:
            rec = self.order_lifecycle_manager.get_record(intent_id)
            if rec and rec.state == OrderState.NEW:
                self.order_lifecycle_manager.mark_rejected(
                    intent_id=intent_id,
                    reason=reason,
                    metadata_update=metadata_update,
                )
        except Exception:
            logger.exception(
                "MARK_REJECT_FAILED intent_id=%s reason=%s",
                intent_id,
                reason,
            )

    # =====================================================
    # RISK HOOKS
    # =====================================================

    def _evaluate_risk(self, order):
        evaluate = getattr(self.risk_manager, "evaluate", None)
        if callable(evaluate):
            return evaluate(order)

        evaluate_decision = getattr(self.risk_manager, "evaluate_decision", None)
        if callable(evaluate_decision):
            return evaluate_decision(order)

        self._write_execution_evidence(
            event_type="risk_manager_contract_error",
            symbol=str(getattr(order, "symbol", "")).strip(),
            side=str(getattr(order, "side", "")).strip().upper(),
            reason="controller_error",
            stage="risk",
            detail="risk_manager_missing_evaluate_method",
            payload={
                "intent_id": None,
                "account_type": self.account_type,
            },
        )
        raise AttributeError(
            "risk_manager must provide evaluate(order) or evaluate_decision(order)"
        )

    def _notify_risk_order_failed(self, order) -> None:
        on_order_failed = getattr(self.risk_manager, "on_order_failed", None)
        if callable(on_order_failed):
            try:
                on_order_failed(order)
            except Exception:
                logger.exception("RISK_MANAGER_ON_ORDER_FAILED_ERROR")

    def _notify_risk_order_sent(self, order) -> None:
        on_order_sent = getattr(self.risk_manager, "on_order_sent", None)
        if callable(on_order_sent):
            try:
                on_order_sent(order)
            except Exception:
                logger.exception("RISK_MANAGER_ON_ORDER_SENT_ERROR")

    # =====================================================
    # ORDER FACTORY
    # =====================================================

    def _build_order_from_signal(self, signal):
        create_order = getattr(self.order_factory, "create_order", None)
        if callable(create_order):
            return create_order(signal)

        build_from_signal = getattr(self.order_factory, "build_from_signal", None)
        if callable(build_from_signal):
            return build_from_signal(signal)

        self._write_execution_evidence(
            event_type="order_factory_contract_error",
            symbol="",
            side="",
            reason="controller_error",
            stage="validation",
            detail="order_factory_missing_build_method",
            payload={
                "intent_id": None,
                "account_type": self.account_type,
            },
        )
        raise AttributeError(
            "order_factory must provide create_order(signal) or build_from_signal(signal)"
        )

    # =====================================================
    # ADAPTER
    # =====================================================

    def _send_order(self, order):
        try:
            return self.adapter.send_order(order, account_type=self.account_type)
        except TypeError:
            logger.warning(
                "SEND_ORDER_ACCOUNT_TYPE_FALLBACK adapter=%s account_type=%s",
                type(self.adapter).__name__,
                self.account_type,
            )
            return self.adapter.send_order(order)

    # =====================================================
    # UTIL
    # =====================================================

    def _validate_order_basic(self, order):
        symbol = str(getattr(order, "symbol", "")).strip()
        side = str(getattr(order, "side", "")).strip().upper()

        try:
            qty = int(getattr(order, "qty", 0))
        except (TypeError, ValueError):
            return "invalid_qty"

        if not symbol:
            return "invalid_symbol"

        if side not in ("BUY", "SELL"):
            return f"invalid_side:{side}"

        if qty <= 0:
            return f"invalid_qty:{qty}"

        return None

    def _has_active_duplicate(self, order, intent_id=None) -> bool:
        if self.order_lifecycle_manager is None:
            return False

        try:
            return self.order_lifecycle_manager.has_active_order_for_symbol_side(
                str(getattr(order, "symbol", "")).strip(),
                str(getattr(order, "side", "")).strip().upper(),
                exclude_intent_id=intent_id,
            )
        except Exception:
            logger.exception("DUP_CHECK_FAILED")
            return True

    def _is_symbol_allowed_by_cooldown(self, symbol: str) -> bool:
        if self.cooldown_manager is None:
            return True

        try:
            return bool(self.cooldown_manager.is_allowed(symbol))
        except Exception:
            logger.exception("COOLDOWN_CHECK_FAILED symbol=%s", symbol)
            return False  # fail-closed

    def _get_runtime_control_state(self):
        if self.recovery_state_supplier is None:
            logger.error("CONTROL_STATE_SUPPLIER_MISSING_FAIL_CLOSED")
            return None

        try:
            return self.recovery_state_supplier()
        except Exception:
            logger.exception("CONTROL_STATE_READ_ERROR_FAIL_CLOSED")
            return None

    def _normalize_control_state(self, state):
        if state is None:
            return "UNKNOWN"
        return str(state).strip().upper()

    def _is_send_success(self, result) -> bool:
        if result is None:
            return False

        if isinstance(result, int):
            return result == 0

        if isinstance(result, dict):
            if "ret" in result:
                return result.get("ret") == 0
            if "success" in result:
                return bool(result.get("success"))
            if "ok" in result:
                return bool(result.get("ok"))
            return True

        return True

    def _extract_broker_order_id(self, result):
        if result is None:
            return None

        if isinstance(result, dict):
            for key in (
                "broker_order_id",
                "order_id",
                "order_no",
                "org_order_no",
            ):
                value = result.get(key)
                if value is not None and str(value).strip():
                    return str(value).strip()

        for attr in ("broker_order_id", "order_id", "order_no", "org_order_no"):
            value = getattr(result, attr, None)
            if value is not None and str(value).strip():
                return str(value).strip()

        return None

    def _build_intent_id(self, signal, order):
        symbol = str(getattr(order, "symbol", "")).strip()
        side = str(getattr(order, "side", "")).strip().upper()
        signal_type = str(getattr(signal, "signal_type", "signal")).strip().lower()
        return f"{symbol}:{side}:{signal_type}:{uuid4().hex[:8]}"

    # =====================================================
    # EVIDENCE
    # =====================================================

    def _write_execution_evidence(
        self,
        event_type,
        symbol,
        side,
        reason,
        stage,
        detail,
        payload=None,
    ) -> None:
        if self.evidence_writer is None:
            return

        try:
            self.evidence_writer.write_event(
                category="execution",
                component="execution_controller",
                event_type=event_type,
                payload={
                    "symbol": symbol,
                    "side": side,
                    "reason": reason,
                    "stage": stage,
                    "detail": detail,
                    **(payload or {}),
                },
            )
        except Exception:
            logger.exception(
                "EVIDENCE_WRITE_FAILED event_type=%s symbol=%s side=%s reason=%s stage=%s detail=%s",
                event_type,
                symbol,
                side,
                reason,
                stage,
                detail,
            )