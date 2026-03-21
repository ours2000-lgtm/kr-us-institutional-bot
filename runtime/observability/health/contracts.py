from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple, Type, TypeVar

# -----------------------------
# Helpers (Contract Guards)
# -----------------------------
def require_utc_aware(dt: datetime) -> datetime:
    if not isinstance(dt, datetime):
        raise TypeError("ts_utc must be datetime")
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("ts_utc must be timezone-aware UTC datetime")
    return dt.astimezone(timezone.utc)


def require_nonblank_str(value: str, where: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{where} must be str")
    if value.strip() == "":
        raise ValueError(f"{where} must not be blank")
    return value


def require_bool(value: bool, where: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{where} must be bool")
    return value


E = TypeVar("E", bound=Enum)


def require_enum(value, enum_type: Type[E], where: str) -> E:
    # NOTE: We intentionally do NOT coerce strings into Enum here.
    # Contract: must be an Enum instance at runtime.
    if not isinstance(value, enum_type):
        raise TypeError(f"{where} must be {enum_type.__name__}")
    return value


def require_score_0_1(score: float, where: str = "score") -> float:
    if not isinstance(score, (int, float)):
        raise TypeError(f"{where} must be number")
    score_f = float(score)
    if not (0.0 <= score_f <= 1.0):
        raise ValueError(f"{where} must be in [0.0, 1.0]")
    return score_f


# -----------------------------
# Enums
# -----------------------------
class Severity(str, Enum):
    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"
    SEV4 = "SEV4"


class HealthState(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class TransitionTrigger(str, Enum):
    INCIDENT_OVERRIDE = "INCIDENT_OVERRIDE"
    SCORE_THRESHOLD = "SCORE_THRESHOLD"
    COOLDOWN_EXIT = "COOLDOWN_EXIT"
    SUSTAINED = "SUSTAINED"
    MANUAL = "MANUAL"


# -----------------------------
# Contracts
# -----------------------------
@dataclass(frozen=True)
class IncidentEvent:
    ts_utc: datetime
    strategy_id: str
    incident_code: str
    severity: Severity
    count: int = 1
    window_sec: int = 0
    trace_id: Optional[str] = None

    def __post_init__(self):
        object.__setattr__(self, "ts_utc", require_utc_aware(self.ts_utc))
        object.__setattr__(self, "strategy_id", require_nonblank_str(self.strategy_id, "IncidentEvent.strategy_id"))
        object.__setattr__(self, "incident_code", require_nonblank_str(self.incident_code, "IncidentEvent.incident_code"))
        object.__setattr__(self, "severity", require_enum(self.severity, Severity, "IncidentEvent.severity"))

        if not isinstance(self.count, int):
            raise TypeError("IncidentEvent.count must be int")
        if self.count <= 0:
            raise ValueError("IncidentEvent.count must be >= 1")

        if not isinstance(self.window_sec, int):
            raise TypeError("IncidentEvent.window_sec must be int")
        if self.window_sec < 0:
            raise ValueError("IncidentEvent.window_sec must be >= 0")

        if self.trace_id is not None and not isinstance(self.trace_id, str):
            raise TypeError("IncidentEvent.trace_id must be str or None")


@dataclass(frozen=True)
class ReasonCode:
    strategy_id: str
    severity: Severity
    count: int
    window_sec: int
    incident_code: str
    summary: Optional[str] = None

    def __post_init__(self):
        object.__setattr__(self, "strategy_id", require_nonblank_str(self.strategy_id, "ReasonCode.strategy_id"))
        object.__setattr__(self, "incident_code", require_nonblank_str(self.incident_code, "ReasonCode.incident_code"))
        object.__setattr__(self, "severity", require_enum(self.severity, Severity, "ReasonCode.severity"))

        if not isinstance(self.count, int):
            raise TypeError("ReasonCode.count must be int")
        if self.count <= 0:
            raise ValueError("ReasonCode.count must be >= 1")

        if not isinstance(self.window_sec, int):
            raise TypeError("ReasonCode.window_sec must be int")
        if self.window_sec < 0:
            raise ValueError("ReasonCode.window_sec must be >= 0")

        if self.summary is not None and not isinstance(self.summary, str):
            raise TypeError("ReasonCode.summary must be str or None")

    def render(self) -> str:
        window_min = max(1, int(self.window_sec // 60)) if self.window_sec else 0
        w = f"{window_min}m" if window_min else "0m"
        return f"{self.strategy_id}:{self.severity.value}:{self.count}/{w}:{self.incident_code}"


@dataclass(frozen=True)
class ContributorScore:
    strategy_id: str
    score: float

    def __post_init__(self):
        object.__setattr__(self, "strategy_id", require_nonblank_str(self.strategy_id, "ContributorScore.strategy_id"))
        object.__setattr__(self, "score", require_score_0_1(self.score, "ContributorScore.score"))


@dataclass
class StrategyHealthSnapshot:
    ts_utc: datetime
    strategy_id: str
    state: HealthState
    score: float
    sustained_high_score: bool
    cooldown_active: bool
    reason_codes: List[ReasonCode] = field(default_factory=list)

    def __post_init__(self):
        self.ts_utc = require_utc_aware(self.ts_utc)
        self.strategy_id = require_nonblank_str(self.strategy_id, "StrategyHealthSnapshot.strategy_id")
        self.state = require_enum(self.state, HealthState, "StrategyHealthSnapshot.state")
        self.score = require_score_0_1(self.score, "StrategyHealthSnapshot.score")
        self.sustained_high_score = require_bool(self.sustained_high_score, "StrategyHealthSnapshot.sustained_high_score")
        self.cooldown_active = require_bool(self.cooldown_active, "StrategyHealthSnapshot.cooldown_active")

        if not isinstance(self.reason_codes, list):
            raise TypeError("StrategyHealthSnapshot.reason_codes must be list")
        for i, rc in enumerate(self.reason_codes):
            if not isinstance(rc, ReasonCode):
                raise TypeError(f"StrategyHealthSnapshot.reason_codes[{i}] must be ReasonCode")


@dataclass
class GlobalHealthSnapshot:
    ts_utc: datetime
    global_state: HealthState
    global_score: float
    top_contributors: List[ContributorScore] = field(default_factory=list)
    reason_codes_sample: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.ts_utc = require_utc_aware(self.ts_utc)
        self.global_state = require_enum(self.global_state, HealthState, "GlobalHealthSnapshot.global_state")
        self.global_score = require_score_0_1(self.global_score, "GlobalHealthSnapshot.global_score")

        if not isinstance(self.top_contributors, list):
            raise TypeError("GlobalHealthSnapshot.top_contributors must be list")
        for i, c in enumerate(self.top_contributors):
            if not isinstance(c, ContributorScore):
                raise TypeError(f"GlobalHealthSnapshot.top_contributors[{i}] must be ContributorScore")

        if not isinstance(self.reason_codes_sample, list):
            raise TypeError("GlobalHealthSnapshot.reason_codes_sample must be list")
        for i, s in enumerate(self.reason_codes_sample):
            if not isinstance(s, str):
                raise TypeError(f"GlobalHealthSnapshot.reason_codes_sample[{i}] must be str")


@dataclass
class PolicyFlags:
    ts_utc: datetime
    feature_freeze_suggested: bool
    global_block_suggested: bool

    strategy_block_suggested: Dict[str, bool] = field(default_factory=dict)
    cooldown_active: Dict[str, bool] = field(default_factory=dict)

    reason_codes_by_strategy: Dict[str, List[ReasonCode]] = field(default_factory=dict)
    reason_codes_sample: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.ts_utc = require_utc_aware(self.ts_utc)
        self.feature_freeze_suggested = require_bool(self.feature_freeze_suggested, "PolicyFlags.feature_freeze_suggested")
        self.global_block_suggested = require_bool(self.global_block_suggested, "PolicyFlags.global_block_suggested")

        if not isinstance(self.strategy_block_suggested, dict):
            raise TypeError("PolicyFlags.strategy_block_suggested must be dict")
        for k, v in self.strategy_block_suggested.items():
            require_nonblank_str(k, "PolicyFlags.strategy_block_suggested key")
            if not isinstance(v, bool):
                raise TypeError("PolicyFlags.strategy_block_suggested values must be bool")

        if not isinstance(self.cooldown_active, dict):
            raise TypeError("PolicyFlags.cooldown_active must be dict")
        for k, v in self.cooldown_active.items():
            require_nonblank_str(k, "PolicyFlags.cooldown_active key")
            if not isinstance(v, bool):
                raise TypeError("PolicyFlags.cooldown_active values must be bool")

        if not isinstance(self.reason_codes_by_strategy, dict):
            raise TypeError("PolicyFlags.reason_codes_by_strategy must be dict")
        for sid, lst in self.reason_codes_by_strategy.items():
            require_nonblank_str(sid, "PolicyFlags.reason_codes_by_strategy key")
            if not isinstance(lst, list):
                raise TypeError("PolicyFlags.reason_codes_by_strategy values must be list[ReasonCode]")
            for i, rc in enumerate(lst):
                if not isinstance(rc, ReasonCode):
                    raise TypeError(f"PolicyFlags.reason_codes_by_strategy[{sid}][{i}] must be ReasonCode")

        if not isinstance(self.reason_codes_sample, list):
            raise TypeError("PolicyFlags.reason_codes_sample must be list")
        for i, s in enumerate(self.reason_codes_sample):
            if not isinstance(s, str):
                raise TypeError(f"PolicyFlags.reason_codes_sample[{i}] must be str")


@dataclass
class StateTransitionEvent:
    ts_utc: datetime
    strategy_id: str
    from_state: HealthState
    to_state: HealthState
    score_at_transition: float
    trigger: TransitionTrigger

    incident_override_applied: bool
    override_incident: Optional[IncidentEvent] = None

    sustained_high_score: bool = False
    cooldown_active: bool = False
    reason_codes: List[ReasonCode] = field(default_factory=list)

    def __post_init__(self):
        self.ts_utc = require_utc_aware(self.ts_utc)
        self.strategy_id = require_nonblank_str(self.strategy_id, "StateTransitionEvent.strategy_id")
        self.from_state = require_enum(self.from_state, HealthState, "StateTransitionEvent.from_state")
        self.to_state = require_enum(self.to_state, HealthState, "StateTransitionEvent.to_state")
        self.trigger = require_enum(self.trigger, TransitionTrigger, "StateTransitionEvent.trigger")

        if self.from_state == self.to_state:
            raise ValueError("StateTransitionEvent.from_state must not equal to_state")

        self.score_at_transition = require_score_0_1(self.score_at_transition, "StateTransitionEvent.score_at_transition")

        self.incident_override_applied = require_bool(
            self.incident_override_applied, "StateTransitionEvent.incident_override_applied"
        )
        if self.override_incident is not None and not isinstance(self.override_incident, IncidentEvent):
            raise TypeError("StateTransitionEvent.override_incident must be IncidentEvent or None")

        self.sustained_high_score = require_bool(self.sustained_high_score, "StateTransitionEvent.sustained_high_score")
        self.cooldown_active = require_bool(self.cooldown_active, "StateTransitionEvent.cooldown_active")

        if not isinstance(self.reason_codes, list):
            raise TypeError("StateTransitionEvent.reason_codes must be list")
        for i, rc in enumerate(self.reason_codes):
            if not isinstance(rc, ReasonCode):
                raise TypeError(f"StateTransitionEvent.reason_codes[{i}] must be ReasonCode")


@dataclass
class HealthEvaluationResult:
    ts_utc: datetime
    evaluation_window: Tuple[datetime, datetime]
    strategy_snapshots: List[StrategyHealthSnapshot]
    global_snapshot: GlobalHealthSnapshot
    policy_flags: PolicyFlags
    transition_events: List[StateTransitionEvent] = field(default_factory=list)

    def __post_init__(self):
        self.ts_utc = require_utc_aware(self.ts_utc)
        w0, w1 = self.evaluation_window
        self.evaluation_window = (require_utc_aware(w0), require_utc_aware(w1))

        if not isinstance(self.strategy_snapshots, list):
            raise TypeError("HealthEvaluationResult.strategy_snapshots must be list")
        for i, s in enumerate(self.strategy_snapshots):
            if not isinstance(s, StrategyHealthSnapshot):
                raise TypeError(f"HealthEvaluationResult.strategy_snapshots[{i}] must be StrategyHealthSnapshot")

        if not isinstance(self.global_snapshot, GlobalHealthSnapshot):
            raise TypeError("HealthEvaluationResult.global_snapshot must be GlobalHealthSnapshot")

        if not isinstance(self.policy_flags, PolicyFlags):
            raise TypeError("HealthEvaluationResult.policy_flags must be PolicyFlags")

        if not isinstance(self.transition_events, list):
            raise TypeError("HealthEvaluationResult.transition_events must be list")
        for i, e in enumerate(self.transition_events):
            if not isinstance(e, StateTransitionEvent):
                raise TypeError(f"HealthEvaluationResult.transition_events[{i}] must be StateTransitionEvent")