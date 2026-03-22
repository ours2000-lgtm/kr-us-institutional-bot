# path: engine/incident_manager.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from logging import getLogger
from threading import RLock
from typing import Any, Dict, List, Optional


logger = getLogger(__name__)


class IncidentSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class IncidentRecord:
    incident_id: str
    category: str
    reason: str
    severity: IncidentSeverity
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = field(default_factory=dict)


class IncidentManager:
    """
    운영 incident manager

    역할:
    - 이상 이벤트를 구조화 기록
    - evidence writer 연동
    - 최근 incident 조회

    NOTE:
    초기 버전은 in-memory 저장 기반.
    """

    def __init__(self, evidence_writer=None):
        self.evidence_writer = evidence_writer
        self._lock = RLock()
        self._incidents: List[IncidentRecord] = []
        self._counter = 0

    def create_incident(
        self,
        category: str,
        reason: str,
        severity: IncidentSeverity,
        payload: Optional[Dict[str, Any]] = None,
    ) -> IncidentRecord:
        normalized_category = str(category).strip()
        normalized_reason = str(reason).strip()

        if not normalized_category:
            raise ValueError("category is required")

        if not normalized_reason:
            raise ValueError("reason is required")

        with self._lock:
            self._counter += 1
            incident_id = f"INC-{self._counter:06d}"

            rec = IncidentRecord(
                incident_id=incident_id,
                category=normalized_category,
                reason=normalized_reason,
                severity=severity,
                payload=dict(payload or {}),
            )
            self._incidents.append(rec)

        logger.error(
            "INCIDENT_CREATED incident_id=%s category=%s reason=%s severity=%s",
            rec.incident_id,
            rec.category,
            rec.reason,
            rec.severity.value,
        )

        self._write_evidence(rec)
        return rec

    def list_recent(self, limit: int = 20) -> List[IncidentRecord]:
        with self._lock:
            return list(self._incidents[-max(1, int(limit)):])

    def _write_evidence(self, rec: IncidentRecord) -> None:
        if self.evidence_writer is None:
            return

        try:
            self.evidence_writer.write_event(
                category="incident",
                component="incident_manager",
                event_type="incident_created",
                payload={
                    "incident_id": rec.incident_id,
                    "category": rec.category,
                    "reason": rec.reason,
                    "severity": rec.severity.value,
                    "created_at": rec.created_at.isoformat(),
                    **rec.payload,
                },
            )
        except Exception:
            logger.exception(
                "INCIDENT_EVIDENCE_WRITE_FAILED incident_id=%s",
                rec.incident_id,
            )