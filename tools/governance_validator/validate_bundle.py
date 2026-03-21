from __future__ import annotations

from dataclasses import is_dataclass
from typing import Any, Dict, List, Optional, Tuple

from tools.governance_validator.result_contract import (
    Decision,
    FailedStage,
    Severity,
    Violation,
    ValidationResult,
)

# ---- policy defaults
DEFAULT_SCHEMA_SET_REF = "docs/schemas/v1"

# ---- event types
EV_RUN_START = "RUN_START"
EV_TRANSITION = "TRANSITION"
EV_RATIFICATION = "RATIFICATION_RECORD"


# =============================================================================
# Bundle normalization
# =============================================================================
def _as_records_and_meta(bundle_like: Any) -> Tuple[List[Dict[str, Any]], str]:
    """
    Normalize incoming bundle into (records, schema_set_ref).

    Accepts:
      - EvidenceBundle-like object with .records and optional .schema_set_ref
      - list[dict]  (fixtures)
      - dict with {"records": [...], "schema_set_ref": "..."}
      - dict (single record) -> [dict]
    """
    schema_set_ref = DEFAULT_SCHEMA_SET_REF

    # 1) EvidenceBundle / object input (dataclass or plain object)
    if hasattr(bundle_like, "records"):
        try:
            recs = getattr(bundle_like, "records")
            ssr = getattr(bundle_like, "schema_set_ref", None)
            if isinstance(ssr, str) and ssr:
                schema_set_ref = ssr

            if isinstance(recs, list):
                return [r for r in recs if isinstance(r, dict)], schema_set_ref
            if isinstance(recs, dict):
                return [recs], schema_set_ref
            return [], schema_set_ref
        except Exception:
            return [], schema_set_ref

    # 2) dict-wrapped bundle
    if isinstance(bundle_like, dict):
        ssr = bundle_like.get("schema_set_ref")
        if isinstance(ssr, str) and ssr:
            schema_set_ref = ssr

        if "records" in bundle_like:
            recs = bundle_like["records"]
            if isinstance(recs, list):
                return [r for r in recs if isinstance(r, dict)], schema_set_ref
            if isinstance(recs, dict):
                return [recs], schema_set_ref
            return [], schema_set_ref

        # single record dict
        return [bundle_like], schema_set_ref

    # 3) list of records
    if isinstance(bundle_like, list):
        return [r for r in bundle_like if isinstance(r, dict)], schema_set_ref

    return [], schema_set_ref


# =============================================================================
# Violation builder (contract-compatible)
# =============================================================================
def _supports_field(obj: Any, field: str) -> bool:
    """
    True if dataclass has field, or class __init__ likely accepts it.
    We keep it conservative to avoid raising TypeError.
    """
    try:
        if is_dataclass(obj):
            return field in getattr(obj, "__dataclass_fields__", {})
    except Exception:
        pass
    # For classes, best-effort: assume not supported unless dataclass says so.
    return False


def _mk_violation(
    *,
    code: str,
    severity: Severity,
    message: str,
    rule_id: Optional[str] = None,
    evidence_id: Optional[str] = None,
    refs: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Violation:
    """
    Create Violation while staying compatible with both contracts:
      - older: Violation(..., refs=...)
      - newer: Violation(..., refs=..., context=...)
    """
    base_kwargs: Dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
        "rule_id": rule_id,
        "evidence_id": evidence_id,
        "refs": refs or {},
    }

    # If Violation contract has 'context', include it.
    # If not, fold context into refs to keep audit info.
    if _supports_field(Violation, "context"):
        base_kwargs["context"] = context or {}
    else:
        if context:
            # preserve context even on older contract
            base_kwargs["refs"] = {**(refs or {}), **{"context": context}}

    return Violation(**base_kwargs)


def _is_blocking(v: Violation) -> bool:
    return v.severity in (Severity.BLOCKING, Severity.CRITICAL)


