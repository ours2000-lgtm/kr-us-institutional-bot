from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

# 너의 프로젝트 구조에 맞춰 import 유지
from tools.governance_validator.result_contract import ValidationResult


# -----------------------------
# Canonical / Crypto helpers
# -----------------------------
def _canonical_bytes(obj: Any) -> bytes:
    """
    Canonical JSON bytes for hashing.
    - sort_keys=True
    - separators=(",", ":")
    - ensure_ascii=False  (Korean-safe)
    """
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_hex(data: Union[bytes, bytearray]) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_now_compact() -> str:
    # 파일명에 쓰기 좋은 UTC 타임스탬프
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _as_result_dict(result: ValidationResult) -> Dict[str, Any]:
    """
    ValidationResult -> dict
    - 가장 우선: result.to_dict()
    - 그 다음: dataclasses.asdict(result)
    """
    if hasattr(result, "to_dict"):
        return result.to_dict()  # type: ignore[no-any-return]
    return asdict(result)  # type: ignore[no-any-return]


# -----------------------------
# Public API
# -----------------------------
def write_validation_evidence(
    *,
    out_dir: Path,
    bundle_path: Path,
    validation_result: ValidationResult,
    prev_chain_hash: Optional[str] = None,
    node_id: Optional[str] = None,
    git_commit: Optional[str] = None,
    compute_file_sha256: bool = True,
) -> Path:
    """
    Test-contract compliant evidence writer.

    Satisfies tests/test_evidence_writer.py:
    - payload["evidence_type"] == "GOV_VALIDATION_EVIDENCE"
    - payload["evidence_version"] == "EVIDENCE_v1"
    - top-level "created_at_utc" exists
    - missing bundle raises RuntimeError with message containing "bundle not found" or "failed reading bundle"
    - chain.this_hash is computed from canonical bytes of payload where chain.this_hash is None
    - inputs.bundle_path stored as POSIX
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle_path = Path(bundle_path)

    # --- missing bundle -> RuntimeError (test expects RuntimeError) ---
    if not bundle_path.exists():
        raise RuntimeError(f"bundle not found: {bundle_path}")

    # --- POSIX-stable path ---
    bundle_path_posix = bundle_path.resolve().as_posix()

    # --- file sha256 binding (clear error on read fail) ---
    try:
        bundle_sha256 = _sha256_file_hex(bundle_path)
    except Exception as ex:
        raise RuntimeError(f"failed reading bundle: {bundle_path}") from ex

    # --- result dict ---
    result_dict = _as_result_dict(validation_result)

    violations = result_dict.get("violations", [])
    violations_count = len(violations) if isinstance(violations, list) else 0

    summary = {
        "decision": result_dict.get("decision", "UNKNOWN"),
        "fail_closed": bool(result_dict.get("fail_closed", False)),
        "failed_stage": result_dict.get("failed_stage", "NONE"),
        "violations_count": violations_count,
    }

    # --- created_at_utc required at top-level ---
    created_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # --- meta (must exist, created_at_utc also included here for convenience) ---
    meta: Dict[str, Any] = {
        "created_at_utc": created_at_utc,
    }
    if node_id is not None:
        meta["node_id"] = node_id
    if git_commit is not None:
        meta["git_commit"] = git_commit

    inputs = {
        "bundle_path": bundle_path_posix,
        "bundle_sha256": bundle_sha256,
    }

    # chain: hash 계산 시 this_hash는 None이어야 함 (test contract)
    chain: Dict[str, Any] = {
        "prev_hash": prev_chain_hash or "GENESIS",
        "this_hash": None,
    }

    # --- payload (test-required keys) ---
    payload: Dict[str, Any] = {
        "evidence_type": "GOV_VALIDATION_EVIDENCE",
        "evidence_version": "EVIDENCE_v1",
        "created_at_utc": created_at_utc,
        "meta": meta,
        "inputs": inputs,
        "summary": summary,
        "result": result_dict,
        "chain": chain,
    }

    # --- compute this_hash (self-reference excluded via None contract) ---
    # make deep copy safely via json roundtrip (no non-JSON objects expected here)
    payload_for_hash: Dict[str, Any] = json.loads(json.dumps(payload, ensure_ascii=False))
    payload_for_hash["chain"]["this_hash"] = None

    this_hash = _sha256_hex(_canonical_bytes(payload_for_hash))
    payload["chain"]["this_hash"] = this_hash

    # filename policy
    decision = str(summary["decision"])
    ts = _utc_now_compact()
    out_path = out_dir / f"validation_{decision}_{ts}_{this_hash[:12]}.json"

    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # optional integrity check
    if compute_file_sha256:
        _ = _sha256_file_hex(out_path)

    return out_path
