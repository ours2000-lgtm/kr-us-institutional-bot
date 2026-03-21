from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

from risk_engine.v1_1.enums.applies_scope import AppliesScope
from risk_engine.v1_1.enums.snapshot_quality_grade import SnapshotQualityGrade
from risk_engine.v1_1.enums.system_health_grade import SystemHealthGrade


MODEL_VERSION: Literal["1.1"] = "1.1"
DecisionOutcome = Literal["ALLOW", "DENY", "UNKNOWN"]


class AccountRiskDecisionV1_1(BaseModel):
    """
    Canonical ACCOUNT-level risk decision object (v1.1)

    LOCK (Runtime Core Contract):
      - decision: "ALLOW" | "DENY" | "UNKNOWN"
      - fail_closed: bool
        (True if the decision results from a fail-closed safety mode, False otherwise.)
    """

    model_version: Literal["1.1"] = Field(default=MODEL_VERSION)

    # Scope / grades (domain signals)
    applies_scope: AppliesScope
    snapshot_quality_grade: SnapshotQualityGrade
    system_health_grade: SystemHealthGrade

    # Runtime core outcome (LOCK)
    decision: DecisionOutcome
    fail_closed: bool = False

    # Optional operational fields
    reset_policy: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    action: Optional[str] = None
    reason_code: Optional[str] = None

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
    )
