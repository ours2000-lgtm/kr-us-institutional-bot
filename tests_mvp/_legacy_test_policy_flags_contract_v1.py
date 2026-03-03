# tests_mvp/test_policy_flags_contract_v1.py
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from runtime.observability.health.contracts import PolicyFlags, ReasonCode, Severity


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _mk_reason(strategy_id: str = "KIWOOM_PAPER") -> ReasonCode:
    return ReasonCode(
        strategy_id=strategy_id,
        severity=Severity.SEV2,
        count=1,
        window_sec=60,
        incident_code="TEST_INCIDENT",
        summary="test",
    )


def test_policy_flags_valid_minimal():
    ts = _utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))

    pf = PolicyFlags(
        ts_utc=ts,
        feature_freeze_suggested=False,
        global_block_suggested=False,
    )

    # 핵심 필드 타입/존재
    assert pf.ts_utc.tzinfo is not None
    assert pf.ts_utc.utcoffset() is not None
    assert pf.ts_utc.astimezone(timezone.utc) == pf.ts_utc

    assert isinstance(pf.feature_freeze_suggested, bool)
    assert isinstance(pf.global_block_suggested, bool)

    # 기본 컨테이너 초기화
    assert isinstance(pf.strategy_block_suggested, dict)
    assert isinstance(pf.cooldown_active, dict)
    assert isinstance(pf.reason_codes_by_strategy, dict)
    assert isinstance(pf.reason_codes_sample, list)


def test_policy_flags_ts_must_be_utc_aware():
    ts_naive = datetime(2026, 3, 2, 0, 0, 0)  # naive

    with pytest.raises(ValueError):
        PolicyFlags(
            ts_utc=ts_naive,
            feature_freeze_suggested=False,
            global_block_suggested=False,
        )


def test_policy_flags_bool_fields_must_be_bool():
    ts = _utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))

    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(  # type: ignore[arg-type]
            ts_utc=ts,
            feature_freeze_suggested="no",  # not bool
            global_block_suggested=False,
        )

    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(  # type: ignore[arg-type]
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=1,  # not bool
        )


def test_policy_flags_strategy_maps_must_be_dict_str_bool():
    ts = _utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))

    # wrong container type
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(  # type: ignore[arg-type]
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            strategy_block_suggested=["KIWOOM_PAPER"],  # not dict
        )

    # wrong value type
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(  # type: ignore[arg-type]
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            strategy_block_suggested={"KIWOOM_PAPER": "BLOCK"},  # not bool
        )

    # wrong key type
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(  # type: ignore[arg-type]
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            strategy_block_suggested={1: True},  # key not str
        )


def test_policy_flags_reason_codes_by_strategy_shape():
    ts = _utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))

    # valid
    pf = PolicyFlags(
        ts_utc=ts,
        feature_freeze_suggested=True,
        global_block_suggested=False,
        reason_codes_by_strategy={"KIWOOM_PAPER": [_mk_reason("KIWOOM_PAPER")]},
    )
    assert "KIWOOM_PAPER" in pf.reason_codes_by_strategy
    assert isinstance(pf.reason_codes_by_strategy["KIWOOM_PAPER"], list)
    assert isinstance(pf.reason_codes_by_strategy["KIWOOM_PAPER"][0], ReasonCode)

    # wrong: value not list
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(  # type: ignore[arg-type]
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            reason_codes_by_strategy={"KIWOOM_PAPER": _mk_reason("KIWOOM_PAPER")},  # not list
        )

    # wrong: list item not ReasonCode
    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(  # type: ignore[arg-type]
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            reason_codes_by_strategy={"KIWOOM_PAPER": ["NOT_REASONCODE"]},
        )


def test_policy_flags_reason_codes_sample_must_be_list_str():
    ts = _utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))

    pf = PolicyFlags(
        ts_utc=ts,
        feature_freeze_suggested=False,
        global_block_suggested=False,
        reason_codes_sample=["A", "B"],
    )
    assert pf.reason_codes_sample == ["A", "B"]

    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(  # type: ignore[arg-type]
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            reason_codes_sample="A",  # not list
        )

    with pytest.raises((TypeError, ValueError)):
        PolicyFlags(  # type: ignore[arg-type]
            ts_utc=ts,
            feature_freeze_suggested=False,
            global_block_suggested=False,
            reason_codes_sample=["A", 2],  # item not str
        )