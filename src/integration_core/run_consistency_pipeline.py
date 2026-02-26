from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.integration_core.aggregation import (
    AggregationResult,
    ConsistencyResult,
    aggregate_consistency,
)
from src.integration_core.evidence_consistency_run import (
    EvidenceConsistencyRun,
    promote_evidence_consistency_run,
)
from src.integration_core.policy import Mode, PolicyDecision
from src.integration_core.policy_composition import (
    CompositePolicyDecision,
    PolicySpec,
    compose_policies,
)
from src.integration_core.policy_override import PolicyOverride
from src.integration_core.policy_registry import get_policy_set


@dataclass(frozen=True)
class ConsistencyPipelineResult:
    """
    v0.5 pipeline contract:

    consistency (v0.3 lock)
      -> aggregation (v0.4)
      -> policy composition (v0.5: ruleset/strategy)
      -> evidence promotion (v0.4 core hashing)

    Invariants:
    - evidence core hashing must remain stable;
      rich_context MUST be excluded from hash calculation.
    """

    consistency: ConsistencyResult
    aggregation: AggregationResult
    composition: CompositePolicyDecision
    policy: PolicyDecision
    evidence: EvidenceConsistencyRun


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _apply_patch_specs(base: List[PolicySpec], patches: List[PolicySpec]) -> List[PolicySpec]:
    """
    Patch semantics (idempotent, deterministic):
    - If patch.ref exists in base -> replace that entry with patch.
    - Else -> append patch.
    """
    by_ref: Dict[str, PolicySpec] = {s.ref: s for s in base}
    order: List[str] = [s.ref for s in base]

    for p in patches:
        if p.ref in by_ref:
            by_ref[p.ref] = p
        else:
            by_ref[p.ref] = p
            order.append(p.ref)

    return [by_ref[r] for r in order]


def _override_block(
    *,
    override: PolicyOverride,
    base_policy_set_key: str,
    base_ruleset_key: str,
    base_mode: Mode,
    base_specs: List[PolicySpec],
) -> Tuple[str, str, Mode, List[PolicySpec], Dict[str, Any]]:
    """
    Override is intentionally handled as an "extra block":
    - It can modify policy_set_key / ruleset_key / mode / specs.
    - It returns (effective_*) + override_snapshot for rich_context recording.
    - It MUST NOT affect evidence hashes directly (record in rich_context only).
    """
    effective_policy_set_key = base_policy_set_key
    effective_ruleset_key = base_ruleset_key
    effective_mode: Mode = base_mode
    effective_specs: List[PolicySpec] = list(base_specs)

    # Best-effort snapshot for audit/debug
    snap: Dict[str, Any] = {
        "override_mode": getattr(override, "mode", None),
        "base": {
            "policy_set_key": base_policy_set_key,
            "ruleset_key": base_ruleset_key,
            "mode": base_mode,
            "policy_refs": [s.ref for s in base_specs],
            "policy_versions": [s.version for s in base_specs],
        },
        "effective": {},
    }

    ov_mode = getattr(override, "mode", None)

    # 1) Replace set
    replace_set = getattr(override, "replace_set", None)
    if ov_mode == "replace" and replace_set is not None:
        effective_specs = list(replace_set)

    # 2) Patch specs
    patch_specs = getattr(override, "patch_specs", None)
    if ov_mode == "patch" and patch_specs:
        effective_specs = _apply_patch_specs(effective_specs, list(patch_specs))

    # 3) Force policy mode (execution behavior override)
    force_policy_mode = getattr(override, "force_policy_mode", None)
    if ov_mode == "force" and force_policy_mode is not None:
        effective_mode = force_policy_mode

    # 4) Optional: allow overriding policy_set_key / ruleset_key if present
    # (kept optional so registry stays SSOT unless explicitly overridden)
    policy_set_key = getattr(override, "policy_set_key", None)
    if policy_set_key:
        effective_policy_set_key = policy_set_key

    ruleset_key = getattr(override, "ruleset_key", None)
    if ruleset_key:
        effective_ruleset_key = ruleset_key

    snap["effective"] = {
        "policy_set_key": effective_policy_set_key,
        "ruleset_key": effective_ruleset_key,
        "mode": effective_mode,
        "policy_refs": [s.ref for s in effective_specs],
        "policy_versions": [s.version for s in effective_specs],
    }

    return effective_policy_set_key, effective_ruleset_key, effective_mode, effective_specs, snap


