# tests_mvp/test_control_plane_gate_contract_v1.py
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from runtime.control_plane.contracts import GateVerdict, Decision, Grade


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def test_gate_verdict_happy_path():
    v = GateVerdict(
        ts_utc=_utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)),
        trace_id="TRACE-001",
        decision=Decision.ALLOW,
        grade=Grade.PASS,
        reason_codes=["OK"],
        policy_ref="POLICY-VALAGG-MED-001",
        emitter_id="GOV_VALIDATOR",
    )
    assert v.decision == Decision.ALLOW
    assert v.grade == Grade.PASS
    assert v.ts_utc.tzinfo is not None


@pytest.mark.parametrize("bad", ["", "   "])
def test_gate_verdict_trace_id_blank_rejected(bad: str):
    with pytest.raises(ValueError, match=r"trace_id must not be blank"):
        GateVerdict(
            ts_utc=_utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)),
            trace_id=bad,
            decision=Decision.ALLOW,
            grade=Grade.PASS,
        )


def test_gate_verdict_reason_codes_must_be_list_str():
    with pytest.raises(TypeError, match=r"reason_codes must be list"):
        GateVerdict(
            ts_utc=_utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)),
            trace_id="TRACE-001",
            decision=Decision.ALLOW,
            grade=Grade.PASS,
            reason_codes="OK",  # type: ignore
        )


def test_gate_verdict_reason_codes_items_non_empty():
    with pytest.raises(ValueError, match=r"reason_codes\[0\]"):
        GateVerdict(
            ts_utc=_utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)),
            trace_id="TRACE-001",
            decision=Decision.ALLOW,
            grade=Grade.PASS,
            reason_codes=["  "],
        )