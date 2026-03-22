# path: core/execution/order_watchdog.py

from __future__ import annotations

import time
from logging import getLogger
from typing import Any, Dict

from core.execution.order_lifecycle import OrderState
from engine.incident_manager import IncidentSeverity


logger = getLogger(__name__)


class OrderWatchdog:
    """
    ACK timeout 감지 및 incident escalation

    NOTE:
    - start()는 blocking loop (thread에서 실행해야 함)
    - SENT 상태만 timeout 대상
    """

    def __init__(
        self,
        lifecycle_manager,
        risk_manager=None,
        evidence_writer=None,
        incident_manager=None,
        ack_timeout_sec: int = 5,
        check_interval_sec: int = 1,
    ):
        if lifecycle_manager is None:
            raise ValueError("lifecycle_manager is required")

        self.lifecycle_manager = lifecycle_manager
        self.risk_manager = risk_manager
        self.evidence_writer = evidence_writer
        self.incident_manager = incident_manager

        self.ack_timeout_sec = int(ack_timeout_sec)
        self.check_interval_sec = int(check_interval_sec)

        if self.ack_timeout_sec <= 0:
            raise ValueError("ack_timeout_sec must be > 0")

        if self.check_interval_sec <= 0:
            raise ValueError("check_interval_sec must be > 0")

        self._running = False
        self._handled_ack_timeout_intents = set()

    # =====================================================
    # LOOP
    # =====================================================

    def start(self):
        self._running = True
        logger.info(
            "ORDER_WATCHDOG_STARTED ack_timeout=%s interval=%s",
            self.ack_timeout_sec,
            self.check_interval_sec,
        )

        while self._running:
            try:
                self._run_once()
            except Exception:
                logger.exception("ORDER_WATCHDOG_LOOP_ERROR")

            time.sleep(self.check_interval_sec)

    def stop(self):
        self._running = False
        logger.info("ORDER_WATCHDOG_STOPPED")

    # =====================================================
    # CORE
    # =====================================================

    def _run_once(self):
        records = self.lifecycle_manager.get_active_records()

        now = time.time()

        for rec in records:
            try:
                self._check_record(rec, now)
            except Exception:
                logger.exception("WATCHDOG_CHECK_FAILED intent_id=%s", rec.intent_id)

    def _check_record(self, rec, now: float):
        if rec.intent_id in self._handled_ack_timeout_intents:
            return

        state = rec.state

        # watchdog은 SENT만 본다
        if state != OrderState.SENT:
            return

        if rec.updated_at is None:
            return

        elapsed = now - rec.updated_at.timestamp()

        if elapsed < self.ack_timeout_sec:
            return

        self._handle_ack_timeout(rec, elapsed)

    # =====================================================
    # TIMEOUT
    # =====================================================

    def _handle_ack_timeout(self, rec, elapsed: float):
        intent_id = rec.intent_id
        broker_order_id = getattr(rec, "broker_order_id", None)

        logger.error(
            "ORDER_ACK_TIMEOUT intent_id=%s broker_order_id=%s elapsed=%.3f",
            intent_id,
            broker_order_id,
            elapsed,
        )

        # 반복 방지
        self._handled_ack_timeout_intents.add(intent_id)

        # 1) lifecycle 반영
        try:
            self.lifecycle_manager.mark_expired(
                intent_id=intent_id,
                broker_order_id=broker_order_id,
                reason="ack_timeout",
                metadata_update={"elapsed_sec": elapsed},
            )
        except Exception:
            logger.exception(
                "ORDER_ACK_TIMEOUT_MARK_EXPIRED_FAILED intent_id=%s",
                intent_id,
            )
            self._write_evidence(
                "order_ack_timeout_mark_expired_failed",
                {
                    "intent_id": intent_id,
                    "broker_order_id": broker_order_id,
                    "elapsed_sec": elapsed,
                },
            )

        # 2) evidence
        self._write_evidence(
            "order_ack_timeout",
            {
                "intent_id": intent_id,
                "broker_order_id": broker_order_id,
                "elapsed_sec": elapsed,
                "state": getattr(rec.state, "value", str(rec.state)),
                "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
            },
        )

        # 3) incident
        if self.incident_manager is not None:
            try:
                self.incident_manager.create_incident(
                    category="order_watchdog",
                    reason="order_ack_timeout",
                    severity=IncidentSeverity.CRITICAL,
                    payload={
                        "intent_id": intent_id,
                        "broker_order_id": broker_order_id,
                        "elapsed_sec": elapsed,
                    },
                )
            except Exception:
                logger.exception("ACK_TIMEOUT_INCIDENT_FAILED")

        # 4) escalation (risk block)
        self._escalate(rec)

    # =====================================================
    # ESCALATION
    # =====================================================

    def _escalate(self, rec):
        if self.risk_manager is not None:
            try:
                self.risk_manager.block_trading(
                    f"ORDER_ACK_TIMEOUT:{rec.intent_id}"
                )
            except Exception:
                logger.exception("WATCHDOG_ESCALATION_FAILED")
        else:
            logger.warning(
                "WATCHDOG_ESCALATION_SKIPPED risk_manager missing intent_id=%s",
                rec.intent_id,
            )

    # =====================================================
    # EVIDENCE
    # =====================================================

    def _write_evidence(self, event_type: str, payload: Dict[str, Any]):
        if self.evidence_writer is None:
            return

        try:
            self.evidence_writer.write_event(
                category="execution",
                component="order_watchdog",
                event_type=event_type,
                payload=payload,
            )
        except Exception:
            logger.exception("WATCHDOG_EVIDENCE_WRITE_FAILED")