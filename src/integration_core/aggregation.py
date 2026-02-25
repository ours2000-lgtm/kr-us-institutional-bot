from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

Grade = Literal["PASS", "WARN", "BLOCK"]
CompatDecision = Literal["ALLOW", "BLOCK"]


@dataclass(frozen=True)
class ConsistencyResult:
    snapshot_id: Optional[str]
    graph_hash: str
    decision: Literal["PASS", "FAIL"]
    violations: List[Any]


@dataclass(frozen=True)
class AggregationResult:
    grade: Grade
    decision: CompatDecision
    summary: Dict[str, Any]
    violation_ids: List[str]
    violation_count: int
    policy_inputs: Dict[str, Any]


def _extract_violation_id(v: Any) -> str:
    if isinstance(v, dict):
        return str(v.get("violation_id") or v.get("id") or v.get("code") or "UNKNOWN")
    for key in ("violation_id", "id", "code"):
        if hasattr(v, key):
            return str(getattr(v, key))
    return "UNKNOWN"


def _grade_to_compat_decision(grade: Grade) -> CompatDecision:
    return "BLOCK" if grade == "BLOCK" else "ALLOW"


def aggregate_consistency(consistency: ConsistencyResult) -> AggregationResult:
    violations = consistency.violations or []
    violation_ids = [_extract_violation_id(v) for v in violations]
    violation_count = len(violation_ids)
    has_violations = violation_count > 0

    if consistency.decision == "FAIL":
        grade: Grade = "BLOCK"
    else:
        grade = "PASS" if not has_violations else "WARN"

    decision: CompatDecision = _grade_to_compat_decision(grade)

    summary: Dict[str, Any] = {
        "snapshot_id": consistency.snapshot_id,
        "graph_hash": consistency.graph_hash,
        "consistency_decision": consistency.decision,
        "violation_count": violation_count,
        "violation_ids": violation_ids,
        "grade": grade,
        "decision": decision,
    }

    policy_inputs: Dict[str, Any] = {
        "consistency_decision": consistency.decision,
        "grade": grade,
        "violation_count": violation_count,
        "has_violations": has_violations,
    }

    return AggregationResult(
        grade=grade,
        decision=decision,
        summary=summary,
        violation_ids=violation_ids,
        violation_count=violation_count,
        policy_inputs=policy_inputs,
    )


# -------------------------------------------------------------------
# MVP compatibility layer (tests_mvp)
# -------------------------------------------------------------------

DecisionPF = Literal["PASS", "FAIL", "WARN"]


@dataclass(frozen=True, init=False)
class ValidationOutcome:
    validation_id: str
    decision: DecisionPF
    violations: List[Any]

    def __init__(
        self,
        validation_id: Optional[str] = None,
        decision: Optional[DecisionPF] = None,
        violations: Optional[List[Any]] = None,
        *,
        val_id: Optional[str] = None,
        status: Optional[str] = None,
    ):
        vid = (validation_id or val_id or "UNKNOWN")
        dec = (decision or status or "PASS")
        dec_u = str(dec).upper()
        if dec_u not in ("PASS", "FAIL", "WARN"):
            dec_u = "PASS"

        object.__setattr__(self, "validation_id", str(vid))
        object.__setattr__(self, "decision", dec_u)  # type: ignore[assignment]
        object.__setattr__(self, "violations", list(violations or []))


class AnyFailBlockPolicy:
    """
    MVP test contract (observed):
      - empty outcomes => BLOCK (fail-safe)
      - any FAIL       => BLOCK
      - else any WARN  => ALLOW (but WARN grade)
      - else           => ALLOW (PASS grade)

    Required summary keys (observed):
      - summary["counts"]["PASS"|"FAIL"|"WARN"]
      - summary["failed_val_ids"]  (alias of fail_ids)
    """

    policy_ref: str = "AnyFailBlockPolicy"
    policy_version: str = "v0.4"

    def evaluate(self, outcomes: List[ValidationOutcome]) -> AggregationResult:
        return self.aggregate(outcomes)

    def aggregate(self, outcomes: List[ValidationOutcome]) -> AggregationResult:
        outcomes = outcomes or []

        counts = {"PASS": 0, "FAIL": 0, "WARN": 0}
        for o in outcomes:
            if o.decision in counts:
                counts[o.decision] += 1

        fail_ids = [o.validation_id for o in outcomes if o.decision == "FAIL"]
        warn_ids = [o.validation_id for o in outcomes if o.decision == "WARN"]

        violation_ids: List[str] = []
        for o in outcomes:
            for v in (o.violations or []):
                violation_ids.append(_extract_violation_id(v))
        violation_count = len(violation_ids)
        has_violations = violation_count > 0

        empty_fail_safe = len(outcomes) == 0

        if empty_fail_safe:
            grade: Grade = "BLOCK"
        elif len(fail_ids) > 0:
            grade = "BLOCK"
        elif len(warn_ids) > 0 or has_violations:
            grade = "WARN"
        else:
            grade = "PASS"

        decision: CompatDecision = _grade_to_compat_decision(grade)

        summary: Dict[str, Any] = {
            "counts": counts,
            "total": len(outcomes),
            "fail_count": len(fail_ids),
            "fail_ids": fail_ids,
            "failed_val_ids": fail_ids,  # <-- MVP contract alias
            "warn_count": len(warn_ids),
            "warn_ids": warn_ids,
            "violation_count": violation_count,
            "violation_ids": violation_ids,
            "grade": grade,
            "decision": decision,
            "empty_fail_safe": empty_fail_safe,
        }

        policy_inputs: Dict[str, Any] = {
            "grade": grade,
            "decision": decision,
            "counts": counts,
            "fail_count": len(fail_ids),
            "warn_count": len(warn_ids),
            "has_fail": len(fail_ids) > 0,
            "has_warn": len(warn_ids) > 0,
            "has_violations": has_violations,
            "violation_count": violation_count,
            "empty_fail_safe": empty_fail_safe,
        }

        return AggregationResult(
            grade=grade,
            decision=decision,
            summary=summary,
            violation_ids=violation_ids,
            violation_count=violation_count,
            policy_inputs=policy_inputs,
        )

    def apply(self, outcomes: List[ValidationOutcome]) -> AggregationResult:
        return self.aggregate(outcomes)

    def __call__(self, outcomes: List[ValidationOutcome]) -> AggregationResult:
        return self.aggregate(outcomes)