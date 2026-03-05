# tests_mvp/test_gate_decision_runtime_event_v1.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest

from tools.control_plane.gate_runtime_emitter_v1 import emit_gate_decision_runtime_event


SCHEMA_PATH = Path("tools/observability/schemas/runtime_log_event_v0.5.json")
SSOT_SCHEMA_VERSION = "runtime_log_event_v0.5"


def utc_dt() -> datetime:
    return datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)


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


def _load_schema() -> Dict[str, Any]:
    assert SCHEMA_PATH.exists(), (
        f"Runtime schema file missing: {SCHEMA_PATH.as_posix()}\n"
        f"Create/restore it first. (This test intentionally FAILS if schema is missing.)"
    )
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _jsonschema_validate(instance: Dict[str, Any], schema: Dict[str, Any]) -> None:
    try:
        import jsonschema  # type: ignore
    except Exception as e:
        pytest.skip(f"jsonschema not available: {e}. Install: pip install jsonschema")

    jsonschema.validate(instance=instance, schema=schema)


def test_gate_decision_runtime_event_includes_policy_fields_and_schema_valid():
    schema = _load_schema()

    gate_decision = {
        "policy_eval": {"any_fail": False},
        "notes": "ok",
        "meta": {"source": "test"},
    }

    e = emit_gate_decision_runtime_event(
        ts_utc=utc_dt(),
        emitter_id="KIWOOM_PAPER",
        message="gate decision",
        trace_id="TRACE-GATE-001",
        gate_decision=gate_decision,
        policy_ref="POLICY-VALAGG-MED-001",
        decision="ALLOW",
        grade="PASS",
    )

    # SSOT invariants
    assert e.get("schema_version") == SSOT_SCHEMA_VERSION
    assert e.get("event_type") == "GOV_GATE_DECISION"
    assert e.get("level") == "INFO"  # A안: 스키마 안 건드리고 INFO 고정
    assert e.get("emitter_id") == "KIWOOM_PAPER"
    assert e.get("trace_id") == "TRACE-GATE-001"

    # policy fields must be top-level
    assert e.get("policy_ref") == "POLICY-VALAGG-MED-001"
    assert e.get("decision") == "ALLOW"
    assert e.get("grade") == "PASS"

    # ts_utc must be UTC ISO
    assert "ts_utc" in e
    _assert_ts_utc_is_utc(e["ts_utc"])

    # payload shape
    payload = e.get("payload")
    assert isinstance(payload, dict)
    assert "gate_decision" in payload
    assert payload["gate_decision"]["meta"]["source"] == "test"

    # schema 100% validation
    _jsonschema_validate(e, schema)