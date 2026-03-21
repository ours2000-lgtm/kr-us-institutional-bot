# KR_US_INSTITUTION_BOT/src/fsm/canonicalize.py
from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


GENESIS_EVENT_TYPE = "RUN_START"
TRANSITION_EVENT_TYPE = "TRANSITION"

REQUIRED_GENESIS_FIELDS = {"trace_id", "ts_utc", "emitter_id"}


class CanonicalizeError(Exception):
    """
    Structured canonicalization error.
    - code: short id, e.g., G_GENESIS_MISSING
    - message: human message
    - event_index: index in the input list, if applicable
    - context: extra info
    """
    def __init__(
        self,
        code: str,
        message: str = "",
        *,
        event_index: int = -1,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message or code
        self.event_index = event_index
        self.context = context or {}
        super().__init__(f"{self.code}: {self.message}")


@dataclass(frozen=True)
class CanonicalTrace:
    trace_id: str
    genesis: Optional[Dict[str, Any]]
    transitions: List[Dict[str, Any]]   # safe copies (no caller side-effects)


def _parse_ts_utc(ts: Any, *, event_index: int = -1) -> datetime:
    if not isinstance(ts, str) or not ts.strip():
        raise CanonicalizeError(
            "G_TS_INVALID",
            "ts_utc must be a non-empty string",
            event_index=event_index,
        )
    try:
        s = ts.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).astimezone(timezone.utc)
    except Exception as e:
        raise CanonicalizeError(
            "G_TS_INVALID",
            f"cannot parse ts_utc ({e})",
            event_index=event_index,
        )


def _coerce_seq(seq: Any, *, event_index: int = -1) -> Optional[int]:
    if seq is None:
        return None
    try:
        return int(seq)
    except Exception:
        raise CanonicalizeError(
            "G_SEQ_INVALID",
            "seq must be int-castable",
            event_index=event_index,
        )


def _validate_genesis_envelope(genesis: Dict[str, Any]) -> None:
    missing = REQUIRED_GENESIS_FIELDS - set(genesis.keys())
    if missing:
        raise CanonicalizeError(
            "G_GENESIS_INVALID_ENVELOPE",
            f"missing={sorted(missing)}",
        )
    _parse_ts_utc(genesis.get("ts_utc"), event_index=-1)


def _extract_trace_id(events: List[Dict[str, Any]], genesis: Optional[Dict[str, Any]]) -> str:
    # 정책: genesis가 있으면 genesis.trace_id가 기준
    if genesis is not None:
        tid = genesis.get("trace_id")
        if isinstance(tid, str) and tid.strip():
            return tid.strip()
        raise CanonicalizeError("G_TRACE_ID_MISSING_IN_GENESIS", "GENESIS.trace_id is required")

    # 관용 모드(require_genesis=False)에서만 fallback
    for i, e in enumerate(events):
        tid = e.get("trace_id")
        if isinstance(tid, str) and tid.strip():
            return tid.strip()
    raise CanonicalizeError("G_TRACE_ID_MISSING", "trace_id is required")


def canonicalize_events(
    events: List[Dict[str, Any]],
    *,
    require_genesis: bool = True,
) -> CanonicalTrace:
    if not isinstance(events, list):
        raise CanonicalizeError("G_EVENTS_INVALID", "events must be a list")

    # ✅ side-effect 방지: deep copy
    events_copy: List[Dict[str, Any]] = copy.deepcopy(events)

    genesis_events = [e for e in events_copy if e.get("event_type") == GENESIS_EVENT_TYPE]
    if len(genesis_events) > 1:
        raise CanonicalizeError("G_GENESIS_MULTIPLE", "RUN_START must appear at most once")

    genesis = genesis_events[0] if genesis_events else None
    if require_genesis and genesis is None:
        raise CanonicalizeError("G_GENESIS_MISSING", "RUN_START is required")

    if genesis is not None:
        _validate_genesis_envelope(genesis)

    trace_id = _extract_trace_id(events_copy, genesis)

    # trace_id mismatch fail-closed
    for i, e in enumerate(events_copy):
        if e.get("trace_id") != trace_id:
            raise CanonicalizeError(
                "G_TRACE_ID_MISMATCH",
                "trace_id mismatch within trace",
                event_index=i,
                context={"expected": trace_id, "got": e.get("trace_id")},
            )

    # GENESIS 제외: transition 검증 입력에서 제거
    transitions = [e for e in events_copy if e.get("event_type") != GENESIS_EVENT_TYPE]

    # 내부 파생 필드는 copy본에만 주입 (caller 원본 불변)
    for i, e in enumerate(transitions):
        e["_seq_int"] = _coerce_seq(e.get("seq"), event_index=i)
        e["_ts_dt"] = _parse_ts_utc(e.get("ts_utc"), event_index=i) if e.get("ts_utc") is not None else None

    # 정렬 정책: seq 우선, seq 없으면 뒤로 보내고 ts 오름차순
    def sort_key(e: Dict[str, Any]) -> Tuple[int, float]:
        seq = e.get("_seq_int")
        ts = e.get("_ts_dt")
        seq_key = seq if seq is not None else 10**18
        ts_key = ts.timestamp() if ts is not None else 0.0
        return (seq_key, ts_key)

    transitions_sorted = sorted(transitions, key=sort_key)

    return CanonicalTrace(trace_id=trace_id, genesis=genesis, transitions=transitions_sorted)
