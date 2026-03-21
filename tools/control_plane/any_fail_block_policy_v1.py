# tools/control_plane/any_fail_block_policy_v1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tools.governance_validator.result_contract import (
    ChainValidationResult,
    ChainValidationStatus,
)


@dataclass(frozen=True)
class GateDecision:
    """
    Control Plane Gate output (minimal SSOT form)
    """
    allow: bool
    policy_ref: str
    reason: str
    # optional debug breadcrumbs
    errors_count: int = 0
    warnings_count: int = 0


POLICY_REF = "POLICY-GATE-ANYFAILBLOCK-v1"


def evaluate_any_fail_block_policy_v1(res: ChainValidationResult) -> GateDecision:
    """
    AnyFailBlockPolicy v1 (FAIL-CLOSED):
      - BLOCK if status != PASS
      - BLOCK if any errors exist
      - WARNINGS do not block (still ALLOW)
    """
    if not isinstance(res, ChainValidationResult):
        raise TypeError("res must be ChainValidationResult")

    errors_count = len(getattr(res, "errors", []) or [])
    warnings_count = len(getattr(res, "warnings", []) or [])

    if res.status != ChainValidationStatus.PASS:
        return GateDecision(
            allow=False,
            policy_ref=POLICY_REF,
            reason=f"BLOCK: status={res.status}",
            errors_count=errors_count,
            warnings_count=warnings_count,
        )

    if errors_count > 0:
        return GateDecision(
            allow=False,
            policy_ref=POLICY_REF,
            reason=f"BLOCK: errors_count={errors_count}",
            errors_count=errors_count,
            warnings_count=warnings_count,
        )

    return GateDecision(
        allow=True,
        policy_ref=POLICY_REF,
        reason="ALLOW: pass-without-errors",
        errors_count=errors_count,
        warnings_count=warnings_count,
    )