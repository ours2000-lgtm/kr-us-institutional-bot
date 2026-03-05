from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

EmitFunc = Callable[[Dict[str, Any]], None]

SSOT_SCHEMA_VERSION = "runtime_log_event_v0.5"

ALLOWED_LEVELS = {"DEBUG", "INFO", "ERROR"}
ALLOWED_DECISIONS = {"ALLOW", "BLOCK"}
ALLOWED_GRADES = {"PASS", "WARN", "FAIL"}

TRACE_REQUIRED_PREFIXES = ("GOV_", "GATE_", "EVIDENCE_")


def _require_utc_aware(dt: datetime) -> datetime:
    if not isinstance(dt, datetime):
        raise TypeError("ts_utc must be datetime")
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("ts_utc must be timezone-aware")
    return dt.astimezone(timezone.utc)


def _require_non_empty_str(s: Any, name: str) -> str:
    if not isinstance(s, str):
        raise TypeError(f"{name} must be str")
    if not s.strip():
        raise ValueError(f"{name} must not be blank")
    return s.strip()


def _normalize_level(level: Any) -> str:
    if not isinstance(level, str):
        raise TypeError("level must be str")

    s = level.strip()
    if not s:
        raise ValueError("level must not be blank")

    u = s.upper()

    # SSOT: schema enum에는 WARN 없음 → INFO로 normalize
    if u in ("WARN", "WARNING"):
        return "INFO"

    if u in ALLOWED_LEVELS:
        return u

    raise ValueError(f"invalid level: {level!r}")


def _normalize_decision(decision: Any) -> str:
    if not isinstance(decision, str):
        raise TypeError("decision must be str")
    u = decision.strip().upper()
    if not u:
        raise ValueError("decision must not be blank")
    if u in ALLOWED_DECISIONS:
        return u
    raise ValueError(f"invalid decision: {decision!r}")


def _normalize_grade(grade: Any) -> str:
    if not isinstance(grade, str):
        raise TypeError("grade must be str")
    u = grade.strip().upper()
    if not u:
        raise ValueError("grade must not be blank")
    if u in ALLOWED_GRADES:
        return u
    raise ValueError(f"invalid grade: {grade!r}")


def _is_json_value(x: Any, *, depth: int = 0) -> bool:
    if depth > 20:
        return False

    if x is None or isinstance(x, (str, int, float, bool)):
        return True

    if isinstance(x, list):
        return all(_is_json_value(v, depth=depth + 1) for v in x)

    if isinstance(x, dict):
        return all(
            isinstance(k, str) and _is_json_value(v, depth=depth + 1)
            for k, v in x.items()
        )

    return False


def _trace_required_for_event_type(event_type: str) -> bool:
    # event_type는 이미 non-empty str로 정규화된 값이라고 가정
    return event_type.startswith(TRACE_REQUIRED_PREFIXES)


def emit_runtime_event(
    *,
    ts_utc: datetime,
    level: str,
    event_type: str,
    emitter_id: str,
    message: str,
    trace_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    policy_ref: Optional[str] = None,
    decision: Optional[str] = None,
    grade: Optional[str] = None,
    actual_emit: Optional[EmitFunc] = None,
    **extras: Any,
) -> Dict[str, Any]:

    ts_utc_norm = _require_utc_aware(ts_utc)
    level_norm = _normalize_level(level)

    event_type_norm = _require_non_empty_str(event_type, "event_type")
    emitter_id_norm = _require_non_empty_str(emitter_id, "emitter_id")
    message_norm = _require_non_empty_str(message, "message")

    # trace_id: 조건부 필수 (SSOT)
    if _trace_required_for_event_type(event_type_norm):
        if trace_id is None:
            raise ValueError("trace_id is required for GOV_/GATE_/EVIDENCE_ events")

    event: Dict[str, Any] = {
        "schema_version": SSOT_SCHEMA_VERSION,
        "ts_utc": ts_utc_norm.isoformat().replace("+00:00", "Z"),
        "level": level_norm,
        "event_type": event_type_norm,
        "emitter_id": emitter_id_norm,
        "message": message_norm,
    }

    if trace_id is not None:
        event["trace_id"] = _require_non_empty_str(trace_id, "trace_id")

    if payload is not None:
        if not isinstance(payload, dict):
            raise TypeError("payload must be dict[str, Any]")
        if not _is_json_value(payload):
            raise ValueError("payload must be JSON-serializable")
        event["payload"] = payload

    if policy_ref is not None:
        event["policy_ref"] = _require_non_empty_str(policy_ref, "policy_ref")

    # decision/grade: SSOT enum 강제
    if decision is not None:
        event["decision"] = _normalize_decision(decision)

    if grade is not None:
        event["grade"] = _normalize_grade(grade)

    for k, v in extras.items():
        if v is None:
            continue
        if not isinstance(k, str) or not k.strip():
            raise ValueError("extra field keys must be non-empty strings")
        if k in event:
            raise ValueError(f"extra field '{k}' conflicts with reserved field")
        if not _is_json_value(v):
            raise ValueError(f"extra field '{k}' must be JSON-serializable")
        event[k] = v

    if actual_emit is not None:
        if not callable(actual_emit):
            raise TypeError("actual_emit must be callable")
        actual_emit(event)

    return event