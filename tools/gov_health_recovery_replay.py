import os
import sys
from datetime import datetime, timedelta, timezone

# ============================================================
# GOV_HEALTH Recovery Replay
#   - Reproduces GREEN -> YELLOW -> RED -> YELLOW -> GREEN
#   - Uses synthetic time (no sleep) so it's deterministic/fast
#   - Writes:
#       runtime/observability/snapshots/health/YYYY-MM-DD/health.jsonl
#       runtime/observability/snapshots/transitions/YYYY-MM-DD/transitions.jsonl
# ============================================================

# ---- (A) 프로젝트 루트 import 안정화 (tools에서 실행 시 중요) ----
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from runtime.observability.health.evaluator import HealthEvaluator, HealthConfig
from runtime.observability.health.snapshot_emitter import SnapshotEmitter
from runtime.observability.health.contracts import IncidentEvent, Severity


STRATEGY_ID = "KIWOOM_PAPER"


def utc(dt: datetime) -> datetime:
    """Ensure UTC-aware datetime."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def print_eval(tag: str, result) -> None:
    g = result.global_snapshot
    snap = None
    for s in result.strategy_snapshots:
        if s.strategy_id == STRATEGY_ID:
            snap = s
            break

    print(f"\n[{tag}] ts_utc={result.ts_utc.isoformat()}")
    if snap:
        print(f"  strategy={snap.strategy_id} state={snap.state.value} score={snap.score:.3f} "
              f"cooldown={snap.cooldown_active} sustained_high={snap.sustained_high_score}")
        if snap.reason_codes:
            print("  reasons(top):", ", ".join([rc.render() for rc in snap.reason_codes[:3]]))
    print(f"  GLOBAL: {g.global_state.value} {g.global_score:.3f}")
    if result.transition_events:
        for e in result.transition_events:
            print(f"  TRANSITION: {e.strategy_id} {e.from_state.value}->{e.to_state.value} "
                  f"trigger={e.trigger.value} score={e.score_at_transition:.3f}")


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


def main():
    # ------------------------------------------------------------
    # Config tuned for fast deterministic replay (no sleeping)
    # ------------------------------------------------------------
    cfg = HealthConfig(
        evaluate_interval_sec=1,
        # Keep default hysteresis, but make windows/cooldowns short
        incident_window_sec=10,   # seconds
        cooldown_green_sec=2,     # seconds (GREEN<->YELLOW relaxation)
        cooldown_yellow_sec=2,    # seconds (RED relaxation)
        sustained_high_score_min_sec=5,  # not critical for this test
    )

    health = HealthEvaluator(cfg, strategy_weights={STRATEGY_ID: 1.0})

    # Emit every evaluate call (periodic interval=0 means "always eligible")
    emitter = SnapshotEmitter(
        base_dir=PROJECT_ROOT,
        snapshot_interval_sec=0,
        flush_each_write=True,
    )

    # Synthetic time base (UTC)
    t0 = utc(datetime.now(timezone.utc).replace(microsecond=0))

    # 0) Baseline GREEN (no incidents)
    r0 = health.evaluate(t0)
    emitter.emit_evaluation(r0)
    print_eval("0) BASELINE (expect GREEN)", r0)

    # 1) GREEN -> YELLOW
    #   score = max_w(SEV2=0.25) + freq_bonus(3 events => +0.10) => 0.35 (>= green_to_yellow)
    t1 = t0 + timedelta(seconds=1)
    ingest_many(health, t1, Severity.SEV2, "TEST_SEV2", n=3)
    r1 = health.evaluate(t1)
    emitter.emit_evaluation(r1)
    print_eval("1) INDUCE YELLOW (expect GREEN->YELLOW)", r1)

    # 2) YELLOW -> RED (SEV4 override)
    t2 = t1 + timedelta(seconds=1)
    ingest_many(health, t2, Severity.SEV4, "TEST_SEV4", n=1)
    r2 = health.evaluate(t2)
    emitter.emit_evaluation(r2)
    print_eval("2) INDUCE RED (expect YELLOW->RED)", r2)

    # 3) RED -> YELLOW recovery
    #   Need BOTH:
    #     - SEV4 falls out of incident window
    #     - cooldown_yellow_sec expires
    t3 = t2 + timedelta(seconds=cfg.incident_window_sec + cfg.cooldown_yellow_sec + 1)
    r3 = health.evaluate(t3)
    emitter.emit_evaluation(r3)
    print_eval("3) RECOVER to YELLOW (expect RED->YELLOW)", r3)

    # 4) YELLOW -> GREEN recovery
    #   Need cooldown_green_sec to expire after the RED->YELLOW transition
    t4 = t3 + timedelta(seconds=cfg.cooldown_green_sec + 1)
    r4 = health.evaluate(t4)
    emitter.emit_evaluation(r4)
    print_eval("4) RECOVER to GREEN (expect YELLOW->GREEN)", r4)

    print("\nDONE.")
    print(f"- health.jsonl: {PROJECT_ROOT}\\runtime\\observability\\snapshots\\health\\{t0.date()}\\health.jsonl")
    print(f"- transitions.jsonl: {PROJECT_ROOT}\\runtime\\observability\\snapshots\\transitions\\{t0.date()}\\transitions.jsonl")


if __name__ == "__main__":
    main()
