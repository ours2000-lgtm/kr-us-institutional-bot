from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest

from runtime import runner_v0_3


class _Sink:
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def emit(self, event: Dict[str, Any]) -> None:
        self.events.append(event)


def _capture_events(monkeypatch: pytest.MonkeyPatch) -> _Sink:
    """
    runner_v0_3가 사용하는 emit_and_classify_v0_3를
    '캡처용 함수'로 교체해서 event 목록을 얻는다.
    """
    sink = _Sink()

    def _fake_emit_and_classify_v0_3(**kwargs: Any) -> Dict[str, Any]:
        # 실제 emit_runtime_event가 반환하는 dict 형태를 최소로 모사
        event = {
            "schema_version": "runtime_log_event_v0.5",
            "ts_utc": kwargs["ts_utc"].astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": kwargs["level"],
            "event_type": kwargs["event_type"],
            "emitter_id": kwargs["emitter_id"],
            "message": kwargs["message"],
        }
        if kwargs.get("trace_id") is not None:
            event["trace_id"] = kwargs["trace_id"]
        if kwargs.get("payload") is not None:
            event["payload"] = kwargs["payload"]
        if kwargs.get("policy_ref") is not None:
            event["policy_ref"] = kwargs["policy_ref"]
        if kwargs.get("decision") is not None:
            event["decision"] = kwargs["decision"]
        if kwargs.get("grade") is not None:
            event["grade"] = kwargs["grade"]

        sink.emit(event)
        return event

    # runner_v0_3 모듈 내부에서 참조하는 이름을 교체
    monkeypatch.setattr(runner_v0_3, "emit_and_classify_v0_3", _fake_emit_and_classify_v0_3)
    return sink


def test_run_once_sequence_block(monkeypatch: pytest.MonkeyPatch) -> None:
    sink = _capture_events(monkeypatch)

    # gate_engine이 기본 BLOCK을 반환하는 v0.3 stub이라는 전제
    result = runner_v0_3.run_once_v0_3(trace_id="TRACE-TEST-0001")
    assert result["trace_id"] == "TRACE-TEST-0001"

    seq = [e["event_type"] for e in sink.events]

    # 최소 순서 계약 (BLOCK path)
    assert seq[0] == "RUNTIME_RUN_START"
    assert seq[1] == "RUNTIME_SESSION"
    assert "GATE_DECISION" in seq
    assert "EVIDENCE_CHAIN_VALIDATION" in seq
    assert "RUNTIME_EXECUTOR_SKIP" in seq
    assert seq[-1] == "RUNTIME_RUN_END"

    # trace_id invariant: 한 run의 모든 이벤트는 같은 trace_id
    trace_ids = {e.get("trace_id") for e in sink.events}
    assert trace_ids == {"TRACE-TEST-0001"}


def test_run_loop_emits_ticks(monkeypatch: pytest.MonkeyPatch) -> None:
    sink = _capture_events(monkeypatch)

    runner_v0_3.run_loop_v0_3(max_ticks=3, sleep_sec=0.0, trace_id="TRACE-TEST-LOOP")

    tick_events = [e for e in sink.events if e["event_type"] == "RUNTIME_TICK"]
    assert len(tick_events) == 3

    # tick payload에 tick index가 존재
    assert tick_events[0]["payload"]["tick"] == 0
    assert tick_events[1]["payload"]["tick"] == 1
    assert tick_events[2]["payload"]["tick"] == 2

    # loop 전체에서도 trace_id invariant 유지
    trace_ids = {e.get("trace_id") for e in sink.events}
    assert trace_ids == {"TRACE-TEST-LOOP"}