# =============================================================================
# Extractors
# =============================================================================
def _extract_version_bindings(records: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    GSR-000: version bindings must exist.
    Scan records and return first complete triple found.
    """
    for r in records:
        s = r.get("semantic_ruleset_version")
        c = r.get("canonicalizer_profile_version")
        p = r.get("cryptographic_policy_version")
        if s and c and p:
            return str(s), str(c), str(p)
    return None, None, None


def _extract_crypto_annex(records: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    GSR-051: crypto annex envelope must exist.
    Scan records and return first complete set found.
    """
    for r in records:
        alg = r.get("sig_alg")
        signer = r.get("signer_id")
        key_ref = r.get("key_ref")
        sig = r.get("signature_value")
        if alg and signer and key_ref and sig:
            return str(alg), str(signer), str(key_ref), str(sig)
    return None, None, None, None


# =============================================================================
# Checks
# =============================================================================
def _check_minimal_record_shape(records: List[Dict[str, Any]]) -> List[Violation]:
    v: List[Violation] = []
    if not records:
        v.append(
            _mk_violation(
                code="SCHEMA_EMPTY_RECORDS",
                severity=Severity.CRITICAL,
                message="bundle has no records",
                rule_id="GSR-001",
            )
        )
        return v

    for i, r in enumerate(records):
        missing = [k for k in ("event_type", "trace_id", "ts_utc") if k not in r]
        if missing:
            v.append(
                _mk_violation(
                    code="L1_MISSING_CORE_FIELDS",
                    severity=Severity.CRITICAL,
                    message=f"record missing required core fields: {missing}",
                    rule_id="GSR-010",
                    context={"record_index": i, "missing": missing, "event_type": r.get("event_type")},
                )
            )
    return v


def _check_semantic_minimal(records: List[Dict[str, Any]]) -> List[Violation]:
    """
    Minimal semantic checks:
      - If there is a TRANSITION to S2_REHEARSAL_PROVEN, payload must contain rehearsal_id, proof_hash.
      - If RATIFICATION_RECORD exists, must contain >=2 approvals with status APPROVE.
    """
    v: List[Violation] = []

    # S2 payload check
    for i, r in enumerate(records):
        if r.get("event_type") == EV_TRANSITION and r.get("to_state") == "S2_REHEARSAL_PROVEN":
            payload = r.get("payload")
            if not isinstance(payload, dict):
                v.append(
                    _mk_violation(
                        code="L3_PAYLOAD_REQUIRED",
                        severity=Severity.CRITICAL,
                        message="payload is required for transition to S2_REHEARSAL_PROVEN",
                        rule_id="L3-001",
                        context={"record_index": i, "to_state": "S2_REHEARSAL_PROVEN"},
                    )
                )
                continue

            for k in ("rehearsal_id", "proof_hash"):
                if k not in payload:
                    v.append(
                        _mk_violation(
                            code="L3_PAYLOAD_MISSING_FIELD",
                            severity=Severity.CRITICAL,
                            message=f"payload missing required key: {k}",
                            rule_id="L3-002",
                            context={"record_index": i, "missing_key": k, "to_state": "S2_REHEARSAL_PROVEN"},
                        )
                    )

    # Ratification quorum check (if present)
    for i, r in enumerate(records):
        if r.get("event_type") == EV_RATIFICATION:
            approvals = r.get("approvals")
            if not isinstance(approvals, list):
                v.append(
                    _mk_violation(
                        code="GSR_QUORUM_INVALID",
                        severity=Severity.CRITICAL,
                        message="ratification approvals must be a list",
                        rule_id="GSR-020",
                        context={"record_index": i},
                    )
                )
                continue

            ok = [
                a
                for a in approvals
                if isinstance(a, dict) and a.get("status") == "APPROVE" and a.get("reviewer_id")
            ]
            if len(ok) < 2:
                v.append(
                    _mk_violation(
                        code="GSR_QUORUM_NOT_MET",
                        severity=Severity.CRITICAL,
                        message="ratification quorum not met (need >=2 APPROVE)",
                        rule_id="GSR-030",
                        context={"record_index": i, "approve_count": len(ok)},
                    )
                )

    return v


# =============================================================================
# Main
# =============================================================================
def validate_bundle(bundle_like: Any) -> ValidationResult:
    """
    Contract:
      - Returns ValidationResult (Decision.ALLOW or Decision.FAIL_CLOSED)
      - Accepts EvidenceBundle-like object, list[dict] fixtures, or dict-wrapped bundles.
    """
    records, schema_set_ref = _as_records_and_meta(bundle_like)

    violations: List[Violation] = []

    # ---- Stage: SCHEMA (minimal shape)
    violations.extend(_check_minimal_record_shape(records))
    if any(_is_blocking(x) for x in violations):
        return ValidationResult(
            decision=Decision.FAIL_CLOSED,
            fail_closed=True,
            failed_stage=FailedStage.SCHEMA,
            violations=violations,
            schema_set_ref=schema_set_ref,
        )

    # ---- Stage: SEMANTIC bindings (GSR-000)
    semantic_ruleset_version, canonicalizer_profile_version, cryptographic_policy_version = _extract_version_bindings(records)
    if not (semantic_ruleset_version and canonicalizer_profile_version and cryptographic_policy_version):
        violations.append(
            _mk_violation(
                code="GSR_000_VERSION_BINDING_MISSING",
                severity=Severity.CRITICAL,
                message="version bindings missing (semantic/canonicalizer/crypto policy)",
                rule_id="GSR-000",
                context={
                    "semantic_ruleset_version": semantic_ruleset_version,
                    "canonicalizer_profile_version": canonicalizer_profile_version,
                    "cryptographic_policy_version": cryptographic_policy_version,
                },
            )
        )
        return ValidationResult(
            decision=Decision.FAIL_CLOSED,
            fail_closed=True,
            failed_stage=FailedStage.SEMANTIC,
            violations=violations,
            schema_set_ref=schema_set_ref,
            semantic_ruleset_version=semantic_ruleset_version,
            canonicalizer_profile_version=canonicalizer_profile_version,
            cryptographic_policy_version=cryptographic_policy_version,
        )

    # ---- Stage: CRYPTO annex (GSR-051)
    sig_alg, signer_id, key_ref, signature_value = _extract_crypto_annex(records)
    if not (sig_alg and signer_id and key_ref and signature_value):
        violations.append(
            _mk_violation(
                code="GSR_051_CRYPTO_ANNEX_MISSING",
                severity=Severity.CRITICAL,
                message="crypto annex fields missing (sig_alg/signer_id/key_ref/signature_value)",
                rule_id="GSR-051",
                context={
                    "sig_alg": sig_alg,
                    "signer_id": signer_id,
                    "key_ref": key_ref,
                    "signature_value_present": bool(signature_value),
                },
            )
        )
        return ValidationResult(
            decision=Decision.FAIL_CLOSED,
            fail_closed=True,
            failed_stage=FailedStage.CRYPTO,
            violations=violations,
            schema_set_ref=schema_set_ref,
            semantic_ruleset_version=semantic_ruleset_version,
            canonicalizer_profile_version=canonicalizer_profile_version,
            cryptographic_policy_version=cryptographic_policy_version,
        )

    # ---- Stage: SEMANTIC minimal rules (payload + quorum if exists)
    violations.extend(_check_semantic_minimal(records))
    if any(_is_blocking(x) for x in violations):
        return ValidationResult(
            decision=Decision.FAIL_CLOSED,
            fail_closed=True,
            failed_stage=FailedStage.SEMANTIC,
            violations=violations,
            schema_set_ref=schema_set_ref,
            semantic_ruleset_version=semantic_ruleset_version,
            canonicalizer_profile_version=canonicalizer_profile_version,
            cryptographic_policy_version=cryptographic_policy_version,
        )

    # ---- PASS (Golden path)
    return ValidationResult(
        decision=Decision.ALLOW,
        fail_closed=False,
        failed_stage=FailedStage.NONE,
        violations=violations,  # WARNING/INFO only (none for now)
        schema_set_ref=schema_set_ref,
        semantic_ruleset_version=semantic_ruleset_version,
        canonicalizer_profile_version=canonicalizer_profile_version,
        cryptographic_policy_version=cryptographic_policy_version,
    )
