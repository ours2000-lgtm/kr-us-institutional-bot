# KR_US_INSTITUTIONAL_BOT/tests/test_evidence_writer.py
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from tools.governance_validator import validate_bundle
from tools.governance_validator.evidence_writer import write_validation_evidence


FIXTURE_OK = Path("tests/fixtures/traces/trace_ok_v1_signed.json")


def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _canonical_bytes_for_chain(payload: dict) -> bytes:
    """
    evidence_writer.py에서 this_hash를 계산할 때 쓰는 canonical JSON bytes와 동일 규칙.
    주의: writer는 chain.this_hash를 None 상태로 canonicalize한 후 해시를 계산한다.
    """
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def test_evidence_writer_creates_artifact_and_chain_is_valid(tmp_path: Path):
    # --- arrange
    assert FIXTURE_OK.exists(), f"Missing fixture: {FIXTURE_OK}"

    # fixture는 "bundle_path" 역할(입력 bytes 해시 바인딩)
    bundle_bytes = FIXTURE_OK.read_bytes()
    bundle_sha256 = _sha256_hex(bundle_bytes)

    # validate_bundle은 EvidenceBundle 객체를 받는다.
    # (io.py의 EvidenceBundle 정의에 맞춰 생성)
    from tools.governance_validator.io import EvidenceBundle  # local import for clarity

    records = json.loads(FIXTURE_OK.read_text(encoding="utf-8"))
    bundle = EvidenceBundle(records=records, schema_set_ref="docs/schemas/v1")

    # validation_result
    result = validate_bundle(bundle)

    # --- act
    out_path = write_validation_evidence(
        out_dir=tmp_path,
        bundle_path=FIXTURE_OK,
        validation_result=result,
        node_id="TEST-NODE",
        git_commit="TEST-COMMIT",
    )

    # --- assert (file created)
    assert out_path.exists(), f"Evidence file not created: {out_path}"
    payload = json.loads(out_path.read_text(encoding="utf-8"))

    # --- assert (top-level required keys)
    assert payload.get("evidence_type") == "GOV_VALIDATION_EVIDENCE"
    assert payload.get("evidence_version") == "EVIDENCE_v1"
    assert "created_at_utc" in payload
    assert "meta" in payload
    assert "inputs" in payload
    assert "summary" in payload
    assert "result" in payload
    assert "chain" in payload

    # --- assert (inputs binding)
    assert payload["inputs"]["bundle_path"].endswith(str(FIXTURE_OK).replace("\\", "/")) or payload["inputs"]["bundle_path"].endswith(str(FIXTURE_OK))
    assert payload["inputs"]["bundle_sha256"] == bundle_sha256

    # --- assert (summary contract)
    summary = payload["summary"]
    for k in ("decision", "fail_closed", "failed_stage", "violations_count"):
        assert k in summary

    assert summary["decision"] in ("ALLOW", "FAIL_CLOSED", "DENY", "UNKNOWN")
    # Golden fixture는 ALLOW여야 함 (지금 trace_ok_v1_signed.json은 ALLOW로 설계)
    assert summary["decision"] == "ALLOW"
    assert summary["fail_closed"] is False

    # --- assert (chain contract)
    chain = payload["chain"]
    assert "prev_hash" in chain
    assert "this_hash" in chain
    assert isinstance(chain["this_hash"], str) and len(chain["this_hash"]) == 64
    assert chain["prev_hash"] in ("GENESIS",) or isinstance(chain["prev_hash"], str)

    # --- assert (this_hash integrity)
    # writer는 "chain.this_hash = None" 상태에서 canonical bytes를 만들고 sha256을 계산한 뒤,
    # 그 값을 chain.this_hash에 다시 채운다.
    payload_for_hash = copy.deepcopy(payload)
    payload_for_hash["chain"]["this_hash"] = None

    canonical = _canonical_bytes_for_chain(payload_for_hash)
    expected_this_hash = _sha256_hex(canonical)

    assert payload["chain"]["this_hash"] == expected_this_hash


def test_evidence_writer_raises_clear_error_when_bundle_missing(tmp_path: Path):
    missing = tmp_path / "no_such_bundle.json"

    # validation_result는 어떤 객체든 들어갈 수 있지만, 여기선 최소 형태로 충분
    class DummyResult:
        decision = "ALLOW"
        fail_closed = False
        failed_stage = "NONE"
        violations = []

    with pytest.raises(RuntimeError) as e:
        write_validation_evidence(
            out_dir=tmp_path,
            bundle_path=missing,
            validation_result=DummyResult(),
        )

    msg = str(e.value)
    assert "bundle not found" in msg or "failed reading bundle" in msg
