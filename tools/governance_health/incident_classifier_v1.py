# tools/governance_health/incident_classifier_v1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class IncidentClassificationResult:
    """
    Result of mapping Governance Health → Incident level.
    """
    incident_level: str   # NONE | P2 | P1 | P0
    health_status: str
    score: int
    rationale: str


class IncidentClassifierV1:
    """
    Minimal incident classification matrix v1.

    Mapping:

        Health GREEN  → NONE
        Health AMBER  → P2
        Health RED    → P0

    (P1 reserved for future intermediate escalation rules)
    """

    def classify(self, health_result: Any) -> IncidentClassificationResult:
        status = getattr(health_result, "status", None)
        score = getattr(health_result, "score", None)
        rationale = getattr(health_result, "rationale", "")

        if status == "GREEN":
            level = "NONE"
        elif status == "AMBER":
            level = "P2"
        elif status == "RED":
            level = "P0"
        else:
            # defensive fallback
            level = "P1"

        return IncidentClassificationResult(
            incident_level=level,
            health_status=status,
            score=int(score) if score is not None else -1,
            rationale=rationale,
        )