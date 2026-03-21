from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..io import EvidenceBundle
from ..result_contract import Severity, Violation


# Golden Fixture LOCK(v1) 기준: 최소 Annex envelope 필드 존재를 요구
_REQUIRED_ANNEX_FIELDS = ("sig_alg", "signer_id", "key_ref", "signature_value")


def _mk_violation(
    *,
    code: str,
    severity: Severity,
    message: str,
    context: Optional[Dict[str, Any]] = None,
) -> Violation:
    return Violation(
        code=code,
        severity=severity,
        message=message,
        rule_id="GSR-051",
        refs={},
        context=context or {},
    )


def crypto_validate_all(bundle: EvidenceBundle) -> List[Violation]:
    """
    Stage 3: Crypto Annex binding

    v1 policy (LOCK-aligned):
      - At least one record MUST carry Annex envelope fields:
          sig_alg, signer_id, key_ref, signature_value
      - Missing or empty fields => FAIL_CLOSED (BLOCKING)
      - Actual signature cryptographic verification is deferred (Annex v2+).
    """
    records = bundle.records or []
    if not isinstance(records, list):
        # defensive: should not happen if validate_bundle normalized
        return [
            _mk_violation(
                code="CRYPTO_RECORDS_SHAPE_INVALID",
                severity=Severity.BLOCKING,
                message="records must be a list of dicts for crypto validation",
                context={"records_type": str(type(records))},
            )
        ]

    # find first record that contains any annex-related field
    candidate: Optional[Dict[str, Any]] = None
    for r in records:
        if isinstance(r, dict) and any(k in r for k in _REQUIRED_ANNEX_FIELDS):
            candidate = r
            break

    if candidate is None:
        return [
            _mk_violation(
                code="CRYPTO_ANNEX_MISSING",
                severity=Severity.BLOCKING,
                message="Crypto Annex envelope is missing (no record carries annex fields).",
                context={"required_fields": list(_REQUIRED_ANNEX_FIELDS)},
            )
        ]

    missing = [k for k in _REQUIRED_ANNEX_FIELDS if k not in candidate]
    if missing:
        return [
            _mk_violation(
                code="CRYPTO_ANNEX_FIELDS_MISSING",
                severity=Severity.BLOCKING,
                message=f"Crypto Annex envelope missing fields: {missing}",
                context={"missing": missing, "required_fields": list(_REQUIRED_ANNEX_FIELDS)},
            )
        ]

    # Empty string check (struct-level validity)
    empty = [k for k in _REQUIRED_ANNEX_FIELDS if str(candidate.get(k, "")).strip() == ""]
    if empty:
        return [
            _mk_violation(
                code="CRYPTO_ANNEX_FIELDS_EMPTY",
                severity=Severity.BLOCKING,
                message=f"Crypto Annex envelope has empty fields: {empty}",
                context={"empty": empty},
            )
        ]

    # Optional: soft sanity checks (WARNING only)
    v: List[Violation] = []
    sig_alg = str(candidate.get("sig_alg", "")).upper()
    if sig_alg not in ("ED25519", "SECP256K1", "RSA-PSS", "RSA_PSS"):
        v.append(
            _mk_violation(
                code="CRYPTO_SIG_ALG_UNKNOWN",
                severity=Severity.WARNING,
                message=f"Unknown sig_alg '{candidate.get('sig_alg')}', allowed in v1 as WARNING.",
                context={"sig_alg": candidate.get("sig_alg")},
            )
        )

    return v
