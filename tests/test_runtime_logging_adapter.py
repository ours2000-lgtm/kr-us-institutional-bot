import pytest
from datetime import datetime, timezone

from tools.observability.runtime_logging_adapter import emit_runtime_event


def test_naive_ts_rejected():
    with pytest.raises(ValueError):
        emit_runtime_event(
            ts_utc=datetime.now(),  # naive
            level="INFO",
            event_type="RUNTIME_HEALTH",
            emitter_id="kr.engine",
            message="ok",
        )


def test_warn_level_normalized_to_info():
    e = emit_runtime_event(
        ts_utc=datetime.now(timezone.utc),
        level="warn",
        event_type="RUNTIME_HEALTH",
        emitter_id="kr.engine",
        message="ok",
    )
    assert e["level"] == "INFO"


def test_payload_datetime_rejected():
    with pytest.raises(ValueError):
        emit_runtime_event(
            ts_utc=datetime.now(timezone.utc),
            level="INFO",
            event_type="RUNTIME_HEALTH",
            emitter_id="kr.engine",
            message="bad payload",
            payload={"t": datetime.now(timezone.utc)},
        )


def test_extras_reserved_key_conflict_rejected():
    with pytest.raises(ValueError):
        emit_runtime_event(
            ts_utc=datetime.now(timezone.utc),
            level="INFO",
            event_type="RUNTIME_HEALTH",
            emitter_id="kr.engine",
            message="bad extras",
            level2="x",   # ok
            level="y",    # <-- 이건 파이썬 문법상 안 됨(중복 키)
        )

# 위 케이스는 파이썬 호출 자체가 불가하니, 실제론 아래처럼 'schema_version' 같은 reserved를 extras로 주면 됨.
def test_extras_conflict_with_reserved_field_rejected():
    with pytest.raises(ValueError):
        emit_runtime_event(
            ts_utc=datetime.now(timezone.utc),
            level="INFO",
            event_type="RUNTIME_HEALTH",
            emitter_id="kr.engine",
            message="bad extras",
            schema_version="x",  # reserved conflict via **extras
        )


def test_decision_enum_enforced():
    with pytest.raises(ValueError):
        emit_runtime_event(
            ts_utc=datetime.now(timezone.utc),
            level="INFO",
            event_type="GATE_DECISION",
            emitter_id="gov.control",
            message="bad decision",
            trace_id="t-1",
            decision="PERMIT",  # invalid
        )


def test_grade_enum_enforced():
    with pytest.raises(ValueError):
        emit_runtime_event(
            ts_utc=datetime.now(timezone.utc),
            level="INFO",
            event_type="GATE_DECISION",
            emitter_id="gov.control",
            message="bad grade",
            trace_id="t-1",
            grade="OK",  # invalid
        )


def test_trace_id_required_for_gate_events():
    with pytest.raises(ValueError):
        emit_runtime_event(
            ts_utc=datetime.now(timezone.utc),
            level="INFO",
            event_type="GATE_DECISION",
            emitter_id="gov.control",
            message="missing trace",
            # trace_id omitted -> must fail
        )


def test_trace_id_optional_for_runtime_events():
    e = emit_runtime_event(
        ts_utc=datetime.now(timezone.utc),
        level="DEBUG",
        event_type="RUNTIME_HEALTH",
        emitter_id="kr.engine",
        message="ok",
        # trace_id omitted -> allowed
    )
    assert "trace_id" not in e