from __future__ import annotations

from typing import Dict, List, Optional, Set

from ..io import EvidenceBundle
from ..result_contract import Severity, Violation


REQUIRED_BINDINGS = [
    "semantic_ruleset_version",
    "canonicalizer_profile_version",
    "cryptographic_policy_version",
]


def _collect_binding_values(records: List[Dict]) -> Dict[str, Set[Optional[str]]]:
    out: Dict[str, Set[Optional[str]]] = {k: set() for k in REQUIRED_BINDINGS}
    for r in records:
        for k in REQUIRED_BINDINGS:
            out[k].add(r.get(k))
    return out


def group_by_evidence_type(records: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Future-proof hook:
    Next iterations (GSR-010/011/020/...) will often be evidence_type-specific.
    This grouping keeps the semantic engine clean and deterministic.
    """
    by_type: Dict[str, List[Dict]] = {}
    for r in records:
        t = r.get("evidence_type") or r.get("record_type") or "UNKNOWN"
        by_type.setdefault(str(t), []).append(r)
    return by_type


def semantic_validate_all(bundle: EvidenceBundle) -> List[Violation]:
    records = bundle.records
    v: List[Violation] = []

    # Prepare type buckets for future GSR expansion
    _by_type = group_by_evidence_type(records)

    # GSR-000: all eligible for canonical decisions must satisfy version binding
    bindings = _collect_binding_values(records)
    for k, values in bindings.items():
        if None in values or "" in values:
            v.append(
                Violation(
                    code="GSR_000_MISSING_VERSION_BINDING",
                    severity=Severity.BLOCKING,
                    message=(
                        f"Evidence missing required binding field: {k}. "
                        "Evidence that does not satisfy GSR-000 SHALL NOT be eligible for any canonical decision."
                    ),
                    rule_id="GSR-000",
                    refs={"field": k},
                )
            )

    # 동일성(전부 같은 버전이어야) - v0.1: BLOCKING
    for k, values in bindings.items():
        non_null = {x for x in values if x not in (None, "")}
        if len(non_null) > 1:
            v.append(
                Violation(
                    code="GSR_000_VERSION_BINDING_MISMATCH",
                    severity=Severity.BLOCKING,
                    message=f"Version binding mismatch across records for {k}: {sorted(list(non_null))}",
                    rule_id="GSR-000",
                    refs={"field": k},
                )
            )

    # GSR-030/031: Evidence linkage 필드 이름 명시(스키마와 규칙의 1:1)
    for r in records:
        payload = r.get("payload", {})
        if isinstance(payload, dict):
            if "evidence_refs" in payload and not isinstance(payload.get("evidence_refs"), list):
                v.append(
                    Violation(
                        code="GSR_030_EVIDENCE_REFS_NOT_ARRAY",
                        severity=Severity.CRITICAL,
                        message="payload.evidence_refs must be an array when present",
                        rule_id="GSR-030",
                        evidence_id=r.get("evidence_id"),
                    )
                )
            if "evidence_pack_ref" in payload and not isinstance(payload.get("evidence_pack_ref"), str):
                v.append(
                    Violation(
                        code="GSR_031_EVIDENCE_PACK_REF_NOT_STRING",
                        severity=Severity.CRITICAL,
                        message="payload.evidence_pack_ref must be a string when present",
                        rule_id="GSR-031",
                        evidence_id=r.get("evidence_id"),
                    )
                )

    # NOTE: _by_type is intentionally unused in v0.1 beyond construction.
    # It is a stable extension point for GSR-010/011/020/040.. etc.

    return v
