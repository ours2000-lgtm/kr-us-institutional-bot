# tests_mvp/test_any_fail_block_policy_gate_v1.py
from __future__ import annotations

import pytest

from tools.control_plane.any_fail_block_policy_v1 import (
    evaluate_any_fail_block_policy_v1,
    POLICY_REF,
)
from tools.governance_validator.result_contract import (
    ChainValidationResult,
    ChainValidationStatus,
)


def _mk_res(
    status: ChainValidationStatus,
    errors: int = 0,
    warnings: int = 0,
) -> ChainValidationResult:
    # ChainValidationResult 실제 필드에 맞춰 최소 세트로 생성
    # (프로젝트에서 이미 쓰는 생성자 형태를 유지해야 함)
    return ChainValidationResult(
        status=status,
        errors=[{"code": "E"}] * errors,
        warnings=[{"code": "W"}] * warnings,
    )


def test_anyfail_blocks_when_status_not_pass():
    res = _mk_res(ChainValidationStatus.FAIL, errors=0, warnings=0)
    d = evaluate_any_fail_block_policy_v1(res)
    assert d.allow is False
    assert d.policy_ref == POLICY_REF
    assert "status=" in d.reason


def test_anyfail_blocks_when_any_errors_exist():
    res = _mk_res(ChainValidationStatus.PASS, errors=1, warnings=0)
    d = evaluate_any_fail_block_policy_v1(res)
    assert d.allow is False
    assert d.errors_count == 1


def test_anyfail_allows_when_pass_and_no_errors_even_with_warnings():
    res = _mk_res(ChainValidationStatus.PASS, errors=0, warnings=2)
    d = evaluate_any_fail_block_policy_v1(res)
    assert d.allow is True
    assert d.warnings_count == 2


def test_anyfail_rejects_wrong_type():
    with pytest.raises(TypeError):
        evaluate_any_fail_block_policy_v1("nope")  # type: ignore