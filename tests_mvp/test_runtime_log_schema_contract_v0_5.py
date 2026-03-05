# tests_mvp/test_runtime_log_schema_contract_v0_5.py
from __future__ import annotations

import json
from pathlib import Path

import pytest


SCHEMA_PATH = Path("tools/observability/schemas/runtime_log_event_v0.5.json")


def test_runtime_schema_file_exists():
    assert SCHEMA_PATH.exists(), f"schema file missing: {SCHEMA_PATH}"


def test_runtime_schema_is_valid_json():
    raw = SCHEMA_PATH.read_text(encoding="utf-8")
    obj = json.loads(raw)
    assert isinstance(obj, dict)
    assert obj.get("type") == "object"
    assert "properties" in obj
    assert obj["properties"]["schema_version"]["const"] == "runtime_log_event_v0.5"


def test_runtime_schema_accepts_minimal_event():
    jsonschema = pytest.importorskip("jsonschema")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    event = {
        "schema_version": "runtime_log_event_v0.5",
        "ts_utc": "2026-03-02T00:00:00Z",
        "level": "INFO",
        "event_type": "RUNTIME_HEALTH",
        "emitter_id": "KIWOOM_PAPER",
        "message": "ok",
        "trace_id": "TRACE-001",
        "payload": {"k": "v"}
    }
    jsonschema.validate(instance=event, schema=schema)