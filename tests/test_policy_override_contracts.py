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
from src.integration_core.policy_override import PolicyOverride  # v0.5.3
from src.integration_core.policy_registry import get_policy_set  # v0.5.1


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


def _apply_override_to_specs(
    specs: List[PolicySpec],
    override: PolicyOverride,
) -> List[PolicySpec]:
    """
    Apply patch_specs override:
    - disable refs (enabled=False)
    - priority overrides
    """
    disable = set(override.disable_refs or [])
    prio_over = override.priority_overrides or {}

    patched: List[PolicySpec] = []
    for s in specs:
        patched.append(
            PolicySpec(
                ref=s.ref,
                version=s.version,
                enabled=(s.enabled and (s.ref not in disable)),
                priority=prio_over.get(s.ref, s.priority),
                expected_ref=getattr(s, "expected_ref", None),
                expected_version=getattr(s, "expected_version", None),
            )
        )
    return patched


def run_consistency_pipeline(
    *,
    consistency: ConsistencyResult,
    principal: Dict[str, str],
    timestamp_utc: Optional[str] = None,
    mode: Mode = "default",
    policies: Optional[List[PolicySpec]] = None,
    rich_context: Optional[Dict[str, Any]] = None,
    schema_version: str = "v0.4",
    override: Optional[PolicyOverride] = None,  # v0.5.3
) -> ConsistencyPipelineResult:
    """
    End-to-end consistency pipeline.

    Core flow:
      ConsistencyResult -> AggregationResult -> compose_policies -> PolicyDecision -> EvidencePromotion

    Notes:
    - `mode` is part of the POLICY core (and thus affects hashes via policy fields).
    - `rich_context` is for audit/debug only and MUST NOT affect hashes.
    - Composition meta/components are recorded into rich_context only.
    - Override is recorded into rich_context only; however, override can change chosen specs / mode,
      which will affect policy core and thus hashes (by design).
    """
    ts = timestamp_utc or _utc_now_z()
    ov = override or PolicyOverride(mode="none")

    # 1) Aggregate (v0.4)
    aggregation = aggregate_consistency(consistency)

    # 2) Resolve policy specs (base -> override replace/patch)
    base_specs: List[PolicySpec]
    if policies is not None:
        base_specs = list(policies)
    else:
        base_specs = [
            PolicySpec(ref="AnyFailBlockPolicy", version="v0.4", enabled=True, priority=100)
        ]

    effective_specs = base_specs
    if ov.mode == "replace_set":
        key = ov.policy_set_key or "default"
        effective_specs = list(get_policy_set(key))

    if ov.mode == "patch_specs":
        effective_specs = _apply_override_to_specs(effective_specs, ov)

    # 3) Resolve effective mode (override force_mode)
    effective_mode: Mode = mode
    if ov.mode == "force_mode" and ov.force_policy_mode is not None:
        effective_mode = ov.force_policy_mode

    # 4) Compose policies (v0.5)
    composition = compose_policies(aggregation, policies=effective_specs, mode=effective_mode)

    # 5) Final policy is the composed final decision
    policy = composition.final

    # 6) Rich context (excluded from hashing)
    ctx: Dict[str, Any] = dict(rich_context or {})

    # Always record override in rich_context (hash-excluded)
    ctx.setdefault("override", ov.to_rich_dict())

    # Keep meta/components under a stable key (debug only)
    meta_dict = {
        "ruleset": composition.meta.ruleset,
        "ordered_policy_refs": list(composition.meta.ordered_policy_refs),
        "ordered_policy_versions": list(composition.meta.ordered_policy_versions),
        "disabled_policy_refs": list(composition.meta.disabled_policy_refs),
        "disabled_policy_versions": list(composition.meta.disabled_policy_versions),
    }
    # v0.5.2+: optional priorities
    if hasattr(composition.meta, "disabled_policy_priorities"):
        meta_dict["disabled_policy_priorities"] = list(composition.meta.disabled_policy_priorities)

    ctx.setdefault(
        "composition",
        {
            "meta": meta_dict,
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
    snapshot = {
        "snapshot_id": consistency.snapshot_id,
        "graph_hash": consistency.graph_hash,
        "consistency_decision": consistency.decision,
        "violation_count": len(consistency.violations),
        "aggregation_grade": aggregation.grade,
        "policy_decision": policy.decision,
        "policy_grade": policy.grade,
        "mode": effective_mode,
        "timestamp_utc": ts,
        # composition debug extras (still NOT hashed)
        "composition_ruleset": composition.meta.ruleset,
        "composition_ordered_policy_refs": list(composition.meta.ordered_policy_refs),
        "composition_final_reason_codes": list(composition.final.reason_codes),
    }
    if hasattr(composition.meta, "disabled_policy_priorities"):
        snapshot["composition_disabled_policy_priorities"] = list(
            composition.meta.disabled_policy_priorities
        )

    ctx.setdefault("pipeline_snapshot", snapshot)

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

# ---------------------------------------------------------------------
# v0.5.3 Override hardening (hash-safety + marker invariants)
# Append-only tests: DO NOT modify existing tests above.
# ---------------------------------------------------------------------

from src.integration_core.run_consistency_pipeline import run_consistency_pipeline
from src.integration_core.policy_composition import PolicySpec
from src.integration_core.policy_override import PolicyOverride


def _marker(rcs: list[str]) -> str:
    markers = [rc for rc in rcs if rc in ("P0-COMPOSITE-BLOCK", "P2-COMPOSITE-ALLOW")]
    assert len(markers) == 1, f"Expected exactly one composite marker, got={markers} / rcs={rcs}"
    return markers[0]


def test_override_patch_specs_no_effect_keeps_hashes_identical():
    """
    Hash-safety contract:
    If override does NOT change the effective policy outcome,
    then inputs_hash/evidence_hash MUST remain identical.
    Override MUST be recorded in rich_context ONLY.
    """
    c = _consistency()
    ts = "2026-02-26T00:00:00Z"

    # Baseline: default behavior
    r0 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
    )

    # Patch override that is "no-op" in effect:
    # We patch the policy specs to the same set that baseline would use anyway.
    specs = [
        PolicySpec(ref="AnyFailBlockPolicy", version="v0.4", enabled=True, priority=100)
    ]
    ov = PolicyOverride(
        mode="patch_specs",
        patch_specs=specs,
    )

    r1 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
        override=ov,
    )

    assert r0.evidence.inputs_hash == r1.evidence.inputs_hash
    assert r0.evidence.evidence_hash == r1.evidence.evidence_hash

    # override is audit/debug only (rich_context), never in core hash input
    rc1 = r1.evidence.rich_context or {}
    assert "override" in rc1, "override MUST be recorded in rich_context"
    # (Optional) minimal sanity: ensure it is not empty
    assert rc1["override"]


