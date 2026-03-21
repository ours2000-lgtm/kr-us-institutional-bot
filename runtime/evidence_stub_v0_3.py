from __future__ import annotations

from datetime import datetime
from typing import Optional

from tools.observability.incident_pipeline_v0_3 import emit_and_classify_v0_3


def emit_evidence_chain_validation_stub_v0_3(*, ts_utc: datetime, trace_id: str) -> None:
    emit_and_classify_v0_3(
        ts_utc=ts_utc,
        level="INFO",
        event_type="EVIDENCE_CHAIN_VALIDATION",
        emitter_id="runtime.evidence_stub_v0_3",
        message="chain validation stub",
        trace_id=trace_id,
        payload={"status": "STUB"},
    )