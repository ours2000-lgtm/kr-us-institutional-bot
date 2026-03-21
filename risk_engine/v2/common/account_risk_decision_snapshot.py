# ============================================================
# AccountRiskDecisionSnapshot (CANONICAL SNAPSHOT)
# Constitution Appendix Version: v1.0
#
# Immutable snapshot capturing the evidence used at the moment
# an AccountRiskDecision was made.
#
# This snapshot MUST be reproducible and auditable.
# Runtime state MUST NOT be embedded directly.
# ============================================================

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from pydantic import BaseModel, Field

from risk_engine.v2.common.snapshot_grades import (
    SnapshotQualityGrade,
    SystemHealthGrade,
)


class AccountRiskDecisionSnapshot(BaseModel):
    """
    Canonical snapshot of evidence at decision time.

    Responsibilities:
    - Capture minimal, deterministic evidence
    - Be immutable and replayable
    - Serve as audit / debug / ML ground truth

    IMPORTANT:
    - This snapshot is NOT runtime state.
    - It represents a frozen view at decision time.
    """

    # ------------------------------------------------------------------
    # Identity & time
    # ------------------------------------------------------------------
    snapshot_id: str = Field(
        ...,
        min_length=1,
        description="Globally unique snapshot identifier",
    )

    created_at: datetime = Field(
        ...,
        description="UTC timestamp when snapshot was created",
    )

    # ------------------------------------------------------------------
    # Canonical grades (fail-closed anchors)
    # ------------------------------------------------------------------
    snapshot_quality: SnapshotQualityGrade = Field(
        ...,
        description="Quality grade of the snapshot evidence",
    )

    system_health: SystemHealthGrade = Field(
        ...,
        description="Overall system health grade at decision time",
    )

    # ------------------------------------------------------------------
    # Minimal structured evidence (summarized)
    # ------------------------------------------------------------------
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Minimal structured evidence used for the decision. "
            "Must be deterministic and audit-safe."
        ),
    )

    # ------------------------------------------------------------------
    # Pydantic configuration (FAIL-CLOSED)
    # ------------------------------------------------------------------
    model_config = {
        "extra": "forbid",
        "strict": True,
        "arbitrary_types_allowed": False,
        "frozen": True,  # Snapshot MUST be immutable
    }
