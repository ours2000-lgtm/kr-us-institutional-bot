# tests_mvp/test_policy_flags_contract.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from runtime.observability.health.contracts import PolicyFlags, ReasonCode, Severity


def utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def kst(dt: datetime) -> datetime:
    # Asia/Seoul without external tz lib
    KST = timezone(timedelta(hours=9))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=KST)
    return dt.astimezone(KST)


def _rc(strategy_id: str = "KIWOOM_PAPER") -> ReasonCode:
    return ReasonCode(
        strategy_id=strategy_id,
        severity=Severity.SEV2,
        count=1,
        window_sec=60,
        incident_code="TEST",
        summary="ok",
    )


def test_policy_flags_valid_minimal():
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))

    pf = PolicyFlags(
        ts_utc=ts,
        feature_freeze_suggested=False,
        global_block_suggested=False,
        strategy_block_suggested={"KIWOOM_PAPER": False},
        cooldown_active={"KIWOOM_PAPER": False},
        reason_codes_by_strategy={"KIWOOM_PAPER": [_rc("KIWOOM_PAPER")]},
        reason_codes_sample=["KIWOOM_PAPER:SEV2:1/1m:TEST"],
    )

    assert pf.ts_utc.tzinfo is not None
    assert pf.ts_utc.utcoffset() == timedelta(0)
    assert pf.strategy_block_suggested["KIWOOM_PAPER"] is False


def test_policy_flags_ts_utc_normalizes_to_utc():
    ts_kst = kst(datetime(2026, 3, 2, 9, 0, 0))  # KST 09:00 == UTC 00:00
    pf = PolicyFlags(
        ts_utc=ts_kst,
        feature_freeze_suggested=False,
        global_block_suggested=False,
    )
    assert pf.ts_utc.utcoffset() == timedelta(0)


@pytest.mark.parametrize("val", [0, 1, "false", None, object()])
def test_policy_flags_feature_freeze_must_be_bool(val):
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(
            ts_utc=ts,
            feature_freeze_suggested=val,  # type: ignore[arg-type]
            global_block_suggested=False,
        )


@pytest.mark.parametrize("val", [0, 1, "false", None, object()])
def test_policy_flags_global_block_must_be_bool(val):
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=val,  # type: ignore[arg-type]
        )


def test_policy_flags_strategy_block_suggested_invalid_key_rejected():
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            strategy_block_suggested={"": True},  # blank
        )


def test_policy_flags_strategy_block_suggested_invalid_value_rejected():
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            strategy_block_suggested={"KIWOOM_PAPER": "YES"},  # type: ignore[dict-item]
        )


def test_policy_flags_cooldown_active_invalid_value_rejected():
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            cooldown_active={"KIWOOM_PAPER": 1},  # type: ignore[dict-item]
        )


def test_policy_flags_reason_codes_by_strategy_item_type_enforced():
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            reason_codes_by_strategy={"KIWOOM_PAPER": ["NOT_A_REASONCODE"]},  # type: ignore[list-item]
        )


def test_policy_flags_reason_codes_sample_must_be_list_of_str():
    ts = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            reason_codes_sample=[123],  # type: ignore[list-item]
        )