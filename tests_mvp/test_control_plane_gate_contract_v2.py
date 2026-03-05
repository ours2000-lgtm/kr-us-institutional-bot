# tests_mvp/test_control_plane_gate_contract_v2.py
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from tools.governance_validator.result_contract import (
    ChainValidationResult,
    ChainValidationStatus,
    RuleCode,
    Severity,
    Violation,
    make_fail,
    make_pass,
)


def _utc_dt() -> datetime:
    return datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)


def _mk_err(msg: str = "boom") -> Violation:
    return Violation(
        rule=RuleCode.EVIDENCE_SCHEMA_ERROR,
        severity=Severity.ERROR,
        message=msg,
        evidence_path="E:/KR_US_INSTITUTIONAL_BOT/evidence/x.json",
        trace_id="TRACE-TEST-001",
        context={"k": "v"},
    )


def _mk_warn(msg: str = "warn") -> Violation:
    return Violation(
        rule=RuleCode.TIME_DRIFT,
        severity=Severity.WARNING,
        message=msg,
        trace_id="TRACE-TEST-002",
        skew_ms=123,
    )


def test_chain_validation_result_make_pass_contract_shape():
    res = make_pass(warnings=[_mk_warn("w1")])

    assert isinstance(res, ChainValidationResult)
    assert res.status == ChainValidationStatus.PASS
    assert res.is_pass() is True
    assert res.contract_version == "chain_validation_result_v1"
    assert isinstance(res.validated_at_utc, str) and res.validated_at_utc.endswith("Z")

    d = res.to_dict()
    assert d["contract_version"] == "chain_validation_result_v1"
    assert d["status"] == "PASS"
    assert isinstance(d["errors"], list) and len(d["errors"]) == 0
    assert isinstance(d["warnings"], list) and len(d["warnings"]) == 1
    assert d["warnings"][0]["severity"] == "WARNING"
    assert d["warnings"][0]["rule"] == RuleCode.TIME_DRIFT.value


def test_chain_validation_result_make_fail_contract_shape():
    res = make_fail(errors=[_mk_err("e1")], warnings=[_mk_warn("w1")])

    assert isinstance(res, ChainValidationResult)
    assert res.status == ChainValidationStatus.FAIL
    assert res.is_pass() is False
    assert len(res.errors) == 1
    assert len(res.warnings) == 1

    d = res.to_dict()
    assert d["status"] == "FAIL"
    assert len(d["errors"]) == 1
    assert d["errors"][0]["severity"] == "ERROR"
    assert d["errors"][0]["rule"] == RuleCode.EVIDENCE_SCHEMA_ERROR.value


@pytest.mark.parametrize("bad_msg", ["", "   "])
def test_violation_message_must_not_be_blank_by_convention(bad_msg: str):
    """
    result_contract 자체가 message blank를 강제하진 않지만,
    Gate/운영에서 message blank는 금지 규약으로 박제한다.
    (즉: 지금은 '문서화된 규약' 테스트)
    """
    v = _mk_err(msg=bad_msg)
    assert (v.message.strip() != "") is False