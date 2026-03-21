from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .contracts import (
    ContributorScore,
    GlobalHealthSnapshot,
    HealthEvaluationResult,
    PolicyFlags,
    ReasonCode,
    StateTransitionEvent,
    StrategyHealthSnapshot,
    require_utc_aware,
)


def _iso_z(dt: datetime) -> str:
    dt = require_utc_aware(dt)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _to_jsonable(obj: Any) -> Any:
    # dataclass → dict
    if is_dataclass(obj):
        d = asdict(obj)
        return _to_jsonable(d)

    if isinstance(obj, datetime):
        return _iso_z(obj)

    if isinstance(obj, ReasonCode):
        # 기본은 구조 + render를 같이 넣어준다(운영자/머신 둘 다)
        return {
            "strategy_id": obj.strategy_id,
            "severity": obj.severity.value,
            "count": obj.count,
            "window_sec": obj.window_sec,
            "incident_code": obj.incident_code,
            "summary": obj.summary,
            "rendered": obj.render(),
        }

    if isinstance(obj, ContributorScore):
        return {"strategy_id": obj.strategy_id, "score": obj.score}

    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]

    return obj


class SnapshotEmitter:
    """
    jsonl emitter with IO-stability policy:
      - always emit transition events immediately
      - periodic snapshots at snapshot_interval_sec (default 60s)
    """

    def __init__(
        self,
        base_dir: str | Path,
        snapshot_interval_sec: int = 60,
        flush_each_write: bool = True,
    ):
        self.base_dir = Path(base_dir)
        self.snapshot_interval_sec = snapshot_interval_sec
        self.flush_each_write = flush_each_write

        self._last_periodic_emit_at: Optional[datetime] = None

    # -------------
    # Public API
    # -------------

    def emit_evaluation(self, result: HealthEvaluationResult) -> None:
        """
        Apply emission policy:
          1) Emit all transition events immediately
          2) Emit periodic snapshots only if interval elapsed
        """
        now = require_utc_aware(result.ts_utc)

        # 1) transitions always
        if result.transition_events:
            self.emit_transition_events(result.transition_events, now)

            # transition과 함께 스냅샷/flags도 바로 남기는 편이 운영상 유리
            self.emit_strategy_snapshots(result.strategy_snapshots, now)
            self.emit_global_snapshot(result.global_snapshot, now)
            self.emit_policy_flags(result.policy_flags, now)
            return

        # 2) periodic
        if self._should_emit_periodic(now):
            self.emit_strategy_snapshots(result.strategy_snapshots, now)
            self.emit_global_snapshot(result.global_snapshot, now)
            self.emit_policy_flags(result.policy_flags, now)
            self._last_periodic_emit_at = now

    def emit_transition_events(self, events: List[StateTransitionEvent], now_utc: datetime) -> None:
        path = self._path_for("transitions", now_utc, "transitions.jsonl")
        for e in events:
            rec = {
                "type": "state_transition_event",
                "ts_utc": _iso_z(e.ts_utc),
                "strategy_id": e.strategy_id,
                "from": e.from_state.value,
                "to": e.to_state.value,
                "score_at_transition": e.score_at_transition,
                "trigger": e.trigger.value,
                "incident_override_applied": e.incident_override_applied,
                "override_incident": _to_jsonable(e.override_incident) if e.override_incident else None,
                "sustained_high_score": e.sustained_high_score,
                "cooldown_active": e.cooldown_active,
                "reason_codes": _to_jsonable(e.reason_codes),
            }
            self._append_jsonl(path, rec)

    def emit_strategy_snapshots(self, snaps: List[StrategyHealthSnapshot], now_utc: datetime) -> None:
        path = self._path_for("health", now_utc, "health.jsonl")
        for s in snaps:
            rec = {
                "type": "strategy_health_snapshot",
                "ts_utc": _iso_z(s.ts_utc),
                "strategy_id": s.strategy_id,
                "state": s.state.value,
                "score": s.score,
                "sustained_high_score": s.sustained_high_score,
                "cooldown_active": s.cooldown_active,
                "reason_codes": _to_jsonable(s.reason_codes),
                "reason_codes_rendered": [rc.render() for rc in s.reason_codes],
            }
            self._append_jsonl(path, rec)

    def emit_global_snapshot(self, snap: GlobalHealthSnapshot, now_utc: datetime) -> None:
        path = self._path_for("health", now_utc, "health.jsonl")
        rec = {
            "type": "global_health_snapshot",
            "ts_utc": _iso_z(snap.ts_utc),
            "global_state": snap.global_state.value,
            "global_score": snap.global_score,
            "top_contributors": _to_jsonable(snap.top_contributors),
            "reason_codes_sample": list(snap.reason_codes_sample),
        }
        self._append_jsonl(path, rec)

    def emit_policy_flags(self, flags: PolicyFlags, now_utc: datetime) -> None:
        path = self._path_for("health", now_utc, "health.jsonl")
        # reason_codes_by_strategy는 구조화 유지 + rendered 병기
        rendered_by_strategy: Dict[str, List[str]] = {
            sid: [rc.render() for rc in rcs] for sid, rcs in flags.reason_codes_by_strategy.items()
        }
        rec = {
            "type": "policy_flags_snapshot",
            "ts_utc": _iso_z(flags.ts_utc),
            "feature_freeze_suggested": flags.feature_freeze_suggested,
            "global_block_suggested": flags.global_block_suggested,
            "strategy_block_suggested": dict(flags.strategy_block_suggested),
            "cooldown_active": dict(flags.cooldown_active),
            "reason_codes_by_strategy": _to_jsonable(flags.reason_codes_by_strategy),
            "reason_codes_by_strategy_rendered": rendered_by_strategy,
            "reason_codes_sample": list(flags.reason_codes_sample),
        }
        self._append_jsonl(path, rec)

    # -------------
    # Internals
    # -------------

    def _should_emit_periodic(self, now_utc: datetime) -> bool:
        if self._last_periodic_emit_at is None:
            return True
        elapsed = (now_utc - self._last_periodic_emit_at).total_seconds()
        return elapsed >= self.snapshot_interval_sec

    def _path_for(self, category: str, now_utc: datetime, filename: str) -> Path:
        d = require_utc_aware(now_utc).astimezone(timezone.utc).strftime("%Y-%m-%d")
        path = self.base_dir / "runtime" / "observability" / "snapshots" / category / d
        path.mkdir(parents=True, exist_ok=True)
        return path / filename

    def _append_jsonl(self, path: Path, record: Dict[str, Any]) -> None:
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            if self.flush_each_write:
                f.flush()