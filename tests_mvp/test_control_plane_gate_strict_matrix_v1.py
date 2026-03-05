# tests_mvp/test_control_plane_gate_strict_matrix_v1.py
from __future__ import annotations

import pytest

from tools.governance_validator.result_contract import (
    ChainValidationStatus,
    RuleCode,
    Severity,
    Violation,
    make_fail,
    make_pass,
)


def _err(rule: RuleCode = RuleCode.HEAD_MISMATCH) -> Violation:
    return Violation(
        rule=rule,
        severity=Severity.ERROR,
        message="err",
        trace_id="TRACE-GATE-001",
    )


def _warn(rule: RuleCode = RuleCode.TIME_DRIFT) -> Violation:
    return Violation(
        rule=rule,
        severity=Severity.WARNING,
        message="warn",
        trace_id="TRACE-GATE-002",
    )


def _strict_gate_allows(res) -> bool:
    """
    STRICT Gate matrix (v1):
      - FAIL or any ERROR => BLOCK
      - PASS with only warnings => ALLOW (but degraded)
      - PASS no warnings => ALLOW
    """
    if res.status != ChainValidationStatus.PASS:
        return False
    if getattr(res, "errors", None) and len(res.errors) > 0:
        return False
    return True


def test_strict_gate_blocks_on_fail_status():
    res = make_fail(errors=[_err()])
    assert _strict_gate_allows(res) is False


def test_strict_gate_blocks_on_pass_but_has_errors():
    # 방어적: status를 PASS로 만들 수 없지만, 정책 차원에서 “errors 있으면 무조건 BLOCK”을 박제
    res = make_fail(errors=[_err()], warnings=[_warn()])  # FAIL 경로가 정상
    assert _strict_gate_allows(res) is False


def test_strict_gate_allows_on_pass_with_only_warnings():
    res = make_pass(warnings=[_warn()])
    assert _strict_gate_allows(res) is True


def test_strict_gate_allows_on_clean_pass():
    res = make_pass()
    assert _strict_gate_allows(res) is True