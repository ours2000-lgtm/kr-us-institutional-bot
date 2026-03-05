# tests_mvp/test_runtime_log_schema_enforcement_v0_5_v2.py
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

import pytest

from tools.observability.runtime_logging_adapter import emit_runtime_event

SCHEMA_PATH = Path("tools/observability/schemas/runtime_log_event_v0.5.json")
SSOT_SCHEMA_VERSION = "runtime_log_event_v0.5"
ALLOWED_LEVELS = {"DEBUG", "INFO", "ERROR"}  # 스키마 enum SSOT (WARN 미허용)


def _parse_iso(dt_s: str) -> datetime:
    if not isinstance(dt_s, str) or not dt_s.strip():
        raise AssertionError(f"ts_utc must be a non-empty str, got={dt_s!r}")
    s = dt_s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _assert_ts_utc_is_utc(dt_s: str) -> None:
    dt = _parse_iso(dt_s)
    assert dt.tzinfo is not None, f"ts_utc must be timezone-aware, got={dt_s!r}"
    assert dt.utcoffset() == timezone.utc.utcoffset(None), f"ts_utc must be UTC(+00:00), got={dt_s!r}"


def _load_schema_or_skip() -> Dict[str, Any]:
    if not SCHEMA_PATH.exists():
        pytest.skip(f"runtime schema missing (local env): {SCHEMA_PATH.as_posix()}")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _jsonschema_validate_or_skip(instance: Dict[str, Any], schema: Dict[str, Any]) -> None:
    try:
        import jsonschema  # type: ignore
    except Exception as e:
        pytest.skip(f"jsonschema not available: {e}. Install: pip install jsonschema")
    jsonschema.validate(instance=instance, schema=schema)


def utc_dt() -> datetime:
    return datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)


def kst_dt() -> datetime:
    kst = timezone(timedelta(hours=9))
    return datetime(2026, 3, 2, 9, 0, 0, tzinfo=kst)


def _assert_base_invariants(e: Dict[str, Any]) -> None:
    assert e.get("schema_version") == SSOT_SCHEMA_VERSION
    assert e.get("level") in ALLOWED_LEVELS, f"level must be one of {sorted(ALLOWED_LEVELS)}, got={e.get('level')!r}"
    assert "ts_utc" in e
    _assert_ts_utc_is_utc(e["ts_utc"])


def test_emit_runtime_event_ts_utc_is_utc_and_schema_version_ssot():
    e = emit_runtime_event(
        ts_utc=utc_dt(),
        level="INFO",
        event_type="RUNTIME_HEALTH",
        emitter_id="KIWOOM_PAPER",
        message="ok",
        trace_id="TRACE-UTC-001",
        payload={"k": "v"},
    )
    _assert_base_invariants(e)


def test_emit_runtime_event_timezone_normalization_kst_to_utc():
    e = emit_runtime_event(
        ts_utc=kst_dt(),
        level="INFO",
        event_type="RUNTIME_HEALTH",
        emitter_id="KIWOOM_PAPER",
        message="kst->utc",
        trace_id="TRACE-TZ-001",
        payload={"k": "v"},
    )
    _assert_base_invariants(e)


@pytest.mark.parametrize("bad_level", ["", "   ", None, "BAD"])
def test_emit_runtime_event_invalid_level_rejected(bad_level):
    with pytest.raises((TypeError, ValueError)):
        emit_runtime_event(
            ts_utc=utc_dt(),
            level=bad_level,  # type: ignore[arg-type]
            event_type="RUNTIME_HEALTH",
            emitter_id="KIWOOM_PAPER",
            message="bad-level",
            trace_id="TRACE-BADLEVEL-001",
            payload={"k": "v"},
        )


@pytest.mark.parametrize(
    "alias,expected",
    [
        ("info", "INFO"),
        ("Info", "INFO"),
        ("ERROR", "ERROR"),
        ("debug", "DEBUG"),
        ("warn", "INFO"),
        ("WARN", "INFO"),
    ],
)
def test_emit_runtime_event_level_normalizes(alias: str, expected: str):
    e = emit_runtime_event(
        ts_utc=utc_dt(),
        level=alias,
        event_type="RUNTIME_HEALTH",
        emitter_id="KIWOOM_PAPER",
        message="level-normalize",
        trace_id="TRACE-LVL-001",
        payload={"k": "v"},
    )
    assert e.get("level") == expected
    _assert_base_invariants(e)


def test_emit_runtime_event_payload_variety_schema_valid():
    schema = _load_schema_or_skip()

    varied_payload = {
        "num": 123,
        "pi": 3.14159,
        "flag": True,
        "arr": [1, 2, 3, {"x": "y"}],
        "obj": {"nested": {"a": 1, "b": [10, 20]}},
        "nullish": None,
    }

    e = emit_runtime_event(
        ts_utc=utc_dt(),
        level="INFO",
        event_type="RUNTIME_HEALTH",
        emitter_id="KIWOOM_PAPER",
        message="payload-variety",
        trace_id="TRACE-PAYLOAD-001",
        payload=varied_payload,
    )
    _assert_base_invariants(e)
    _jsonschema_validate_or_skip(e, schema)


def test_emit_runtime_event_optional_policy_fields_schema_valid():
    """
    policy_ref / decision / grade:
    - 어댑터가 **kwargs로 event에 포함시키는 구조일 때만 의미가 있음.
    - 스키마가 허용하지 않으면 여기서 FAIL이 정상 → 스키마/계약 합의 필요.
    """
    schema = _load_schema_or_skip()

    e = emit_runtime_event(
        ts_utc=utc_dt(),
        level="WARN",  # 입력은 WARN이어도 최종은 INFO로 normalize 되어야 함
        event_type="GOV_GATE_DECISION",
        emitter_id="KIWOOM_PAPER",
        message="policy fields present",
        trace_id="TRACE-POLICY-001",
        payload={"reason": "test"},
        policy_ref="POLICY-VALAGG-MED-001",
        decision="ALLOW",
        grade="PASS",
    )

    _assert_base_invariants(e)
    _jsonschema_validate_or_skip(e, schema)