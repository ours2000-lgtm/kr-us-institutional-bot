from __future__ import annotations

from datetime import datetime, timezone
from time import sleep
from typing import Any, Dict, List, Optional
from uuid import uuid4

from tools.observability.incident_pipeline_v0_3 import emit_and_classify_v0_3

from runtime.session_detector_v0_3 import detect_session_v0_3
from runtime.gate_engine_v0_3 import evaluate_gate_v0_3
from runtime.executor_stub_v0_3 import execute_stub_v0_3

# (권장) 분리 파일을 만들면 아래 import 사용
# from runtime.evidence_stub_v0_3 import emit_evidence_chain_validation_stub_v0_3


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_trace_id(trace_id: Optional[str]) -> str:
    if trace_id is None or not str(trace_id).strip():
        return f"TRACE-RUN-{uuid4().hex}"
    return str(trace_id).strip()


def _emit_evidence_chain_validation_stub(*, ts_utc: datetime, trace_id: str) -> None:
    """
    v0.3.1 stub:
    - v0.4에서 ChainValidationResult 연결 예정
    """
    emit_and_classify_v0_3(
        ts_utc=ts_utc,
        level="INFO",
        event_type="EVIDENCE_CHAIN_VALIDATION",
        emitter_id="runtime.evidence_stub_v0_3",
        message="chain validation stub",
        trace_id=trace_id,
        payload={"status": "STUB"},
    )


def run_once_v0_3(*, trace_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Single run (v0.3.1):
    - RUN_START/RUN_END
    - Session detection
    - Gate decision
    - Executor allow/skip
    - Evidence chain validation stub
    - trace_id invariant: one run == one trace_id
    """
    trace_id = _ensure_trace_id(trace_id)
    ts = _now_utc()

    emit_and_classify_v0_3(
        ts_utc=ts,
        level="INFO",
        event_type="RUNTIME_RUN_START",
        emitter_id="runtime.runner_v0_3",
        message="runtime run started",
        trace_id=trace_id,
        payload={"mode": "run_once_v0_3"},
    )

    # 1) Session detection
    session = detect_session_v0_3(ts_utc=ts)
    emit_and_classify_v0_3(
        ts_utc=ts,
        level="INFO",
        event_type="RUNTIME_SESSION",
        emitter_id="runtime.runner_v0_3",
        message="session detected",
        trace_id=trace_id,
        payload={"session": session},
    )

    # 2) Gate decision
    gate = evaluate_gate_v0_3(ts_utc=ts, trace_id=trace_id, session=session)
    emit_and_classify_v0_3(
        ts_utc=ts,
        level="INFO",
        event_type="GATE_DECISION",
        emitter_id="runtime.gate_engine_v0_3",
        message="gate decision",
        trace_id=trace_id,
        decision=gate["decision"],
        grade=gate["grade"],
        policy_ref=gate.get("policy_ref"),
        payload=gate,
    )

    # 3) Evidence chain validation stub (v0.3.1)
    _emit_evidence_chain_validation_stub(ts_utc=ts, trace_id=trace_id)

    # 4) Executor
    if gate["decision"] == "ALLOW":
        execute_stub_v0_3(ts_utc=ts, trace_id=trace_id, session=session)
    else:
        emit_and_classify_v0_3(
            ts_utc=ts,
            level="INFO",
            event_type="RUNTIME_EXECUTOR_SKIP",
            emitter_id="runtime.runner_v0_3",
            message="executor skipped due to gate decision",
            trace_id=trace_id,
            payload={"decision": gate["decision"], "grade": gate["grade"], "session": session},
        )

    emit_and_classify_v0_3(
        ts_utc=_now_utc(),
        level="INFO",
        event_type="RUNTIME_RUN_END",
        emitter_id="runtime.runner_v0_3",
        message="runtime run completed",
        trace_id=trace_id,
        payload={
            "mode": "run_once_v0_3",
            "session": session,
            "gate_decision": gate["decision"],
            "gate_grade": gate["grade"],
        },
    )

    return {"trace_id": trace_id, "session": session, "gate": gate}


def run_loop_v0_3(
    *,
    max_ticks: int = 5,
    sleep_sec: float = 0.0,
    trace_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    v0.3.1 loop:
    - Each tick emits RUNTIME_TICK (DEBUG)
    - Then performs run_once_v0_3 (which emits the SSOT sequence)
    - max_ticks bounded (no infinite loop in v0.3.x)
    """
    trace_id = _ensure_trace_id(trace_id)

    results: List[Dict[str, Any]] = []
    for i in range(max_ticks):
        emit_and_classify_v0_3(
            ts_utc=_now_utc(),
            level="DEBUG",
            event_type="RUNTIME_TICK",
            emitter_id="runtime.runner_v0_3",
            message="tick",
            trace_id=trace_id,
            payload={"tick": i},
        )

        results.append(run_once_v0_3(trace_id=trace_id))

        if sleep_sec > 0:
            sleep(sleep_sec)

    return results


if __name__ == "__main__":
    # 개발용
    run_loop_v0_3(max_ticks=1, sleep_sec=0.0, trace_id="TRACE-LOCAL-DEV-0001")