def test_override_force_mode_changes_decision_and_changes_hashes():
    """
    Override behavior contract:
    If override changes the effective policy outcome (e.g., force_mode=block),
    then hashes MUST change because core policy fields change.
    """
    c = _consistency()
    ts = "2026-02-26T00:00:00Z"

    r0 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
    )

    ov = PolicyOverride(
        mode="force_mode",
        force_policy_mode="block",
    )

    r1 = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
        override=ov,
    )

    # Must block regardless of aggregation
    assert r1.policy.decision == "BLOCK"

    # Since core policy result is different, hashes must differ
    assert r0.evidence.inputs_hash != r1.evidence.inputs_hash
    assert r0.evidence.evidence_hash != r1.evidence.evidence_hash


def test_override_replace_set_records_set_key_in_rich_context():
    """
    replace_set audit contract:
    policy_set_key MUST be preserved in rich_context for auditability.
    """
    c = _consistency()
    ts = "2026-02-26T00:00:00Z"

    ov = PolicyOverride(
        mode="replace_set",
        policy_set_key="default",
    )

    r = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
        override=ov,
    )

    rc = r.evidence.rich_context or {}
    assert "override" in rc
    # Expect the registry key to be recorded
    # (key name depends on PolicyOverride.to_rich_dict implementation; these two cover common shapes)
    o = rc["override"]
    if isinstance(o, dict) and "policy_set_key" in o:
        assert o["policy_set_key"] == "default"
    elif isinstance(o, dict) and "replace_set" in o and isinstance(o["replace_set"], dict):
        assert o["replace_set"].get("policy_set_key") == "default"
    else:
        raise AssertionError(f"Unexpected override rich_context shape: {o}")


def test_override_marker_reason_code_invariant_exactly_once_and_first():
    """
    Marker invariant (audit/diff stability):
    - composite marker MUST appear exactly once
    - marker MUST be the first reason_code
    This must hold even when override is used.
    """
    c = _consistency()
    ts = "2026-02-26T00:00:00Z"

    # Run with an override to ensure invariants survive override paths.
    ov = PolicyOverride(mode="force_mode", force_policy_mode="block")

    r = run_consistency_pipeline(
        consistency=c,
        principal=_principal(),
        timestamp_utc=ts,
        mode="default",
        override=ov,
    )

    rcs = list(r.policy.reason_codes)
    mk = _marker(rcs)

    assert rcs[0] == mk, f"Marker MUST be first. mk={mk} rcs={rcs}"
    assert rcs.count(mk) == 1, f"Marker MUST appear exactly once. mk={mk} rcs={rcs}"