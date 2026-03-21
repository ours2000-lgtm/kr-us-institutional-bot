import json
from pathlib import Path
import pytest

# tests/conftest.py 기준: fixtures는 tests/fixtures/traces 에 존재
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "traces"


@pytest.fixture
def load_trace():
    def _load(name: str):
        path = FIXTURE_DIR / name
        assert path.exists(), f"fixture not found: {path}"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise AssertionError(f"invalid JSON fixture: {path} ({e})")
    return _load


@pytest.fixture
def mk_genesis():
    def _mk(trace_id: str = "T-TEST", ts_utc: str = "2026-02-05T00:00:00Z", emitter_id: str = "E"):
        e = {"event_type": "RUN_START"}
        if trace_id is not None:
            e["trace_id"] = trace_id
        if ts_utc is not None:
            e["ts_utc"] = ts_utc
        if emitter_id is not None:
            e["emitter_id"] = emitter_id
        return e
    return _mk


@pytest.fixture
def mk_transition():
    def _mk(
        fr: str = "S0_INIT",
        to: str = "S1_COLLECTED",
        seq=None,
        ts_utc: str | None = None,
        trace_id: str | None = None,
        payload: dict | None = None,
    ):
        e = {"event_type": "TRANSITION", "from_state": fr, "to_state": to}
        if seq is not None:
            e["seq"] = seq
        if ts_utc is not None:
            e["ts_utc"] = ts_utc
        if trace_id is not None:
            e["trace_id"] = trace_id
        if payload is not None:
            e["payload"] = payload
        return e
    return _mk
