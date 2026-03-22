# path: broker/order_event_bridge.py

from __future__ import annotations

from logging import getLogger
from typing import Any, Dict, Optional

from engine.incident_manager import IncidentSeverity


logger = getLogger(__name__)


class OrderEventBridge:

    def __init__(self, order_lifecycle_manager, evidence_writer=None, incident_manager=None):
        if order_lifecycle_manager is None:
            raise ValueError("order_lifecycle_manager is required")

        self.order_lifecycle_manager = order_lifecycle_manager
        self.evidence_writer = evidence_writer
        self.incident_manager = incident_manager

    # =====================================================
    # ACK
    # =====================================================

    def handle_order_ack(
        self,
        intent_id: Optional[str],
        broker_order_id: str,
        reason: str = "broker_ack",
    ) -> bool:

        broker_order_id = str(broker_order_id or "").strip()
        resolved_intent_id = None if intent_id is None else str(intent_id).strip()

        if not broker_order_id:
            return False

        if not resolved_intent_id:
            resolved_intent_id = self._resolve_intent_id(broker_order_id)

        if not resolved_intent_id:
            logger.error("ACK_UNKNOWN_CONTEXT broker_order_id=%s", broker_order_id)

            self._write_evidence(
                "order_ack_unknown_context",
                {
                    "reason": "unknown_order_context",
                    "stage": "bridge",
                    "detail": "intent_not_found",
                    "broker_order_id": broker_order_id,
                },
            )

            # 🔥 incident
            if self.incident_manager:
                self.incident_manager.create_incident(
                    category="order_event_bridge",
                    reason="order_ack_unknown_context",
                    severity=IncidentSeverity.WARNING,
                    payload={
                        "broker_order_id": broker_order_id,
                    },
                )

            return False

        self.order_lifecycle_manager.mark_acked(
            intent_id=resolved_intent_id,
            broker_order_id=broker_order_id,
            reason=reason,
        )

        return True

    # =====================================================
    # UTIL
    # =====================================================

    def _resolve_intent_id(self, broker_order_id: str) -> Optional[str]:
        try:
            return self.order_lifecycle_manager.resolve_intent_id(
                broker_order_id
            )
        except Exception:
            logger.exception("RESOLVE_INTENT_ID_FAILED")
            return None

    def _write_evidence(self, event_type: str, payload: Dict[str, Any]):
        if self.evidence_writer is None:
            return

        try:
            self.evidence_writer.write_event(
                category="execution",
                component="order_event_bridge",
                event_type=event_type,
                payload=payload,
            )
        except Exception:
            logger.exception("EVIDENCE_WRITE_FAILED")