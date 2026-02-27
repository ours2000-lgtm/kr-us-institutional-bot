import pytest

from tools.observability.runtime_logging_adapter import emit_runtime_event
from tools.observability.errors import RuntimeLoggingSchemaError, RuntimeLoggingInvariantError


def actual_emit_sink(events):
    def _emit(e: dict):
        events.append(e)
    return _emit


def test_decision_bearing_schema_violation_fail_fast():
    bad = {
        "ts_utc": "2026-02-26T00:00:00Z",
        "level": "INFO",
        "component": "aggregation",
        "event": "AGGREGATION_COMPLETED",
        "emitter_id": "test",
        "trace_id": "T1",
        "decision": "ALLOW",
        "grade": "WARN",
        # missing required: policy_ref/reason_codes/marker/inputs_hash/evidence_hash/latency_ms etc
    }

    out = []
    with pytest.raises(RuntimeLoggingSchemaError):
        emit_runtime_event(bad, actual_emit_sink(out))

    assert out == []


def test_decision_bearing_invariant_violation_fail_fast_marker_membership():
    bad = {
        "ts_utc": "2026-02-26T00:00:00Z",
        "level": "INFO",
        "component": "aggregation",
        "event": "AGGREGATION_COMPLETED",
        "emitter_id": "test",
        "trace_id": "T2",
        "decision": "ALLOW",
        "grade": "WARN",
        "policy_ref": "POLICY-X",
        "reason_codes": ["STALE_INPUTS"],  # marker missing
        "marker": {"code": "COMPOSITE_MARKER", "index": 0, "count": 1},
        "inputs_hash": "abc",
        "evidence_hash": "def",
        "latency_ms": 1,
    }

    out = []
    with pytest.raises(RuntimeLoggingInvariantError):
        emit_runtime_event(bad, actual_emit_sink(out))

    assert out == []


def test_infra_only_schema_violation_is_dropped_not_raised():
    bad_infra = {
        "ts_utc": "not-a-datetime",  # ✅ now enforced by FormatChecker
        "level": "INFO",
        "component": "runtime",
        "event": "RUN_STARTED",
        "emitter_id": "infra-daemon",
    }

    out = []
    emit_runtime_event(bad_infra, actual_emit_sink(out))
    assert out == []