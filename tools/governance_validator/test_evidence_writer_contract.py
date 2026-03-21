from __future__ import annotations

import json
import hashlib
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

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
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _as_result_dict(result: ValidationResult) -> Dict[str, Any]:
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
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle_path = Path(bundle_path)

    # ✅ 테스트 계약: missing -> RuntimeError + message contains "bundle not found" or "failed reading bundle"
    if not bundle_path.exists():
        raise RuntimeError(f"bundle not found: {bundle_path}")

    # ✅ POSIX 고정
    bundle_path_posix = bundle_path.resolve().as_posix()

    # ✅ 파일 sha256
    try:
        bundle_sha256 = _sha256_file_hex(bundle_path)
    except Exception as ex:
        raise RuntimeError(f"failed reading bundle: {bundle_path}") from ex

    # result dict
    result_dict = _as_result_dict(validation_result)

    violations = result_dict.get("violations", [])
    violations_count = len(violations) if isinstance(violations, list) else 0

    summary = {
        "decision": result_dict.get("decision", "UNKNOWN"),
        "fail_closed": bool(result_dict.get("fail_closed", False)),
        "failed_stage": result_dict.get("failed_stage", "NONE"),
        "violations_count": violations_count,
    }

    # ✅ 테스트 계약: created_at_utc 는 top-level에도 있어야 함
    created_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

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

    chain = {
        "prev_hash": prev_chain_hash or "GENESIS",
        "this_hash": None,  # ✅ 테스트 계약: 해시 계산 시 None 상태
    }

    # ✅ 테스트 계약: evidence_type / evidence_version 키 이름이 고정
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

    # --- compute this_hash WITHOUT self-reference ---
    # ✅ 테스트 계약: canonicalize 전에 this_hash는 None
    payload_for_hash = json.loads(json.dumps(payload, ensure_ascii=False))
    payload_for_hash["chain"]["this_hash"] = None

    this_hash = _sha256_hex(_canonical_bytes(payload_for_hash))

    # 저장 payload에는 문자열 this_hash를 채움
    payload["chain"]["this_hash"] = this_hash

    decision = str(summary["decision"])
    ts = _utc_now_compact()
    out_path = out_dir / f"validation_{decision}_{ts}_{this_hash[:12]}.json"

    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if compute_file_sha256:
        _ = _sha256_file_hex(out_path)

    return out_path
