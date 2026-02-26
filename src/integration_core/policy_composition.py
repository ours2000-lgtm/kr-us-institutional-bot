from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Literal, Tuple

from .aggregation import AggregationResult, Grade
from .policy import PolicyDecision, apply_policy, ReasonCode

Mode = Literal["default", "strict", "warn", "block"]


@dataclass(frozen=True)
class RuleSet:
    """
    v0.5 composition ruleset container.

    MVP: only identity + stable ordering rules are used.
    """
    name: str = "v0.5-fail-closed"
    version: str = "v0.5"


@dataclass(frozen=True)
class PolicySpec:
    """
    Policy definition spec used by v0.5 composition.

    - ref/version: policy identity
    - enabled: if False, excluded from evaluation (recorded in meta only)
    - priority: deterministic ordering key (ascending)
    - expected_ref/expected_version: optional expected identity for mismatch detection
    """
    ref: str
    version: str
    enabled: bool = True
    priority: int = 100
    expected_ref: Optional[str] = None
    expected_version: Optional[str] = None


@dataclass(frozen=True)
class CompositionMeta:
    """
    v0.5 composition metadata (NON-HASH ZONE).
    Intended for audit/debug purposes only.

    ordered_*: enabled policies in evaluation order
    disabled_*: disabled policies captured for auditability
    """
    ruleset: RuleSet
    ordered_policy_refs: List[str]
    ordered_policy_versions: List[str]
    disabled_policy_refs: List[str]
    disabled_policy_versions: List[str]
    disabled_policy_priorities: List[int]


@dataclass(frozen=True)
class CompositePolicyDecision:
    """
    v0.5 composite decision root.

    - final: the final policy decision (policy_ref="COMPOSITE", policy_version="v0.5")
    - components: component decisions for enabled policies (NON-HASH ZONE)
    - meta: ordering + disabled policy record (NON-HASH ZONE)
    """
    final: PolicyDecision
    components: List[PolicyDecision]
    meta: CompositionMeta


def _grade_rank(g: Grade) -> int:
    return {"PASS": 0, "WARN": 1, "BLOCK": 2}[g]


def _max_grade(grades: List[Grade]) -> Grade:
    if not grades:
        return "PASS"
    return max(grades, key=_grade_rank)


def _stable_unique(reason_codes: List[ReasonCode]) -> List[ReasonCode]:
    seen = set()
    out: List[ReasonCode] = []
    for rc in reason_codes:
        if rc in seen:
            continue
        seen.add(rc)
        out.append(rc)
    return out


def _sort_specs(specs: List[PolicySpec]) -> List[PolicySpec]:
    # Deterministic ordering rule:
    # 1) enabled=True first
    # 2) priority asc
    # 3) ref asc
    # 4) version asc
    return sorted(
        specs,
        key=lambda s: (not s.enabled, s.priority, s.ref, s.version),
    )


def default_policy_specs_v05() -> List[PolicySpec]:
    # Backward-compatible default: single policy
    return [PolicySpec(ref="AnyFailBlockPolicy", version="v0.4", enabled=True, priority=100)]


def compose_policies(
    aggregation_result: AggregationResult,
    *,
    policies: Optional[List[PolicySpec]] = None,
    mode: Mode = "default",
    ruleset: Optional[RuleSet] = None,
) -> CompositePolicyDecision:
    """
    Compose multiple policies under a fail-closed rule.

    - Evaluate enabled policies in deterministic order.
    - final.decision = BLOCK if any component blocks, else ALLOW.
    - final.grade = max(component.grade)
    - Insert composition marker reason code at reason_codes[0].
    - Record disabled policies in meta (refs/versions/priorities).
    """
    ruleset = ruleset or RuleSet()
    specs = _sort_specs(policies or default_policy_specs_v05())

    enabled = [s for s in specs if s.enabled]
    disabled = [s for s in specs if not s.enabled]

    meta = CompositionMeta(
        ruleset=ruleset,
        ordered_policy_refs=[s.ref for s in enabled],
        ordered_policy_versions=[s.version for s in enabled],
        disabled_policy_refs=[s.ref for s in disabled],
        disabled_policy_versions=[s.version for s in disabled],
        disabled_policy_priorities=[s.priority for s in disabled],
    )

    components: List[PolicyDecision] = []
    merged_reason_codes: List[ReasonCode] = []
    component_grades: List[Grade] = []
    any_block = False

    for spec in enabled:
        exp_ref = spec.expected_ref or spec.ref
        exp_ver = spec.expected_version or spec.version

        d = apply_policy(
            aggregation_result,
            mode=mode,
            policy_ref=spec.ref,
            policy_version=spec.version,
            expected_policy_ref=exp_ref,
            expected_policy_version=exp_ver,
        )
        components.append(d)

        component_grades.append(d.grade)
        merged_reason_codes.extend(d.reason_codes)

        if d.decision == "BLOCK":
            any_block = True

    final_grade: Grade = _max_grade(component_grades)

    if any_block:
        final_decision: Literal["ALLOW", "BLOCK"] = "BLOCK"
        marker: ReasonCode = "P0-COMPOSITE-BLOCK"
    else:
        final_decision = "ALLOW"
        marker = "P2-COMPOSITE-ALLOW"

    # Marker must be first and appear exactly once.
    merged_reason_codes = [marker] + merged_reason_codes
    merged_reason_codes = _stable_unique(merged_reason_codes)

    notes = (
        f"v0.5 composition ({ruleset.name}): "
        f"components={len(components)}, "
        f"disabled={len(disabled)}, "
        f"final_grade={final_grade}"
    )

    final = PolicyDecision(
        decision=final_decision,
        reason_codes=merged_reason_codes,
        policy_ref="COMPOSITE",
        policy_version=ruleset.version,
        grade=final_grade,
        notes=notes,
    )

    return CompositePolicyDecision(final=final, components=components, meta=meta)