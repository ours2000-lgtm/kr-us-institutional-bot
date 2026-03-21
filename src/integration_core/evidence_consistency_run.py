from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from .aggregation import AggregationResult, ConsistencyResult
from .policy import PolicyDecision

Principal = Dict[str, str]  # {"type": "human"|"service", "id": "..."}


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_bytes(obj: Any) -> bytes:
    """
    Hashing specification (v0.4):
    - Python stdlib json
    - sort_keys=True
    - ensure_ascii=False
    - separators=(",", ":")
    - UTF-8 encoding
    """
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class EvidenceConsistencyRun:
    """
    EVID-CONSISTENCY-RUN v0.4

    - core: canonical-minimal fields (hash included)
    - rich_context: debugging/ops snapshot (NOT included in hashes)
    """

    evidence_type: Literal["EVID-CONSISTENCY-RUN"]
    schema_version: str

    # canonical core
    snapshot_id: Optional[str]
    graph_hash: str
    consistency_decision: Literal["PASS", "FAIL"]

    aggregation_grade: Literal["PASS", "WARN", "BLOCK"]
    aggregation_decision_compat: Literal["ALLOW", "BLOCK"]
    violation_count: int
    violation_ids: List[str]

    policy_decision: Literal["ALLOW", "BLOCK"]
    policy_grade: Literal["PASS", "WARN", "BLOCK"]
    reason_codes: List[str]
    policy_ref: str
    policy_version: str
    mode: str

    principal: Principal
    timestamp_utc: str

    inputs_hash: str
    evidence_hash: str

    rich_context: Optional[Dict[str, Any]] = None


def promote_evidence_consistency_run(
    *,
    consistency: ConsistencyResult,
    aggregation: AggregationResult,
    policy: PolicyDecision,
    principal: Principal,
    timestamp_utc: Optional[str] = None,
    schema_version: str = "v0.4",
    rich_context: Optional[Dict[str, Any]] = None,
) -> EvidenceConsistencyRun:
    ts = timestamp_utc or _utc_now_z()

    # ---------
    # Canonical core (hash included)
    # ---------
    core: Dict[str, Any] = {
        "evidence_type": "EVID-CONSISTENCY-RUN",
        "schema_version": schema_version,
        "snapshot_id": consistency.snapshot_id,
        "graph_hash": consistency.graph_hash,
        "consistency_decision": consistency.decision,
        "aggregation_grade": aggregation.grade,
        "aggregation_decision_compat": aggregation.decision,
        "violation_count": aggregation.violation_count,
        "violation_ids": aggregation.violation_ids,
        "policy_decision": policy.decision,
        "policy_grade": policy.grade,
        "reason_codes": list(policy.reason_codes),
        "policy_ref": policy.policy_ref,
        "policy_version": policy.policy_version,
        "mode": policy.mode,
        "principal": principal,
        "timestamp_utc": ts,
    }

    inputs_hash = _sha256_hex(_canonical_bytes(core))

    core_with_inputs = dict(core)
    core_with_inputs["inputs_hash"] = inputs_hash
    evidence_hash = _sha256_hex(_canonical_bytes(core_with_inputs))

    # ---------
    # Rich context (NOT hashed) — safe to expand
    # ---------
    rc: Dict[str, Any] = dict(rich_context or {})
    rc.setdefault("aggregation_summary", aggregation.summary)
    rc.setdefault(
        "consistency",
        {
            "snapshot_id": consistency.snapshot_id,
            "graph_hash": consistency.graph_hash,
            "decision": consistency.decision,
            "violation_count": len(consistency.violations or []),
        },
    )
    rc.setdefault("policy_inputs", policy.inputs)
    rc.setdefault("pipeline_timestamp_utc", ts)

    return EvidenceConsistencyRun(
        evidence_type="EVID-CONSISTENCY-RUN",
        schema_version=schema_version,
        snapshot_id=consistency.snapshot_id,
        graph_hash=consistency.graph_hash,
        consistency_decision=consistency.decision,
        aggregation_grade=aggregation.grade,
        aggregation_decision_compat=aggregation.decision,
        violation_count=aggregation.violation_count,
        violation_ids=aggregation.violation_ids,
        policy_decision=policy.decision,
        policy_grade=policy.grade,
        reason_codes=list(policy.reason_codes),
        policy_ref=policy.policy_ref,
        policy_version=policy.policy_version,
        mode=policy.mode,
        principal=principal,
        timestamp_utc=ts,
        inputs_hash=inputs_hash,
        evidence_hash=evidence_hash,
        rich_context=rc,
    )