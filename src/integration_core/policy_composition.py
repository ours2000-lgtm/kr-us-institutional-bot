from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import List, Literal, Optional, Sequence, Tuple


# ---------------------------------------------------------------------
# Core enums
# ---------------------------------------------------------------------
Grade = Literal["PASS", "WARN", "BLOCK"]
Decision = Literal["ALLOW", "BLOCK"]
Mode = Literal["default", "strict", "warn", "block"]

Strategy = Literal["fail-closed", "quorum", "weighted"]


ReasonCode = Literal[
    # aggregation/policy layer
    "P0-AGG-BLOCK",
    "P0-MODE-BLOCK-ALL",
    "P0-MODE-STRICT-BLOCK",
    "P0-POLICY-MISMATCH",
    "P2-AGG-WARN-ALLOW",
    "P2-AGG-PASS-ALLOW",
    "P2-MODE-WARN-ALLOW",
    # composition layer markers
    "P0-COMPOSITE-BLOCK",
    "P2-COMPOSITE-ALLOW",
]


# ---------------------------------------------------------------------
# RuleSet / Specs
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class RuleSet:
    """
    Composition ruleset identity + strategy selector.

    strategy meanings (v0.5.2):
    - fail-closed: ANY component BLOCK => final BLOCK
    - quorum     : reserved (NotImplementedError)
    - weighted   : reserved (NotImplementedError)
    """
    name: str
    version: str
    strategy: Strategy = "fail-closed"


@dataclass(frozen=True)
class PolicySpec:
    ref: str
    version: str
    enabled: bool = True
    priority: int = 100
    expected_ref: Optional[str] = None
    expected_version: Optional[str] = None


# ---------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    reason_codes: List[ReasonCode]
    policy_ref: str
    policy_version: str
    grade: Optional[Grade] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class CompositionMeta:
    ruleset: RuleSet
    ordered_policy_refs: List[str]
    ordered_policy_versions: List[str]
    disabled_policy_refs: List[str]
    disabled_policy_versions: List[str]
    disabled_policy_priorities: List[int]


@dataclass(frozen=True)
class CompositePolicyDecision:
    meta: CompositionMeta
    components: List[PolicyDecision]
    final: PolicyDecision


# ---------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------
_GRADE_ORDER = {"PASS": 0, "WARN": 1, "BLOCK": 2}


def _max_grade(grades: Sequence[Optional[Grade]]) -> Optional[Grade]:
    g = [x for x in grades if x is not None]
    if not g:
        return None
    return max(g, key=lambda x: _GRADE_ORDER[x])


def _stable_unique(xs: Sequence[ReasonCode]) -> List[ReasonCode]:
    seen = set()
    out: List[ReasonCode] = []
    for x in xs:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def _sort_specs(policies: Sequence[PolicySpec]) -> List[PolicySpec]:
    # enabled first, then priority, then stable lexical
    return sorted(
        list(policies),
        key=lambda s: (not s.enabled, s.priority, s.ref, s.version),
    )


# ---------------------------------------------------------------------
# Minimal apply_policy used by composition
# (If you already have src/integration_core/policy.py apply_policy,
#  this function is ONLY for composition fallback usage; you may remove
#  if composition calls the other apply_policy directly.)
# ---------------------------------------------------------------------
def apply_policy(
    aggregation_result,
    *,
    mode: Mode = "default",
    policy_ref: str = "AnyFailBlockPolicy",
    policy_version: str = "v0.5",
    expected_policy_ref: Optional[str] = None,
    expected_policy_version: Optional[str] = None,
) -> PolicyDecision:
    """
    v0.5 policy SSOT (thin): decision derived from aggregation grade + mode.

    NOTE:
    - This exists to keep composition self-contained.
    - If your project already defines apply_policy elsewhere, composition can import it.
    """
    grade: Grade = aggregation_result.grade  # expects Grade str
    reason_codes: List[ReasonCode] = []
    notes: Optional[str] = None

    exp_ref = expected_policy_ref or policy_ref
    exp_ver = expected_policy_version or policy_version
    if policy_ref != exp_ref or policy_version != exp_ver:
        reason_codes.append("P0-POLICY-MISMATCH")

    # Mode semantics
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

    return PolicyDecision(
        decision=decision,
        reason_codes=_stable_unique(reason_codes),
        policy_ref=policy_ref,
        policy_version=policy_version,
        grade=grade,
        notes=notes,
    )


# ---------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------
def compose_policies(
    aggregation_result,
    *,
    policies: Sequence[PolicySpec],
    mode: Mode = "default",
    ruleset: Optional[RuleSet] = None,
) -> CompositePolicyDecision:
    """
    Compose multiple policy decisions into a single final decision.

    v0.5.2:
    - fail-closed is implemented (ANY BLOCK => BLOCK)
    - quorum/weighted are reserved (NotImplementedError)
    """
    ruleset = ruleset or RuleSet(name="v0.5-fail-closed", version="v0.5", strategy="fail-closed")

    ordered = _sort_specs(policies)
    enabled = [s for s in ordered if s.enabled]
    disabled = [s for s in ordered if not s.enabled]

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
        merged_reason_codes.extend(d.reason_codes)

    final_grade = _max_grade([c.grade for c in components]) or aggregation_result.grade

    # Strategy dispatch
    if ruleset.strategy == "fail-closed":
        final_decision: Decision = "BLOCK" if any(c.decision == "BLOCK" for c in components) else "ALLOW"
    elif ruleset.strategy == "quorum":
        raise NotImplementedError("RuleSet.strategy='quorum' is reserved for v0.6+")
    elif ruleset.strategy == "weighted":
        raise NotImplementedError("RuleSet.strategy='weighted' is reserved for v0.6+")
    else:
        raise ValueError(f"Unknown ruleset.strategy: {ruleset.strategy}")

    # Composition marker must be the first reason code
    if final_decision == "BLOCK":
        merged_reason_codes.insert(0, "P0-COMPOSITE-BLOCK")
        notes = f"composition={ruleset.name}@{ruleset.version} strategy={ruleset.strategy}: BLOCK"
        policy_ref = "COMPOSITE"
        policy_version = ruleset.version
        final_reason_codes = _stable_unique(merged_reason_codes)
    else:
        merged_reason_codes.insert(0, "P2-COMPOSITE-ALLOW")
        notes = f"composition={ruleset.name}@{ruleset.version} strategy={ruleset.strategy}: ALLOW"
        policy_ref = "COMPOSITE"
        policy_version = ruleset.version
        final_reason_codes = _stable_unique(merged_reason_codes)

    final = PolicyDecision(
        decision=final_decision,
        reason_codes=final_reason_codes,
        policy_ref=policy_ref,
        policy_version=policy_version,
        grade=final_grade,
        notes=notes,
    )

    return CompositePolicyDecision(
        meta=meta,
        components=components,
        final=final,
    )


def composition_meta_to_dict(meta: CompositionMeta) -> dict:
    d = asdict(meta)
    # RuleSet is a dataclass; asdict already expands it.
    return d