# tests_mvp/test_runtime_logging_adapter_enforcement_v1.py
from __future__ import annotations

from datetime import datetime, timezone
import pytest

from tools.observability.runtime_logging_adapter import emit_runtime_event


def utc_now():
    return datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)


def test_emit_runtime_event_happy_path():
    event = emit_runtime_event(
        ts_utc=utc_now(),
        level="INFO",
        event_type="RUNTIME_HEALTH",
        emitter_id="KIWOOM_PAPER",
        message="ok",
        trace_id="TRACE-001",
        payload={"k": "v"},
    )

    assert event["schema_version"] == "runtime_log_event_v0.5"
    assert event["level"] == "INFO"
    assert event["event_type"] == "RUNTIME_HEALTH"
    assert event["emitter_id"] == "KIWOOM_PAPER"
    assert event["trace_id"] == "TRACE-001"
    assert isinstance(event["ts_utc"], str)
    assert event["payload"] == {"k": "v"}


@pytest.mark.parametrize("bad_level", ["info", "BAD", "", None])
def test_emit_runtime_event_invalid_level_rejected(bad_level):
    with pytest.raises((ValueError, TypeError)):
        emit_runtime_event(
            ts_utc=utc_now(),
            level=bad_level,  # invalid
            event_type="RUNTIME_HEALTH",
            emitter_id="KIWOOM_PAPER",
            message="ok",
            trace_id="TRACE-001",
        )


@pytest.mark.parametrize("bad_trace", ["", "   ", None])
def test_emit_runtime_event_trace_id_blank_rejected(bad_trace):
    with pytest.raises((ValueError, TypeError)):
        emit_runtime_event(
            ts_utc=utc_now(),
            level="INFO",
            event_type="RUNTIME_HEALTH",
            emitter_id="KIWOOM_PAPER",
            message="ok",
            trace_id=bad_trace,
        )


def test_emit_runtime_event_missing_required_fields():
    with pytest.raises(TypeError):
        emit_runtime_event(
            ts_utc=utc_now(),
            level="INFO",
            event_type="RUNTIME_HEALTH",
            emitter_id="KIWOOM_PAPER",
            # message missing
            trace_id="TRACE-001",
        )