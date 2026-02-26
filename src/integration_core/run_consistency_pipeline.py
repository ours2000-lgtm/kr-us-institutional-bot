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
)


@dataclass(frozen=True)
class ConsistencyPipelineResult:
    """
    v0.5 pipeline contract:
    - consistency (v0.3 lock) -> aggregation (v0.4) -> policy composition (v0.5) -> evidence promotion (v0.4)
    - evidence core hashing must remain stable; rich_context MUST be excluded from hash calculation.
    """

    consistency: ConsistencyResult
    aggregation: AggregationResult
    composition: CompositePolicyDecision
    policy: PolicyDecision
    evidence: EvidenceConsistencyRun


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_consistency_pipeline(
    *,
    consistency: ConsistencyResult,
    principal: Dict[str, str],
    timestamp_utc: Optional[str] = None,
    mode: Mode = "default",
    policies: Optional[List[PolicySpec]] = None,
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
    """
    ts = timestamp_utc or _utc_now_z()

    # 1) Aggregate (v0.4)
    aggregation = aggregate_consistency(consistency)

    # 2) Compose policies (v0.5)
    specs = policies or [
        PolicySpec(ref="AnyFailBlockPolicy", version="v0.4", enabled=True, priority=100)
    ]
    composition = compose_policies(aggregation, policies=specs, mode=mode)

    # 3) Final policy is the composed final decision
    policy = composition.final

    # 4) Rich context (excluded from hashing)
    ctx: Dict[str, Any] = dict(rich_context or {})

    # Keep meta/components under a stable key
    ctx.setdefault(
        "composition",
        {
            "meta": {
                "ruleset": composition.meta.ruleset,
                "ordered_policy_refs": list(composition.meta.ordered_policy_refs),
                "ordered_policy_versions": list(composition.meta.ordered_policy_versions),
                "disabled_policy_refs": list(composition.meta.disabled_policy_refs),
                "disabled_policy_versions": list(composition.meta.disabled_policy_versions),
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

    # Convenience snapshot (debug only)
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
            "mode": mode,
            "timestamp_utc": ts,
            # composition debug extras (still NOT hashed)
            "composition_ruleset": composition.meta.ruleset,
            "composition_ordered_policy_refs": list(composition.meta.ordered_policy_refs),
            "composition_final_reason_codes": list(composition.final.reason_codes),
        },
    )

    # 5) Evidence promotion (v0.4)
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