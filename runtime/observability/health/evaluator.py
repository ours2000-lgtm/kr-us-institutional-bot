from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple

from .contracts import (
    ContributorScore,
    GlobalHealthSnapshot,
    HealthEvaluationResult,
    HealthState,
    IncidentEvent,
    PolicyFlags,
    ReasonCode,
    Severity,
    StateTransitionEvent,
    StrategyHealthSnapshot,
    TransitionTrigger,
    require_utc_aware,
)


def _state_rank(st: HealthState) -> int:
    return {HealthState.GREEN: 0, HealthState.YELLOW: 1, HealthState.RED: 2}[st]


def max_state(a: HealthState, b: HealthState) -> HealthState:
    return a if _state_rank(a) >= _state_rank(b) else b


@dataclass
class HealthConfig:
    evaluate_interval_sec: int = 10
    high_sensitivity_mode: bool = False

    # hysteresis thresholds
    green_to_yellow: float = 0.35
    yellow_to_green: float = 0.25
    yellow_to_red: float = 0.70
    red_to_yellow: float = 0.55

    # sustained
    sustained_high_score_threshold: float = 0.60
    sustained_high_score_min_sec: int = 30 * 60

    # cooldown
    cooldown_green_sec: int = 30 * 60
    cooldown_yellow_sec: int = 20 * 60

    # incident window
    incident_window_sec: int = 15 * 60  # 15m

    # global
    global_red_score_threshold: float = 0.70
    global_red_if_red_strategies_at_least: int = 2
    global_min_yellow_if_any_strategy_score_is_1: bool = True

    # optional policy knobs
    sev3_single_bumps_to_yellow: bool = False
    sustained_yellow_to_red_enabled: bool = False
    sustained_yellow_min_sec: int = 30 * 60  # if enabled


