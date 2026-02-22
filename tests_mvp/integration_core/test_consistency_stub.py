from __future__ import annotations

import pytest

from integration_core.consistency import ConsistencyResult, enforce


def _violation(msg: str = "drift") -> ConsistencyResult:
    # drift_code -> code 로 통일 (현재 계약)
    return ConsistencyResult(ok=False, message=msg, code="DRIFT_TEST")


def test_enforce_warn_never_raises():
    results = [_violation()]
    enforce(results, mode="warn")


def test_enforce_block_raises_on_drift():
    results = [_violation()]
    with pytest.raises(RuntimeError):
        enforce(results, mode="block")


def test_enforce_ok_never_raises():
    results: list[ConsistencyResult] = []
    enforce(results, mode="block")