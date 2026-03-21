# tools/control_plane/gate_runtime_emitter_v1.py
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from tools.observability.runtime_logging_adapter import emit_runtime_event


RUNTIME_SCHEMA_VERSION = "runtime_log_event_v0.5"
EVENT_TYPE_GOV_GATE_DECISION = "GOV_GATE_DECISION"
LEVEL_INFO = "INFO"


def _utc_iso(dt: datetime) -> str:
    if not isinstance(dt, datetime):
        raise TypeError(f"ts_utc must be datetime, got={type(dt)}")
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("ts_utc must be timezone-aware")
    return dt.astimezone(timezone.utc).isoformat()


def _coerce_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if is_dataclass(obj):
        return asdict(obj)
    # last resort: try attr dict
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    raise TypeError(f"Cannot coerce to dict: {type(obj)}")


def emit_gate_decision_runtime_event(
    *,
    ts_utc: datetime,
    emitter_id: str,
    message: str,
    trace_id: str,
    # Gate decision payload input (any object convertible to dict)
    gate_decision: Any,
    # Optional policy fields (SSOT: top-level fields)
    policy_ref: Optional[str] = None,
    decision: Optional[str] = None,
    grade: Optional[str] = None,
    # Extra fields (forward compatible)
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Emit a runtime log event for Control Plane Gate decision.
    - Keep schema stable: runtime_log_event_v0.5
    - Keep level stable: INFO (A안)
    - policy_ref/decision/grade are top-level optional fields
    """
    payload: Dict[str, Any] = {
        "gate_decision": _coerce_dict(gate_decision),
    }
    if extra:
        if not isinstance(extra, dict):
            raise TypeError(f"extra must be dict, got={type(extra)}")
        payload["extra"] = extra

    # NOTE: emit_runtime_event is expected to accept **kwargs and include them into event dict.
    # If adapter doesn't, the tests will FAIL (by design).
    event = emit_runtime_event(
        ts_utc=ts_utc,
        level=LEVEL_INFO,
        event_type=EVENT_TYPE_GOV_GATE_DECISION,
        emitter_id=emitter_id,
        message=message,
        trace_id=trace_id,
        payload=payload,
        policy_ref=policy_ref,
        decision=decision,
        grade=grade,
    )

    # quick invariants (non-schema)
    if event.get("schema_version") != RUNTIME_SCHEMA_VERSION:
        # do not raise here: make mismatch loud for tests/CI
        raise AssertionError(
            f"schema_version mismatch: expected={RUNTIME_SCHEMA_VERSION!r}, got={event.get('schema_version')!r}"
        )
    # ts_utc must be UTC string
    _utc_iso(ts_utc)  # validate input
    if "ts_utc" not in event:
        raise AssertionError("event must contain ts_utc")
    return event