class HealthEvaluator:
    """
    Execution model:
    - ingest(event): event-driven, O(1), non-blocking, stores incidents
    - evaluate(now): time-driven, recompute score/state/flags/snapshots
    """

    def __init__(self, config: HealthConfig, strategy_weights: Optional[Dict[str, float]] = None):
        self.cfg = config
        self.strategy_weights = strategy_weights or {}

        # strategy_id -> deque[IncidentEvent], ts-ordered by ingest time
        self._buf: Dict[str, Deque[IncidentEvent]] = {}

        # state memory
        self._state: Dict[str, HealthState] = {}
        self._last_transition_at: Dict[str, datetime] = {}

        # sustained trackers
        self._high_score_since: Dict[str, Optional[datetime]] = {}
        self._yellow_since: Dict[str, Optional[datetime]] = {}

        # last computed
        self._last_score: Dict[str, float] = {}
        self._last_reasons: Dict[str, List[ReasonCode]] = {}

    # ---------------------------
    # Public API
    # ---------------------------

    def ingest(self, event: IncidentEvent) -> None:
        # Contract already enforces UTC-aware; keep O(1)
        dq = self._buf.setdefault(event.strategy_id, deque())
        dq.append(event)

    def evaluate(self, now_utc: datetime) -> HealthEvaluationResult:
        now_utc = require_utc_aware(now_utc)

        window_start = now_utc - timedelta(seconds=self.cfg.incident_window_sec)
        evaluation_window = (window_start, now_utc)

        # Per-strategy compute
        strategy_snaps: List[StrategyHealthSnapshot] = []
        transition_events: List[StateTransitionEvent] = []

        for strategy_id in self._all_strategies():
            self._trim_strategy(strategy_id, window_start)

            score, override_target, override_incident, reasons = self._compute_score_and_reasons(
                strategy_id=strategy_id,
                window_start=window_start,
                now_utc=now_utc,
            )

            sustained_high = self._compute_sustained_high_score(strategy_id, score, now_utc)
            cooldown_active = self._cooldown_active(strategy_id, now_utc)

            new_state, trigger = self._compute_state_transition(
                strategy_id=strategy_id,
                score=score,
                override_target_state=override_target,
                override_incident=override_incident,
                sustained_high_score=sustained_high,
                now_utc=now_utc,
            )

            old_state = self._state.get(strategy_id, HealthState.GREEN)
            if new_state != old_state:
                self._state[strategy_id] = new_state
                self._last_transition_at[strategy_id] = now_utc

                transition_events.append(
                    StateTransitionEvent(
                        ts_utc=now_utc,
                        strategy_id=strategy_id,
                        from_state=old_state,
                        to_state=new_state,
                        score_at_transition=score,
                        trigger=trigger,
                        incident_override_applied=(override_target is not None),
                        override_incident=override_incident,
                        sustained_high_score=sustained_high,
                        cooldown_active=cooldown_active,
                        reason_codes=list(reasons),
                    )
                )

            # update yellow_since tracker (for optional sustained_yellow_to_red)
            self._update_yellow_since(strategy_id, now_utc)

            self._last_score[strategy_id] = score
            self._last_reasons[strategy_id] = list(reasons)

            strategy_snaps.append(
                StrategyHealthSnapshot(
                    ts_utc=now_utc,
                    strategy_id=strategy_id,
                    state=self._state.get(strategy_id, HealthState.GREEN),
                    score=score,
                    sustained_high_score=sustained_high,
                    cooldown_active=cooldown_active,
                    reason_codes=list(reasons),
                )
            )

        # Global
        global_snap = self._compute_global(now_utc, strategy_snaps)

        # Flags (Gate input)
        flags = self._build_policy_flags(now_utc, strategy_snaps, global_snap)

        return HealthEvaluationResult(
            ts_utc=now_utc,
            evaluation_window=evaluation_window,
            strategy_snapshots=strategy_snaps,
            global_snapshot=global_snap,
            policy_flags=flags,
            transition_events=transition_events,
        )

    # ---------------------------
    # Internal helpers
    # ---------------------------

    def _all_strategies(self) -> List[str]:
        s = set(self._buf.keys()) | set(self._state.keys()) | set(self.strategy_weights.keys())
        return sorted(s)

    def _trim_strategy(self, strategy_id: str, cutoff: datetime) -> None:
        dq = self._buf.get(strategy_id)
        if not dq:
            return
        # popleft while old
        while dq and dq[0].ts_utc < cutoff:
            dq.popleft()

    def _severity_weight(self, sev: Severity) -> float:
        return {
            Severity.SEV1: 0.10,
            Severity.SEV2: 0.25,
            Severity.SEV3: 0.60,
            Severity.SEV4: 1.00,
        }[sev]

    def _compute_score_and_reasons(
        self,
        strategy_id: str,
        window_start: datetime,
        now_utc: datetime,
    ) -> Tuple[float, Optional[HealthState], Optional[IncidentEvent], List[ReasonCode]]:
        """
        Returns:
          score,
          override_target_state (None if no override),
          override_incident (None if no override),
          reason_codes (structured)
        SSOT:
          - SEV4 in window => score=1.0 clamp, override_target_state=RED
          - reason_codes are structured; render at output time
        """
        dq = self._buf.get(strategy_id)
        if not dq:
            return 0.0, None, None, []

        # Aggregate counts by (severity, incident_code)
        counts: Dict[Tuple[Severity, str], int] = {}
        has_sev4: Optional[IncidentEvent] = None
        has_sev3 = False
        total_events = 0
        max_w = 0.0

        for e in dq:
            if e.ts_utc < window_start:
                continue
            total_events += e.count
            counts[(e.severity, e.incident_code)] = counts.get((e.severity, e.incident_code), 0) + e.count
            w = self._severity_weight(e.severity)
            if w > max_w:
                max_w = w
            if e.severity == Severity.SEV4 and has_sev4 is None:
                has_sev4 = e
            if e.severity == Severity.SEV3:
                has_sev3 = True

        # Build structured reasons (sorted severity desc, count desc)
        window_sec = self.cfg.incident_window_sec
        reasons: List[ReasonCode] = []
        for (sev, code), c in counts.items():
            reasons.append(
                ReasonCode(
                    strategy_id=strategy_id,
                    severity=sev,
                    count=c,
                    window_sec=window_sec,
                    incident_code=code,
                )
            )
        reasons.sort(
    key=lambda r: (self._severity_weight(r.severity), r.count),
    reverse=True,
)

        # Optional: SEV3 단발로 YELLOW bump 정책 (override가 아닌 "정책 트리거"로만 사용)
        # (여기서는 score에만 간접 반영하고, state 로직은 별도에서 처리 가능)

        # SEV4 override
        if has_sev4 is not None:
            return 1.0, HealthState.RED, has_sev4, reasons

        # Score skeleton (안정적/단순/설명 가능)
        # - max severity 기반 + 빈도 기반 보조
        # - 이 산식은 추후 교체 가능(SSOT는 "SEV4 clamp"와 "0..1"만 고정)
        freq_bonus = min(0.30, max(0.0, 0.05 * (total_events - 1)))
        score = max_w + freq_bonus
        score = max(0.0, min(1.0, score))

        # If policy wants: SEV3 단발이면 최소 0.35 이상으로 올려 YELLOW 진입을 유도
        if self.cfg.sev3_single_bumps_to_yellow and has_sev3:
            score = max(score, self.cfg.green_to_yellow)

        return score, None, None, reasons

    def _compute_sustained_high_score(self, strategy_id: str, score: float, now_utc: datetime) -> bool:
        thr = self.cfg.sustained_high_score_threshold
        if score >= thr:
            if self._high_score_since.get(strategy_id) is None:
                self._high_score_since[strategy_id] = now_utc
            since = self._high_score_since[strategy_id]
            assert since is not None
            return (now_utc - since).total_seconds() >= self.cfg.sustained_high_score_min_sec
        else:
            self._high_score_since[strategy_id] = None
            return False

    def _update_yellow_since(self, strategy_id: str, now_utc: datetime) -> None:
        st = self._state.get(strategy_id, HealthState.GREEN)
        if st == HealthState.YELLOW:
            if self._yellow_since.get(strategy_id) is None:
                self._yellow_since[strategy_id] = now_utc
        else:
            self._yellow_since[strategy_id] = None

    def _cooldown_active(self, strategy_id: str, now_utc: datetime) -> bool:
        last = self._last_transition_at.get(strategy_id)
        if not last:
            return False
        st = self._state.get(strategy_id, HealthState.GREEN)
        # GREEN↔YELLOW 완화에는 green cooldown, RED 완화에는 yellow cooldown을 사용
        cd = self.cfg.cooldown_green_sec if st != HealthState.RED else self.cfg.cooldown_yellow_sec
        return (now_utc - last).total_seconds() < cd

    def _compute_state_transition(
        self,
        strategy_id: str,
        score: float,
        override_target_state: Optional[HealthState],
        override_incident: Optional[IncidentEvent],
        sustained_high_score: bool,
        now_utc: datetime,
    ) -> Tuple[HealthState, TransitionTrigger]:
        old = self._state.get(strategy_id, HealthState.GREEN)

        # 1) Incident-First Override (SSOT)
        if override_target_state is not None:
            target = max_state(old, override_target_state)
            if target != old:
                return target, TransitionTrigger.INCIDENT_OVERRIDE
            return old, TransitionTrigger.INCIDENT_OVERRIDE

        # 2) Optional sustained(YELLOW)->RED (정책 옵션)
        if self.cfg.sustained_yellow_to_red_enabled and old == HealthState.YELLOW:
            since = self._yellow_since.get(strategy_id)
            if since is not None:
                if (now_utc - since).total_seconds() >= self.cfg.sustained_yellow_min_sec:
                    return HealthState.RED, TransitionTrigger.SUSTAINED

        # 3) Score-driven hysteresis
        if old == HealthState.GREEN and score >= self.cfg.green_to_yellow:
            return HealthState.YELLOW, TransitionTrigger.SCORE_THRESHOLD

        if old == HealthState.YELLOW:
            if score >= self.cfg.yellow_to_red:
                return HealthState.RED, TransitionTrigger.SCORE_THRESHOLD
            if score < self.cfg.yellow_to_green and not self._cooldown_active(strategy_id, now_utc):
                return HealthState.GREEN, TransitionTrigger.COOLDOWN_EXIT

        if old == HealthState.RED:
            if score < self.cfg.red_to_yellow and not self._cooldown_active(strategy_id, now_utc):
                return HealthState.YELLOW, TransitionTrigger.COOLDOWN_EXIT

        return old, TransitionTrigger.SCORE_THRESHOLD

    def _compute_global(self, now_utc: datetime, strategy_snaps: List[StrategyHealthSnapshot]) -> GlobalHealthSnapshot:
        total_weighted = 0.0
        total_w = 0.0
        any_score_one = False
        red_count = 0

        contributors: List[ContributorScore] = []

        for s in strategy_snaps:
            w = self.strategy_weights.get(s.strategy_id, 1.0)
            total_weighted += w * s.score
            total_w += w

            contributors.append(ContributorScore(strategy_id=s.strategy_id, score=s.score))

            if s.score >= 1.0:
                any_score_one = True
            if s.state == HealthState.RED:
                red_count += 1

        global_score = (total_weighted / total_w) if total_w > 0 else 0.0
        global_score = max(0.0, min(1.0, global_score))

        # Global state priority rules
        if red_count >= self.cfg.global_red_if_red_strategies_at_least:
            global_state = HealthState.RED
        elif global_score >= self.cfg.global_red_score_threshold:
            global_state = HealthState.RED
        elif self.cfg.global_min_yellow_if_any_strategy_score_is_1 and any_score_one:
            global_state = HealthState.YELLOW
        else:
            global_state = HealthState.GREEN if global_score < 0.25 else HealthState.YELLOW

        # Top contributors by score
        top = sorted(contributors, key=lambda c: c.score, reverse=True)[:3]

        # Sample reason codes: pick 1 from top strategies if exists
        reason_sample: List[str] = []
        for c in top:
            rs = self._last_reasons.get(c.strategy_id, [])
            if rs:
                reason_sample.append(rs[0].render())
            if len(reason_sample) >= 3:
                break

        return GlobalHealthSnapshot(
            ts_utc=now_utc,
            global_state=global_state,
            global_score=global_score,
            top_contributors=top,
            reason_codes_sample=reason_sample,
        )

    def _build_policy_flags(
        self,
        now_utc: datetime,
        strategy_snaps: List[StrategyHealthSnapshot],
        global_snap: GlobalHealthSnapshot,
    ) -> PolicyFlags:
        strategy_block = {s.strategy_id: (s.state == HealthState.RED) for s in strategy_snaps}
        cooldown = {s.strategy_id: s.cooldown_active for s in strategy_snaps}

        global_block = (global_snap.global_state == HealthState.RED)
        feature_freeze = (global_snap.global_state != HealthState.GREEN)

        reason_by_strategy: Dict[str, List[ReasonCode]] = {s.strategy_id: list(s.reason_codes) for s in strategy_snaps}

        # global sample: keep short rendered strings
        sample: List[str] = []
        for s in strategy_snaps:
            if s.reason_codes:
                sample.append(s.reason_codes[0].render())
            if len(sample) >= 5:
                break

        return PolicyFlags(
            ts_utc=now_utc,
            feature_freeze_suggested=feature_freeze,
            global_block_suggested=global_block,
            strategy_block_suggested=strategy_block,
            cooldown_active=cooldown,
            reason_codes_by_strategy=reason_by_strategy,
            reason_codes_sample=sample,
        )