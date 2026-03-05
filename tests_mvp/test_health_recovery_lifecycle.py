# tests_mvp/test_health_recovery_lifecycle.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from runtime.observability.health.evaluator import HealthEvaluator, HealthConfig
from runtime.observability.health.contracts import IncidentEvent, Severity

STRATEGY_ID = "KIWOOM_PAPER"


def utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def ingest_many(health: HealthEvaluator, ts_utc: datetime, sev: Severity, code: str, n: int) -> None:
    for _ in range(n):
        health.ingest(
            IncidentEvent(
                ts_utc=ts_utc,
                strategy_id=STRATEGY_ID,
                incident_code=code,
                severity=sev,
                count=1,
            )
        )


def _get_strategy_snap(result, strategy_id: str):
    for s in result.strategy_snapshots:
        if s.strategy_id == strategy_id:
            return s
    raise AssertionError(f"strategy snapshot not found: {strategy_id}")


def _assert_transition(
    result,
    *,
    from_state: str,
    to_state: str,
    trigger: str,
    strategy_id: str = STRATEGY_ID,
):
    """
    result.transition_events:
      - strategy_id
      - from_state.value
      - to_state.value
      - trigger.value
    """
    events = getattr(result, "transition_events", []) or []
    for e in events:
        if (
            e.strategy_id == strategy_id
            and e.from_state.value == from_state
            and e.to_state.value == to_state
            and e.trigger.value == trigger
        ):
            return

    raise AssertionError(
        f"expected transition not found: {strategy_id} {from_state}->{to_state} trigger={trigger}\n"
        f"actual={[(x.strategy_id, x.from_state.value, x.to_state.value, x.trigger.value) for x in events]}"
    )


@pytest.mark.health
def test_health_recovery_lifecycle_red_yellow_green():
    """
    Deterministic replay (no sleep):
      GREEN -> YELLOW  (score threshold)
      YELLOW -> RED    (SEV4 incident override)
      RED -> YELLOW    (incident window out + cooldown exit)
      YELLOW -> GREEN  (cooldown exit)

    This test is the SSOT “복귀 테스트” 박제용.
    """

    cfg = HealthConfig(
        evaluate_interval_sec=1,
        incident_window_sec=10,  # short window for deterministic test
        cooldown_green_sec=2,  # short cooldown
        cooldown_yellow_sec=2,  # short cooldown for RED relaxation
        sustained_high_score_min_sec=5,
    )

    health = HealthEvaluator(cfg, strategy_weights={STRATEGY_ID: 1.0})

    # Fixed synthetic time base (UTC)
    t0 = utc(datetime(2026, 3, 2, 0, 0, 0, tzinfo=timezone.utc))

    # 0) Baseline GREEN
    r0 = health.evaluate(t0)
    s0 = _get_strategy_snap(r0, STRATEGY_ID)
    assert s0.state.value == "GREEN"
    assert r0.global_snapshot.global_state.value == "GREEN"

    # 1) Induce YELLOW
    # score = max_w(SEV2=0.25) + freq_bonus(3 events => +0.10) = 0.35
    t1 = t0 + timedelta(seconds=1)
    ingest_many(health, t1, Severity.SEV2, "TEST_SEV2", n=3)
    r1 = health.evaluate(t1)
    s1 = _get_strategy_snap(r1, STRATEGY_ID)
    assert s1.state.value == "YELLOW"
    assert r1.global_snapshot.global_state.value == "YELLOW"
    _assert_transition(r1, from_state="GREEN", to_state="YELLOW", trigger="SCORE_THRESHOLD")

    # 2) Induce RED via SEV4 override (score clamp 1.0)
    t2 = t1 + timedelta(seconds=1)
    ingest_many(health, t2, Severity.SEV4, "TEST_SEV4", n=1)
    r2 = health.evaluate(t2)
    s2 = _get_strategy_snap(r2, STRATEGY_ID)
    assert s2.state.value == "RED"
    assert abs(s2.score - 1.0) < 1e-9
    assert r2.global_snapshot.global_state.value == "RED"
    _assert_transition(r2, from_state="YELLOW", to_state="RED", trigger="INCIDENT_OVERRIDE")

    # 3) Recover to YELLOW:
    # need SEV4 out of window + cooldown_yellow_sec expired
    t3 = t2 + timedelta(seconds=cfg.incident_window_sec + cfg.cooldown_yellow_sec + 1)
    r3 = health.evaluate(t3)
    s3 = _get_strategy_snap(r3, STRATEGY_ID)
    assert s3.state.value == "YELLOW"
    _assert_transition(r3, from_state="RED", to_state="YELLOW", trigger="COOLDOWN_EXIT")

    # 4) Recover to GREEN:
    # need cooldown_green_sec expired after RED->YELLOW
    t4 = t3 + timedelta(seconds=cfg.cooldown_green_sec + 1)
    r4 = health.evaluate(t4)
    s4 = _get_strategy_snap(r4, STRATEGY_ID)
    assert s4.state.value == "GREEN"
    _assert_transition(r4, from_state="YELLOW", to_state="GREEN", trigger="COOLDOWN_EXIT")