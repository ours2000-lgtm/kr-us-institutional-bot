import os
import sys
from datetime import datetime, timedelta, timezone

# ---- 프로젝트 루트 import 안정화 (pytest 실행 위치가 달라도 동작) ----
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from runtime.observability.health.evaluator import HealthEvaluator, HealthConfig
from runtime.observability.health.contracts import IncidentEvent, Severity


STRATEGY_ID = "KIWOOM_PAPER"


def utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_strategy_snapshot(result, strategy_id: str):
    for s in result.strategy_snapshots:
        if s.strategy_id == strategy_id:
            return s
    raise AssertionError(f"strategy snapshot not found: {strategy_id}")


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


def flatten_transitions(*results):
    out = []
    for r in results:
        if getattr(r, "transition_events", None):
            out.extend(r.transition_events)
    return out


def test_gov_health_recovery_replay_green_yellow_red_yellow_green():
    """
    Deterministic replay:
      0) BASELINE: GREEN
      1) INDUCE YELLOW: score threshold (SEV2 x3 => 0.35)
      2) INDUCE RED: incident override (SEV4 => clamp 1.0)
      3) RECOVER to YELLOW: after incident window + cooldown_yellow
      4) RECOVER to GREEN: after cooldown_green
    Assertions:
      - states match expected
      - transition sequence and triggers match expected
    """

    # Fast deterministic settings (no sleep)
    cfg = HealthConfig(
        evaluate_interval_sec=1,
        incident_window_sec=10,
        cooldown_green_sec=2,
        cooldown_yellow_sec=2,
        sustained_high_score_min_sec=5,
    )

    health = HealthEvaluator(cfg, strategy_weights={STRATEGY_ID: 1.0})

    # Fixed time base (UTC) for determinism
    t0 = utc(datetime(2026, 3, 2, 13, 28, 9, tzinfo=timezone.utc))

    # 0) Baseline
    r0 = health.evaluate(t0)
    s0 = get_strategy_snapshot(r0, STRATEGY_ID)
    assert s0.state.value == "GREEN"
    assert abs(s0.score - 0.0) < 1e-9
    assert r0.transition_events == []

    # 1) GREEN -> YELLOW
    # SEV2 weight(=0.25) + freq_bonus for 3 events(=+0.10) => 0.35
    t1 = t0 + timedelta(seconds=1)
    ingest_many(health, t1, Severity.SEV2, "TEST_SEV2", n=3)
    r1 = health.evaluate(t1)
    s1 = get_strategy_snapshot(r1, STRATEGY_ID)
    assert s1.state.value == "YELLOW"
    assert abs(s1.score - 0.35) < 1e-6
    assert len(r1.transition_events) >= 1  # should contain GREEN->YELLOW

    # 2) YELLOW -> RED (incident override)
    t2 = t1 + timedelta(seconds=1)
    ingest_many(health, t2, Severity.SEV4, "TEST_SEV4", n=1)
    r2 = health.evaluate(t2)
    s2 = get_strategy_snapshot(r2, STRATEGY_ID)
    assert s2.state.value == "RED"
    assert abs(s2.score - 1.0) < 1e-9
    assert len(r2.transition_events) >= 1  # should contain YELLOW->RED

    # 3) RED -> YELLOW recovery
    t3 = t2 + timedelta(seconds=cfg.incident_window_sec + cfg.cooldown_yellow_sec + 1)
    r3 = health.evaluate(t3)
    s3 = get_strategy_snapshot(r3, STRATEGY_ID)
    assert s3.state.value == "YELLOW"
    assert abs(s3.score - 0.0) < 1e-9
    assert len(r3.transition_events) >= 1  # should contain RED->YELLOW

    # 4) YELLOW -> GREEN recovery
    t4 = t3 + timedelta(seconds=cfg.cooldown_green_sec + 1)
    r4 = health.evaluate(t4)
    s4 = get_strategy_snapshot(r4, STRATEGY_ID)
    assert s4.state.value == "GREEN"
    assert abs(s4.score - 0.0) < 1e-9
    assert len(r4.transition_events) >= 1  # should contain YELLOW->GREEN

    # ---- Transition contract assertions (sequence + triggers) ----
    transitions = flatten_transitions(r1, r2, r3, r4)

    # We expect at least these 4 strategy transitions in order.
    # (If you later add extra transitions, we still validate the core subsequence.)
    expected = [
        ("GREEN", "YELLOW", "SCORE_THRESHOLD"),
        ("YELLOW", "RED", "INCIDENT_OVERRIDE"),
        ("RED", "YELLOW", "COOLDOWN_EXIT"),
        ("YELLOW", "GREEN", "COOLDOWN_EXIT"),
    ]

    core = []
    for e in transitions:
        if e.strategy_id != STRATEGY_ID:
            continue
        core.append((e.from_state.value, e.to_state.value, e.trigger.value))

    # Validate that expected sequence appears as a prefix (strictest, matches current behavior)
    assert core[:4] == expected, f"transition sequence mismatch: got={core}"