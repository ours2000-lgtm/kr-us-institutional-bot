from __future__ import annotations

import pytest

from integration_core.consistency import ComplianceRecord, ConsistencyResult, Severity, enforce


def _v(code: str, sev: Severity, msg: str) -> ConsistencyResult:
    return ConsistencyResult(ok=False, code=code, severity=sev.value, message=msg)


def test_enforce_warn_never_raises_and_records():
    captured: list[ComplianceRecord] = []
    results = [_v("DRIFT_TEST", Severity.MEDIUM, "warn-case")]

    assert enforce(results, mode="warn", on_record=captured.append) is True
    assert captured
    assert captured[0].decision == "allowed"
    assert captured[0].violations  # record should include violations


def test_enforce_block_only_high_blocks():
    # MEDIUM only => pass
    assert enforce([_v("M1", Severity.MEDIUM, "m")], mode="block") is True
    # LOW only => pass
    assert enforce([_v("L1", Severity.LOW, "l")], mode="block") is True

    # HIGH => raise
    with pytest.raises(RuntimeError) as e:
        enforce([_v("H1", Severity.HIGH, "h")], mode="block")
    assert "CRITICAL" in str(e.value)
    assert "H1" in str(e.value)


def test_enforce_strict_blocks_any_severity():
    with pytest.raises(RuntimeError):
        enforce([_v("L1", Severity.LOW, "l")], mode="strict")
    with pytest.raises(RuntimeError):
        enforce([_v("M1", Severity.MEDIUM, "m")], mode="strict")
    with pytest.raises(RuntimeError):
        enforce([_v("H1", Severity.HIGH, "h")], mode="strict")


def test_enforce_ok_never_raises():
    ok = ConsistencyResult(ok=True, code="OK", severity=Severity.LOW.value, message="ok")
    assert enforce([ok], mode="warn") is True
    assert enforce([ok], mode="block") is True
    assert enforce([ok], mode="strict") is True