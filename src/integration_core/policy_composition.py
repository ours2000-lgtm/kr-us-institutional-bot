from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.integration_core.policy import (
    Grade,
    Mode,
    PolicyDecision,
    ReasonCode,
    apply_policy,
)

# -----------------------------
# Types
# -----------------------------


@dataclass(frozen=True)
class RuleSet:
    """
    RuleSet (v0.5+)

    strategy:
      - "fail_closed": legacy (equivalent to quorum(k=1))
      - "quorum": blocked_count >= quorum_k => BLOCK else ALLOW
      - "weighted": reserved (not implemented in this card)
      - "reserved": reserved (not implemented in this card)

    quorum_k:
      - Only used when strategy == "quorum"
      - Must satisfy: 1 <= quorum_k <= enabled_components_count
        (if not, fail-fast with ValueError)
    """

    name: str = "default"
    version: str = "v0.5"
    strategy: str = "fail_closed"
    quorum_k: int = 1


@dataclass(frozen=True)
class PolicySpec:
    """
    Policy definition spec for composition.
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
    Meta is for audit/debug (NOT hashed).
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
    Composition result (v0.5):
    - final: the composed PolicyDecision (hashed via Evidence core)
    - components/meta: rich_context only (MUST NOT affect hashes)
    """

    final: PolicyDecision
    components: List[PolicyDecision]
    meta: CompositionMeta


# -----------------------------
# Helpers
# -----------------------------


_GRADE_ORDER: Dict[Grade, int] = {"PASS": 0, "WARN": 1, "BLOCK": 2}


def _grade_max(grades: List[Grade]) -> Grade:
    if not grades:
        # fail-closed default if no components (should not happen in normal flow)
        return "BLOCK"
    return max(grades, key=lambda g: _GRADE_ORDER[g])


def _stable_unique(codes: List[ReasonCode]) -> List[ReasonCode]:
    seen: set[str] = set()
    out: List[ReasonCode] = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _sort_specs(specs: List[PolicySpec]) -> List[PolicySpec]:
    # Deterministic ordering: priority ASC, then ref ASC, then version ASC
    return sorted(specs, key=lambda s: (s.priority, s.ref, s.version))


def _compose_fail_closed(components: List[PolicyDecision]) -> Tuple[str, Grade]:
    # Legacy fail-closed: ANY BLOCK => BLOCK; else ALLOW
    any_block = any(c.decision == "BLOCK" for c in components)
    final_decision = "BLOCK" if any_block else "ALLOW"
    final_grade = _grade_max([c.grade for c in components if c.grade is not None] or ["BLOCK"])
    return final_decision, final_grade


def _compose_quorum(ruleset: RuleSet, components: List[PolicyDecision]) -> Tuple[str, Grade]:
    enabled_count = len(components)
    k = ruleset.quorum_k

    if k < 1:
        raise ValueError(f"RuleSet.quorum_k must be >= 1 (got {k})")
    if enabled_count <= 0:
        raise ValueError("quorum strategy requires at least one enabled policy component")
    if k > enabled_count:
        raise ValueError(
            f"RuleSet.quorum_k must be <= enabled policy count (k={k}, enabled={enabled_count})"
        )

    blocked = sum(1 for c in components if c.decision == "BLOCK")
    final_decision = "BLOCK" if blocked >= k else "ALLOW"
    final_grade = _grade_max([c.grade for c in components if c.grade is not None] or ["BLOCK"])
    return final_decision, final_grade


# -----------------------------
# Public API
# -----------------------------


def compose_policies(
    aggregation_result: Any,
    *,
    policies: List[PolicySpec],
    mode: Mode = "default",
    ruleset: Optional[RuleSet] = None,
) -> CompositePolicyDecision:
    """
    Compose multiple policies into a single final decision.

    Invariants:
    - Composition marker reason code MUST appear exactly once in final.reason_codes.
      - BLOCK => "P0-COMPOSITE-BLOCK"
      - ALLOW => "P2-COMPOSITE-ALLOW"
    - Ordering of reason_codes MUST be deterministic for identical inputs.
    """
    rs = ruleset or RuleSet(name="default", version="v0.5", strategy="fail_closed")

    ordered = _sort_specs(policies)
    enabled = [s for s in ordered if s.enabled]
    disabled = [s for s in ordered if not s.enabled]

    meta = CompositionMeta(
        ruleset=rs,
        ordered_policy_refs=[s.ref for s in enabled],
        ordered_policy_versions=[s.version for s in enabled],
        disabled_policy_refs=[s.ref for s in disabled],
        disabled_policy_versions=[s.version for s in disabled],
        disabled_policy_priorities=[s.priority for s in disabled],
    )

    # Evaluate enabled policies
    components: List[PolicyDecision] = []
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

    if not components:
        # fail-fast: composition requires at least one enabled policy
        raise ValueError("compose_policies requires at least one enabled policy spec")

    # Compose decision/grade
    if rs.strategy == "fail_closed":
        final_decision, final_grade = _compose_fail_closed(components)
    elif rs.strategy == "quorum":
        final_decision, final_grade = _compose_quorum(rs, components)
    elif rs.strategy == "weighted":
        raise NotImplementedError("RuleSet.strategy='weighted' is reserved for a later card")
    elif rs.strategy == "reserved":
        raise NotImplementedError("RuleSet.strategy='reserved' is reserved for a later card")
    else:
        raise ValueError(f"Unknown RuleSet.strategy: {rs.strategy!r}")

    # Merge reason codes deterministically (policy priority order already applied)
    merged: List[ReasonCode] = []
    for c in components:
        merged.extend(list(c.reason_codes))

    # Add composition marker at the front (then stable-unique)
    if final_decision == "BLOCK":
        merged.insert(0, "P0-COMPOSITE-BLOCK")
    else:
        merged.insert(0, "P2-COMPOSITE-ALLOW")

    merged = _stable_unique(merged)

    # Final policy decision identity for composed layer
    final = PolicyDecision(
        decision=final_decision,
        reason_codes=merged,
        policy_ref="COMPOSITE",
        policy_version=rs.version,
        grade=final_grade,
        notes=f"v0.5 composition ({rs.strategy})",
    )

    return CompositePolicyDecision(final=final, components=components, meta=meta)