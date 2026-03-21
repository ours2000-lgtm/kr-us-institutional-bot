# risk_models_reset.py (or reset_policy.py)

from enum import Enum


class ResetPolicyType(str, Enum):
    """
    Reset policy for HARD_STOP recovery.

    Rules:
    - Enum name == serialized value
    - New types require Constitution + Enum change together
    """

    MANUAL_ONLY = "MANUAL_ONLY"
    NEXT_SESSION = "NEXT_SESSION"
    HEALTH_CHECK = "HEALTH_CHECK"

# risk_models_reset.py

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from risk_engine.v2.common.risk_constants import MODEL_VERSION
from risk_engine.v2.common.reset_policy_types import ResetPolicyType


class ResetPolicy(BaseModel):
    """
    Reset policy for HARD_STOP recovery.

    Constitution rules (V2.0.1):
    - Missing policy defaults to MANUAL_ONLY (fail-closed)
    - ResetPolicy itself does NOT decide whether reset is allowed
    - Enforcement is handled by AccountRiskDecision

    NOTE:
    - not_before is only meaningful for NEXT_SESSION / HEALTH_CHECK
    - For MANUAL_ONLY, not_before is ignored by higher-level logic
    - conditions are audit-only and never used for automated reset logic
    """

    type: ResetPolicyType = Field(
        default=ResetPolicyType.MANUAL_ONLY,
        description="Reset policy type (default: MANUAL_ONLY)",
    )

    not_before: datetime | None = Field(
        default=None,
        description="Earliest allowed reset time (informational)",
    )

    conditions: List[str] = Field(
        default_factory=list,
        description="Audit-only reset conditions (never auto-enforced)",
    )

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
    }

