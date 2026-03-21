from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.governance_validator.evidence_writer import write_validation_evidence
from tools.governance_validator.result_contract import (
    Decision,
    FailedStage,
    Severity,
    Violation,
    ValidationResult,
)
from tests._helpers import canonical_bytes, is_hex_64, sha256_file_hex, sha256_hex


def _mk_allow_result() -> ValidationResult:
    return ValidationResult(
        decision=Decision.ALLOW,
        fail_closed=False,
        failed_stage=FailedStage.NONE,
        violations=[],
        schema_set_ref="docs/schemas/v1",
        semantic_ruleset_version="GOV_SEMANTIC_RULES_v1",
        canonicalizer_profile_version="CANONICALIZER_v1",
        cryptographic_policy_version="CRYPTO_POLICY_v1",
        validator_version="v0.1",
    )


def _mk_fail_closed_result() -> ValidationResult:
    v = Violation(
        code="GSR_000_VERSION_BINDING_MISSING",
        severity=Severity.CRITICAL,
        message="version bindings missing",
        rule_id="GSR-000",
        evidence_id=None,
        refs={},
        context={"hint": "fixture"},
    )
    return ValidationResult(
        decision=Decision.FAIL_CLOSED,
        fail_closed=True,
        failed_stage=FailedStage.SEMANTIC,
        violations=[v],
        schema_set_ref="docs/schemas/v1",
        semantic_ruleset_version=None,
        canonicalizer_profile_version=None,
        cryptographic_policy_version=None,
        validator_version="v0.1",
    )


@pytest.mark.parametrize("prev_hash_expected", ["GENESIS", "PREV_HASH_DEMO_001"])
def test_evidence_writer_contract_allow_path(tmp_path: Path, prev_hash_expected: str):
    # bundle file (any json)
    bundle_path = tmp_path / "trace_ok_v1_signed.json"
    bundle_path.write_text(json.dumps([{"hello": "world"}], ensure_ascii=False, indent=2), encoding="utf-8")

    out_dir = tmp_path / "evidence"
    result = _mk_allow_result()

    out_path = write_validation_evidence(
        out_dir=out_dir,
        bundle_path=bundle_path,
        validation_result=result,
        prev_chain_hash=None if prev_hash_expected == "GENESIS" else prev_hash_expected,
        node_id="TEST_NODE",
        git_commit="deadbeef",
    )

    payload = json.loads(out_path.read_text(encoding="utf-8"))

    # ---- top-level contract
    assert payload.get("kind") == "GOV_VALIDATION_EVIDENCE"
    assert payload.get("artifact_type") == "GOV_VALIDATION_EVIDENCE"
    for k in ("inputs", "summary", "result", "chain", "meta"):
        assert k in payload, f"[contract] top-level key missing: {k}"

    # ---- inputs binding
    inputs = payload["inputs"]
    assert isinstance(inputs, dict)
    assert "bundle_path" in inputs, "[contract] inputs.bundle_path missing"
    assert "bundle_sha256" in inputs, "[contract] inputs.bundle_sha256 missing"

    got_path = inputs["bundle_path"]
    expected_suffix = bundle_path.as_posix().replace("\\", "/")
    assert isinstance(got_path, str), "[contract] inputs.bundle_path must be str"
    assert got_path.endswith(expected_suffix), f"[contract] bundle_path suffix mismatch: got={got_path}, expected_suffix={expected_suffix}"

    assert inputs["bundle_sha256"] == sha256_file_hex(bundle_path)

    # ---- summary contract
    summary = payload["summary"]
    assert isinstance(summary, dict)
    for k in ("decision", "fail_closed", "failed_stage", "violations_count"):
        assert k in summary, f"[contract] summary.{k} missing"
    assert summary["decision"] in ("ALLOW", "FAIL_CLOSED", "DENY", "UNKNOWN")
    assert summary["decision"] == "ALLOW"
    assert summary["fail_closed"] is False

    # ---- chain contract
    chain = payload["chain"]
    assert isinstance(chain, dict)
    assert chain.get("prev_hash") == prev_hash_expected
    this_hash = chain.get("this_hash")
    assert isinstance(this_hash, str)
    assert is_hex_64(this_hash), f"[contract] chain.this_hash must be 64-char hex: got={this_hash}"

    # ---- self-hash rule (exclude chain.this_hash itself)
    payload_for_hash = json.loads(json.dumps(payload, ensure_ascii=False))
    payload_for_hash.setdefault("chain", {})
    payload_for_hash["chain"]["this_hash"] = ""
    computed = sha256_hex(canonical_bytes(payload_for_hash))
    assert this_hash == computed, "[contract] chain.this_hash must match computed sha256(canonical_payload_without_self_hash)"

    # ---- filename policy
    assert out_path.parent == out_dir
    assert out_path.suffix == ".json"
    assert out_path.name.startswith("validation_ALLOW_")
    assert this_hash[:12] in out_path.name


def test_evidence_writer_contract_fail_closed_path(tmp_path: Path):
    bundle_path = tmp_path / "bad_bundle.json"
    bundle_path.write_text(json.dumps({"bad": True}, ensure_ascii=False), encoding="utf-8")

    out_dir = tmp_path / "evidence"
    result = _mk_fail_closed_result()

    out_path = write_validation_evidence(
        out_dir=out_dir,
        bundle_path=bundle_path,
        validation_result=result,
        prev_chain_hash="GENESIS",
    )
    payload = json.loads(out_path.read_text(encoding="utf-8"))

    summary = payload["summary"]
    assert summary["decision"] == "FAIL_CLOSED"
    assert summary["fail_closed"] is True
    assert isinstance(summary["violations_count"], int)
    assert summary["violations_count"] >= 1

    # self-hash rule still holds
    this_hash = payload["chain"]["this_hash"]
    payload_for_hash = json.loads(json.dumps(payload, ensure_ascii=False))
    payload_for_hash["chain"]["this_hash"] = ""
    computed = sha256_hex(canonical_bytes(payload_for_hash))
    assert this_hash == computed


def test_evidence_writer_raises_clear_error_when_bundle_missing(tmp_path: Path):
    out_dir = tmp_path / "evidence"
    missing = tmp_path / "no_such_bundle.json"

    with pytest.raises(FileNotFoundError):
        write_validation_evidence(
            out_dir=out_dir,
            bundle_path=missing,
            validation_result=_mk_allow_result(),
        )
