# KR_US_INSTITUTIONAL_BOT/tests/test_validate_e2e.py
import pytest

from src.fsm.validate import validate_trace
from src.fsm.violations import Severity


ALLOWED = {
    ("S0_INIT", "S1_COLLECTED"),
    ("S1_COLLECTED", "S2_REHEARSAL_PROVEN"),
    ("S2_REHEARSAL_PROVEN", "S3_ACTIVATED"),
}

# ✅ 정상 lifecycle 종료 정책
TERMINAL_OK = {"S3_ACTIVATED", "SX_FAIL_CLOSED"}

# ✅ 테스트 전용 정책 (after-terminal 위반 생성용)
TERMINAL_PROVEN_IS_TERMINAL = {"S2_REHEARSAL_PROVEN", "SX_FAIL_CLOSED"}


@pytest.mark.e2e
def test_e2e_ok_minimal(load_trace):
    events = load_trace("trace_ok_minimal.json")
    res = validate_trace(
        events,
        allowed_transitions=ALLOWED,
        terminal_states=TERMINAL_OK,
        require_genesis=True,
        ok_mode="STRICT_ALL",
    )
    assert res.fail_closed is False
    assert res.ok is True


@pytest.mark.e2e
def test_e2e_illegal_transition_fail(load_trace):
    events = load_trace("trace_bad_illegal_transition.json")
    res = validate_trace(
        events,
        allowed_transitions=ALLOWED,
        terminal_states=TERMINAL_OK,
        require_genesis=True,
        ok_mode="STRICT_ALL",
    )
    assert res.fail_closed is True
    v = next(v for v in res.violations if v.code == "L2_ILLEGAL_TRANSITION")
    assert v.severity == Severity.CRITICAL
    assert v.context.get("from_state") == "S0_INIT"
    assert v.context.get("to_state") == "S99_UNKNOWN"


@pytest.mark.e2e
def test_e2e_missing_payload_fail(load_trace):
    events = load_trace("trace_bad_missing_payload.json")
    res = validate_trace(
        events,
        allowed_transitions=ALLOWED,
        terminal_states=TERMINAL_OK,
        require_genesis=True,
        ok_mode="STRICT_ALL",
    )
    assert res.fail_closed is True
    v = next(v for v in res.violations if v.code == "L3_PAYLOAD_MISSING_FIELD")
    assert v.severity == Severity.CRITICAL
    assert v.context.get("to_state") == "S2_REHEARSAL_PROVEN"


@pytest.mark.e2e
def test_e2e_incomplete_trace_warn_but_ok(load_trace):
    events = load_trace("trace_bad_incomplete_trace.json")
    res = validate_trace(
        events,
        allowed_transitions=ALLOWED,
        terminal_states=TERMINAL_OK,
        require_genesis=True,
        l3_finality_policy="WARN_INCOMPLETE",
        ok_mode="STRICT_CRITICAL",  # WARNING-only 허용
    )
    assert res.fail_closed is False
    assert res.ok is True
    v = next(v for v in res.violations if v.code == "L3_TRACE_INCOMPLETE")
    assert v.severity == Severity.WARNING


@pytest.mark.e2e
def test_e2e_activated_before_proven_fail(load_trace):
    events = load_trace("trace_bad_activated_before_proven.json")
    res = validate_trace(
        events,
        allowed_transitions=ALLOWED,
        terminal_states=TERMINAL_OK,
        require_genesis=True,
        ok_mode="STRICT_ALL",
    )
    assert res.fail_closed is True
    v = next(v for v in res.violations if v.code == "L3_ACTIVATED_BEFORE_PROVEN")
    assert v.severity == Severity.CRITICAL


@pytest.mark.e2e
def test_e2e_after_terminal_fail(load_trace):
    events = load_trace("trace_bad_after_terminal.json")
    res = validate_trace(
        events,
        allowed_transitions=ALLOWED,
        terminal_states=TERMINAL_PROVEN_IS_TERMINAL,
        require_genesis=True,
        ok_mode="STRICT_ALL",
    )
    assert res.fail_closed is True
    assert any(v.code == "L2_AFTER_TERMINAL" for v in res.violations)
