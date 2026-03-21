from __future__ import annotations

from datetime import datetime
from typing import Optional

from tools.observability.incident_pipeline_v0_3 import emit_and_classify_v0_3


def execute_stub_v0_3(*, ts_utc: datetime, trace_id: Optional[str], session: str) -> None:
    """
    v0.3 stub executor:
    - 주문 실행 없음
    - '실행 시도/스킵' 텔레메트리만 발행
    """
    emit_and_classify_v0_3(
        ts_utc=ts_utc,
        level="INFO",
        event_type="RUNTIME_EXECUTOR",
        emitter_id="runtime.executor_stub_v0_3",
        message="executor stub invoked",
        trace_id=trace_id,
        payload={"session": session, "note": "no real orders in v0.3"},
    )