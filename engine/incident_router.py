# path: engine/incident_router.py

from __future__ import annotations

from logging import getLogger
from typing import Optional

from engine.incident_manager import IncidentSeverity


logger = getLogger(__name__)


class IncidentRouter:
    """
    Incident → 시스템 반응 정책

    역할:
    - incident severity에 따라 시스템 반응 결정
    - risk_manager / recovery_fsm 연동

    정책:
    - WARNING: 기록만
    - CRITICAL: trading block + FSM BLOCKED
    """

    def __init__(
        self,
        risk_manager=None,
        recovery_fsm=None,
    ):
        self.risk_manager = risk_manager
        self.recovery_fsm = recovery_fsm

    # =====================================================
    # ENTRY
    # =====================================================

    def handle_incident(self, incident) -> None:
        severity = incident.severity
        reason = incident.reason
        incident_id = incident.incident_id

        logger.error(
            "INCIDENT_ROUTER_HANDLE incident_id=%s severity=%s reason=%s",
            incident_id,
            severity,
            reason,
        )

        if severity == IncidentSeverity.CRITICAL:
            self._handle_critical(incident)

        elif severity == IncidentSeverity.WARNING:
            self._handle_warning(incident)

        else:
            logger.info(
                "INCIDENT_ROUTER_INFO incident_id=%s reason=%s",
                incident_id,
                reason,
            )

    # =====================================================
    # HANDLERS
    # =====================================================

    def _handle_warning(self, incident):
        # 현재는 기록만 (확장 가능)
        logger.warning(
            "INCIDENT_WARNING incident_id=%s reason=%s",
            incident.incident_id,
            incident.reason,
        )

    def _handle_critical(self, incident):
        reason = f"INCIDENT_CRITICAL:{incident.reason}"

        # 1) risk block
        if self.risk_manager is not None:
            try:
                self.risk_manager.block_trading(reason)
            except Exception:
                logger.exception("INCIDENT_CRITICAL_RISK_BLOCK_FAILED")

        else:
            logger.warning("INCIDENT_CRITICAL_RISK_MANAGER_MISSING")

        # 2) FSM BLOCKED
        if self.recovery_fsm is not None:
            try:
                self.recovery_fsm.transition(
                    new_state="BLOCKED",
                    event="INCIDENT_CRITICAL",
                    reason=reason,
                )
            except Exception:
                logger.exception("INCIDENT_CRITICAL_FSM_TRANSITION_FAILED")

        else:
            logger.warning("INCIDENT_CRITICAL_FSM_MISSING")