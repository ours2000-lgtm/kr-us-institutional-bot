# tests_mvp/test_policy_flags_contract_v2.py
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from runtime.observability.health.contracts import PolicyFlags, ReasonCode, Severity


def utc_dt() -> datetime:
    return datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc)


def _mk_reason(strategy_id: str = "KIWOOM_PAPER") -> ReasonCode:
    return ReasonCode(
        strategy_id=strategy_id,
        severity=Severity.SEV2,
        count=1,
        window_sec=60,
        incident_code="TEST",
        summary="ok",
    )


def _mk_policy_flags() -> PolicyFlags:
    ts = utc_dt()
    rc = _mk_reason("KIWOOM_PAPER")
    return PolicyFlags(
        ts_utc=ts,
        feature_freeze_suggested=False,
        global_block_suggested=False,
        strategy_block_suggested={"KIWOOM_PAPER": False},
        cooldown_active={"KIWOOM_PAPER": False},
        reason_codes_by_strategy={"KIWOOM_PAPER": [rc]},
        reason_codes_sample=[rc.render()],
    )


def test_policy_flags_happy_path_constructs():
    pf = _mk_policy_flags()
    assert pf.ts_utc.tzinfo is not None
    assert pf.ts_utc.utcoffset() == timezone.utc.utcoffset(None)

    assert isinstance(pf.feature_freeze_suggested, bool)
    assert isinstance(pf.global_block_suggested, bool)

    assert pf.strategy_block_suggested["KIWOOM_PAPER"] is False
    assert pf.cooldown_active["KIWOOM_PAPER"] is False

    assert pf.reason_codes_by_strategy["KIWOOM_PAPER"][0].render() in pf.reason_codes_sample


def test_policy_flags_ts_utc_must_be_timezone_aware():
    with pytest.raises(ValueError):
        PolicyFlags(
            ts_utc=datetime(2026, 3, 2, 0, 0, 0),  # naive
            feature_freeze_suggested=False,
            global_block_suggested=False,
        )


@pytest.mark.parametrize("bad", ["", "   "])
def test_policy_flags_strategy_id_key_blank_rejected(bad: str):
    """
    contracts 레이어가 dict key blank를 '생성 단계에서' 차단하는 계약이라면,
    여기서는 반드시 예외가 발생해야 한다.
    """
    with pytest.raises(ValueError):
        PolicyFlags(
            ts_utc=utc_dt(),
            feature_freeze_suggested=False,
            global_block_suggested=False,
            strategy_block_suggested={bad: True},
            cooldown_active={bad: False},
            reason_codes_by_strategy={bad: [_mk_reason("KIWOOM_PAPER")]},
            reason_codes_sample=["X"],
        )


def test_policy_flags_reason_codes_by_strategy_items_are_reasoncode():
    pf = _mk_policy_flags()
    for sid, rcs in pf.reason_codes_by_strategy.items():
        assert isinstance(sid, str) and sid.strip()
        assert isinstance(rcs, list)
        for rc in rcs:
            assert isinstance(rc, ReasonCode)


def test_policy_flags_reason_codes_sample_is_list_of_str():
    pf = _mk_policy_flags()
    assert isinstance(pf.reason_codes_sample, list)
    for s in pf.reason_codes_sample:
        assert isinstance(s, str)
        assert s.strip()