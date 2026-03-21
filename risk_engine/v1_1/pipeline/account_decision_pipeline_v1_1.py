from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

from risk_engine.v1_1.decision.account_risk_decision_v1_1 import AccountRiskDecisionV1_1
from risk_engine.v1_1.validation.outcome import ValidationOutcome
from risk_engine.v1_1.validator.account_risk_validator_v1_1 import (
    AccountRiskValidatorV1_1,
    AccountValidationResultV1_1,
)

# Governance
from tools.governance_validator import validate_bundle
from tools.governance_validator.evidence_writer import write_validation_evidence
from tools.governance_validator.io import EvidenceBundle


# ---------------------------------------------------------
# Outcome → Core Axis Mapping (LOCK)
# ---------------------------------------------------------
def _map_outcome_to_core_axis(
    outcome: ValidationOutcome,
) -> Tuple[str, bool, str | None]:

    if outcome is ValidationOutcome.ALLOW:
        return ("ALLOW", False, None)

    if outcome is ValidationOutcome.HARD_STOP:
        return ("DENY", True, "HARD_STOP")

    return ("DENY", True, None)


# ---------------------------------------------------------
# Trace Bundle Builder
# ---------------------------------------------------------
def _build_trace_bundle(decision: AccountRiskDecisionV1_1) -> list[dict]:
    """
    Minimal TraceBundle contract.
    This becomes EvidenceBundle.records input.
    """

    return [
        {
            "decision": getattr(decision, "decision", "UNKNOWN"),
            "fail_closed": getattr(decision, "fail_closed", True),
            "reason_code": getattr(decision, "reason_code", None),
            "meta": decision.meta or {},
            "model_version": decision.model_version,
        }
    ]


# ---------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------
def finalize_account_risk_decision_v1_1(
    decision: AccountRiskDecisionV1_1,
    *,
    validator: AccountRiskValidatorV1_1 | None = None,
    evidence_dir: Path | None = None,
    node_id: str | None = None,
    git_commit: str | None = None,
) -> tuple[AccountRiskDecisionV1_1, AccountValidationResultV1_1]:

    v = validator or AccountRiskValidatorV1_1()
    vr = v.validate(decision)

    # -----------------------------------
    # Map to core decision axis
    # -----------------------------------
    core_decision, fail_closed, action = _map_outcome_to_core_axis(vr.outcome)

    meta = dict(decision.meta or {})
    meta["account_validator_outcome"] = vr.outcome.value
    meta["account_validator_reason"] = vr.reason

    finalized = decision.model_copy(
        update={
            "decision": core_decision,
            "fail_closed": fail_closed,
            "action": action or decision.action,
            "meta": meta,
        }
    )

    # -----------------------------------
    # Governance Evidence Emission
    # -----------------------------------
    if evidence_dir is not None:

        trace_records = _build_trace_bundle(finalized)

        bundle = EvidenceBundle(
            records=trace_records,
            schema_set_ref="docs/schemas/v1",
        )

        validation_result = validate_bundle(bundle)

        # bundle 저장 → writer 입력 경로 필요
        bundle_path = Path(evidence_dir) / "runtime_trace_bundle.json"
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        bundle_path.write_text(
            json.dumps(trace_records, indent=2),
            encoding="utf-8",
        )

        write_validation_evidence(
            out_dir=evidence_dir,
            bundle_path=bundle_path,
            validation_result=validation_result,
            node_id=node_id,
            git_commit=git_commit,
        )

    return finalized, vr
