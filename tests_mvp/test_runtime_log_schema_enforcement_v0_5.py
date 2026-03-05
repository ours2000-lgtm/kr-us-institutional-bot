# tests_mvp/test_runtime_log_schema_enforcement_v0_5.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tools.observability.runtime_logging_adapter import emit_runtime_event

SCHEMA_PATH = Path("tools/observability/schemas/runtime_log_event_v0.5.json")


# -----------------------------
# Helpers
# -----------------------------
def _parse_iso(dt_s: str) -> datetime:
    """
    Accepts:
      - 2026-03-02T00:00:00+00:00
      - 2026-03-02T00:00:00Z
    """
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


def _assert_schema_version_v05(e: dict) -> None:
    """
    Historical drift absorber:
      - some code uses "runtime_log_event_v0.5"
      - some code uses "0.5"
    We accept either for now (contract hardening can tighten later).
    """
    sv = e.get("schema_version")
    assert sv in ("runtime_log_event_v0.5", "0.5"), f"schema_version must be v0.5 token, got={sv!r}"


def _load_schema() -> dict:
    assert SCHEMA_PATH.exists(), (
        f"Runtime schema file missing: {SCHEMA_PATH.as_posix()}\n"
        f"Create/restore it first. (This test intentionally FAILS if schema is missing.)"
    )
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _jsonschema_validate(instance: dict, schema: dict) -> None:
    try:
        import jsonschema  # type: ignore
    except Exception as e:
        pytest.skip(f"jsonschema not available: {e}. Install: pip install jsonschema")

    jsonschema.validate(instance=instance, schema=schema)


def utc_dt() -> datetime:
    return datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)


# -----------------------------
# Tests
# -----------------------------
def test_emit_runtime_event_ts_utc_is_utc():
    e = emit_runtime_event(
        ts_utc=utc_dt(),
        level="INFO",
        event_type="RUNTIME_HEALTH",
        emitter_id="KIWOOM_PAPER",
        message="ok",
        trace_id="TRACE-UTC-001",
        payload={"k": "v"},
    )
    assert "ts_utc" in e
    _assert_ts_utc_is_utc(e["ts_utc"])


def test_emit_runtime_event_payload_variety_schema_valid():
    schema = _load_schema()

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

    # Quick invariants before schema validation
    _assert_schema_version_v05(e)
    _assert_ts_utc_is_utc(e["ts_utc"])

    # Schema 100% validation
    _jsonschema_validate(e, schema)


def test_emit_runtime_event_optional_policy_fields_schema_valid():
    """
    policy_ref / decision / grade are optional fields.
    This test PASSes only if:
      - emit_runtime_event accepts **kwargs and includes them in the emitted event dict
      - schema allows those fields
    If schema disallows them, FAIL is correct until schema/contract is aligned.
    """
    schema = _load_schema()

    e = emit_runtime_event(
        ts_utc=utc_dt(),
        level="WARN",
        event_type="GOV_GATE_DECISION",
        emitter_id="KIWOOM_PAPER",
        message="policy fields present",
        trace_id="TRACE-POLICY-001",
        payload={"reason": "test"},
        # Optional fields (adapter must accept **kwargs and merge into event)
        policy_ref="POLICY-VALAGG-MED-001",
        decision="ALLOW",
        grade="PASS",
    )

    _assert_schema_version_v05(e)
    _assert_ts_utc_is_utc(e["ts_utc"])
    _jsonschema_validate(e, schema)