def run_consistency_pipeline(
    *,
    consistency: ConsistencyResult,
    principal: Dict[str, str],
    timestamp_utc: Optional[str] = None,
    mode: Mode = "default",
    # Registry-driven defaults (SSOT)
    policy_set_key: str = "default",
    ruleset_key: str = "default",
    # Optional explicit injection (overrides registry baseline)
    policies: Optional[List[PolicySpec]] = None,
    # Override layer (does NOT affect hashes; recorded in rich_context only)
    override: Optional[PolicyOverride] = None,
    rich_context: Optional[Dict[str, Any]] = None,
    schema_version: str = "v0.4",
) -> ConsistencyPipelineResult:
    """
    End-to-end consistency pipeline.

    Core flow:
      ConsistencyResult -> AggregationResult -> compose_policies -> PolicyDecision -> EvidencePromotion

    Notes:
    - `mode` is part of the POLICY core (and thus affects hashes via policy fields).
    - `rich_context` is for audit/debug only and MUST NOT affect hashes.
    - Composition meta/components are recorded into rich_context only.
    - Registry provides SSOT defaults via (policy_set_key, ruleset_key).
    - Override is an additive block that can change effective mode/specs/ruleset,
      but its details are recorded ONLY into rich_context (hash-excluded).
    """
    ts = timestamp_utc or _utc_now_z()

    # 1) Aggregate (v0.4)
    aggregation = aggregate_consistency(consistency)

    # 2) Resolve baseline specs (Registry SSOT unless policies explicitly provided)
    if policies is not None:
        base_specs = list(policies)
    else:
        ps = get_policy_set(policy_set_key)
        base_specs = list(ps.policies)

    base_policy_set_key = policy_set_key
    base_ruleset_key = ruleset_key
    base_mode: Mode = mode

    # 3) OVERRIDE (extra block)
    override_snapshot: Optional[Dict[str, Any]] = None
    effective_policy_set_key = base_policy_set_key
    effective_ruleset_key = base_ruleset_key
    effective_mode: Mode = base_mode
    effective_specs: List[PolicySpec] = list(base_specs)

    if override is not None:
        (
            effective_policy_set_key,
            effective_ruleset_key,
            effective_mode,
            effective_specs,
            override_snapshot,
        ) = _override_block(
            override=override,
            base_policy_set_key=base_policy_set_key,
            base_ruleset_key=base_ruleset_key,
            base_mode=base_mode,
            base_specs=base_specs,
        )

    # 4) Compose policies (v0.5: ruleset/strategy dispatch happens inside compose_policies)
    composition = compose_policies(
        aggregation,
        policies=effective_specs,
        mode=effective_mode,
        ruleset_key=effective_ruleset_key,  # <-- 전략(예: quorum) 선택
    )

    # 5) Final policy is the composed final decision
    policy: PolicyDecision = composition.final

    # 6) Rich context (excluded from hashing)
    ctx: Dict[str, Any] = dict(rich_context or {})

    # 6-1) Record composition (stable key)
    ctx.setdefault(
        "composition",
        {
            "meta": {
                "ruleset": composition.meta.ruleset,
                "ordered_policy_refs": list(composition.meta.ordered_policy_refs),
                "ordered_policy_versions": list(composition.meta.ordered_policy_versions),
                "disabled_policy_refs": list(composition.meta.disabled_policy_refs),
                "disabled_policy_versions": list(composition.meta.disabled_policy_versions),
                "disabled_policy_priorities": list(composition.meta.disabled_policy_priorities),
            },
            "components": [
                {
                    "policy_ref": c.policy_ref,
                    "policy_version": c.policy_version,
                    "decision": c.decision,
                    "grade": c.grade,
                    "reason_codes": list(c.reason_codes),
                    "notes": c.notes,
                }
                for c in composition.components
            ],
        },
    )

    # 6-2) Record override snapshot (debug/audit only)
    if override_snapshot is not None:
        ctx.setdefault("policy_override", override_snapshot)

    # 6-3) Convenience snapshot (debug only)
    ctx.setdefault(
        "pipeline_snapshot",
        {
            "snapshot_id": consistency.snapshot_id,
            "graph_hash": consistency.graph_hash,
            "consistency_decision": consistency.decision,
            "violation_count": len(consistency.violations),
            "aggregation_grade": aggregation.grade,
            "policy_decision": policy.decision,
            "policy_grade": policy.grade,
            "mode": effective_mode,
            "timestamp_utc": ts,
            "policy_set_key": effective_policy_set_key,
            "ruleset_key": effective_ruleset_key,
            # composition debug extras (still NOT hashed)
            "composition_ruleset": composition.meta.ruleset,
            "composition_ordered_policy_refs": list(composition.meta.ordered_policy_refs),
            "composition_final_reason_codes": list(composition.final.reason_codes),
        },
    )

    # 7) Evidence promotion (v0.4)
    evidence = promote_evidence_consistency_run(
        consistency=consistency,
        aggregation=aggregation,
        policy=policy,
        principal=principal,
        timestamp_utc=ts,
        schema_version=schema_version,
        rich_context=ctx,
    )

    return ConsistencyPipelineResult(
        consistency=consistency,
        aggregation=aggregation,
        composition=composition,
        policy=policy,
        evidence=evidence,
    )