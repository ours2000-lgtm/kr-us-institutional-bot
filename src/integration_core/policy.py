from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from .aggregation import AggregationResult, Grade

Decision = Literal["ALLOW", "BLOCK"]
Mode = Literal["default", "strict", "warn", "block"]

"""
Mode semantics (v0.4):
- default: aggregation 기반 기본 정책.
- strict : WARN도 BLOCK 처리.
- warn   : WARN을 ALLOW 하되 별도 reason_code로 표시.
- block  : 모든 입력 BLOCK (긴급 차단용).
"""

ReasonCode = Literal[
    "P0-AGG-BLOCK",
    "P0-MODE-BLOCK-ALL",
    "P0-MODE-STRICT-BLOCK",
    "P0-POLICY-MISMATCH",
    "P2-AGG-WARN-ALLOW",
    "P2-AGG-PASS-ALLOW",
    "P2-MODE-WARN-ALLOW",
]


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class PolicyDecision:
    """
    v0.4 Policy SSOT contract.

    Invariants (doc-level, can be enforced via tests):
    - decision == "BLOCK" implies grade == "BLOCK" or mode in {"block", "strict"}.
    - decision == "ALLOW" implies grade in {"PASS", "WARN"}.
    """

    decision: Decision
    grade: Grade
    reason_codes: List[ReasonCode]

    policy_ref: str
    policy_version: str
    mode: Mode

    notes: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None


def apply_policy(
    aggregation_result: AggregationResult,
    *,
    mode: Mode = "default",
    policy_ref: str = "AnyFailBlockPolicy",
    policy_version: str = "v0.4",
    expected_policy_ref: str = "AnyFailBlockPolicy",
    expected_policy_version: str = "v0.4",
) -> PolicyDecision:
    """
    v0.4 policy evaluation.

    Governance mismatch rule:
    - if policy_ref/version differs from expected => add P0-POLICY-MISMATCH

    Mode precedence:
    0) block  => unconditional BLOCK (P0-MODE-BLOCK-ALL)
    1) strict => WARN/BLOCK => BLOCK (P0-MODE-STRICT-BLOCK), PASS => ALLOW (P2-AGG-PASS-ALLOW)
    2) default/warn:
       - BLOCK => BLOCK (P0-AGG-BLOCK)
       - WARN  => ALLOW (default: P2-AGG-WARN-ALLOW, warn: P2-MODE-WARN-ALLOW)
       - PASS  => ALLOW (P2-AGG-PASS-ALLOW)
    """
    grade = aggregation_result.grade
    reason_codes: List[ReasonCode] = []
    notes: Optional[str] = None

    # 1) Policy mismatch (always evaluated first; order stability)
    if policy_ref != expected_policy_ref or policy_version != expected_policy_version:
        reason_codes.append("P0-POLICY-MISMATCH")

    # 2) Mode precedence
    if mode == "block":
        decision: Decision = "BLOCK"
        reason_codes.append("P0-MODE-BLOCK-ALL")
        notes = "Mode=block => unconditional BLOCK."

    elif mode == "strict":
        if grade in ("BLOCK", "WARN"):
            decision = "BLOCK"
            reason_codes.append("P0-MODE-STRICT-BLOCK")
            notes = "Mode=strict => WARN/BLOCK treated as BLOCK."
        else:
            decision = "ALLOW"
            reason_codes.append("P2-AGG-PASS-ALLOW")
            notes = "Allow with PASS grade under strict mode."

    else:  # default / warn
        if grade == "BLOCK":
            decision = "BLOCK"
            reason_codes.append("P0-AGG-BLOCK")
            notes = "Aggregation grade BLOCK => fail-closed."
        else:
            decision = "ALLOW"
            if grade == "WARN":
                if mode == "warn":
                    reason_codes.append("P2-MODE-WARN-ALLOW")
                    notes = "Mode=warn => WARN allowed with explicit mode reason."
                else:
                    reason_codes.append("P2-AGG-WARN-ALLOW")
                    notes = "Allow with WARN grade."
            else:
                reason_codes.append("P2-AGG-PASS-ALLOW")
                notes = "Allow with PASS grade."

    # (Optional) Dedup guard (keeps ordering; removes duplicates if any future logic adds twice)
    # Not strictly necessary, but harmless and supports the "no duplicates" invariant.
    if len(reason_codes) != len(set(reason_codes)):
        seen = set()
        deduped: List[ReasonCode] = []
        for rc in reason_codes:
            if rc not in seen:
                deduped.append(rc)
                seen.add(rc)
        reason_codes = deduped

    inputs: Dict[str, Any] = {
        "grade": grade,
        "aggregation_decision_compat": aggregation_result.decision,  # ALLOW/BLOCK surface
        "violation_count": aggregation_result.violation_count,
        "summary": aggregation_result.summary,  # ops/audit snapshot (not Evidence core)
        "mode": mode,
        "timestamp_utc": _utc_now_z(),
    }

    return PolicyDecision(
        decision=decision,
        grade=grade,
        reason_codes=reason_codes,
        policy_ref=policy_ref,
        policy_version=policy_version,
        mode=mode,
        notes=notes,
        inputs=inputs,
    )


def apply_policies(
    policies: List[str],
    aggregation_result: AggregationResult,
    *,
    mode: Mode = "default",
    policy_version: str = "v0.4",
    expected_policy_version: str = "v0.4",
) -> PolicyDecision:
    """
    Compose multiple policies.
    v0.4: 첫 번째 정책만 사용 (단일 정책과 동일 동작).
    """
    primary_ref = policies[0] if policies else "AnyFailBlockPolicy"
    return apply_policy(
        aggregation_result,
        mode=mode,
        policy_ref=primary_ref,
        policy_version=policy_version,
        expected_policy_ref=primary_ref,
        expected_policy_version=expected_policy_version,
    )