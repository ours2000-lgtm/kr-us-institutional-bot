from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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
    RuleSet,
)
from src.integration_core.policy_registry import get_policy_set
from src.integration_core.policy_override import PolicyOverride


# ============================================================
# Pipeline Result
# ============================================================

@dataclass(frozen=True)
class ConsistencyPipelineResult:
    """
    v0.5 pipeline contract:

    consistency -> aggregation -> policy composition -> evidence

    Invariants:
    - Evidence core hashing MUST NOT depend on rich_context.
    - Override MUST NOT affect hashing except via final policy fields.
    """

    consistency: ConsistencyResult
    aggregation: AggregationResult
    composition: CompositePolicyDecision
    policy: PolicyDecision
    evidence: EvidenceConsistencyRun


# ============================================================
# Helpers
# ============================================================

def _utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ============================================================
# Override Resolver
# ============================================================

def _resolve_policy_inputs(
    *,
    mode: Mode,
    policies: Optional[List[PolicySpec]],
    ruleset: Optional[RuleSet],
    override: Optional[PolicyOverride],
):
    """
    Determine final (ruleset, specs, mode) after applying override.

    Override precedence:
    1) replace_set_key
    2) replace_specs
    3) ruleset override
    4) force_policy_mode
    """

    # 1️⃣ Base resolution (registry default)
    if policies is None or ruleset is None:
        base_set = get_policy_set("default")
        resolved_specs = list(policies or base_set.policies)
        resolved_ruleset = ruleset or base_set.ruleset
    else:
        resolved_specs = list(policies)
        resolved_ruleset = ruleset

    resolved_mode = mode

    # 2️⃣ Apply override if present
    if override is not None:

        # replace whole registry set
        if override.replace_set_key is not None:
            ps = get_policy_set(override.replace_set_key)
            resolved_specs = list(ps.policies)
            resolved_ruleset = ps.ruleset

        # replace specs only
        if override.replace_specs is not None:
            resolved_specs = list(override.replace_specs)

        # override ruleset
        if override.ruleset is not None:
            resolved_ruleset = override.ruleset

        # force mode
        if override.force_policy_mode is not None:
            resolved_mode = override.force_policy_mode

    return resolved_ruleset, resolved_specs, resolved_mode


# ============================================================
# Pipeline
# ============================================================

def run_consistency_pipeline(
    *,
    consistency: ConsistencyResult,
    principal: Dict[str, str],
    timestamp_utc: Optional[str] = None,
    mode: Mode = "default",
    policies: Optional[List[PolicySpec]] = None,
    ruleset: Optional[RuleSet] = None,
    override: Optional[PolicyOverride] = None,
    rich_context: Optional[Dict[str, Any]] = None,
    schema_version: str = "v0.4",
) -> ConsistencyPipelineResult:
    """
    End-to-end consistency pipeline with override support.

    Core flow:
        Consistency -> Aggregation -> Composition -> Policy -> Evidence

    Hash contract:
    - Only consistency/aggregation/policy/principal/timestamp/schema_version
      affect evidence hash.
    - rich_context + override debug info MUST NOT affect hash.
    """

    ts = timestamp_utc or _utc_now_z()

    # 1️⃣ Aggregation
    aggregation = aggregate_consistency(consistency)

    # 2️⃣ Resolve policies & ruleset (with override)
    final_ruleset, final_specs, final_mode = _resolve_policy_inputs(
        mode=mode,
        policies=policies,
        ruleset=ruleset,
        override=override,
    )

    # 3️⃣ Compose
    composition = compose_policies(
        aggregation,
        policies=final_specs,
        mode=final_mode,
        ruleset=final_ruleset,
    )

    policy = composition.final

    # 4️⃣ Rich context (NOT hashed)
    ctx: Dict[str, Any] = dict(rich_context or {})

    ctx.setdefault(
        "composition",
        {
            "meta": {
                "ruleset": composition.meta.ruleset,
                "ordered_policy_refs": list(composition.meta.ordered_policy_refs),
                "ordered_policy_versions": list(composition.meta.ordered_policy_versions),
                "disabled_policy_refs": list(composition.meta.disabled_policy_refs),
                "disabled_policy_versions": list(composition.meta.disabled_policy_versions),
                "disabled_policy_priorities": list(
                    getattr(composition.meta, "disabled_policy_priorities", [])
                ),
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
            "mode": final_mode,
            "timestamp_utc": ts,
            "composition_ruleset": composition.meta.ruleset,
            "composition_ordered_policy_refs": list(
                composition.meta.ordered_policy_refs
            ),
            "composition_final_reason_codes": list(
                composition.final.reason_codes
            ),
        },
    )

    # 5️⃣ Evidence promotion
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