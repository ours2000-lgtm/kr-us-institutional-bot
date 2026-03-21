from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


def require_utc_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("ts_utc must be timezone-aware UTC datetime")
    return dt.astimezone(timezone.utc)


class Decision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


class Grade(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class GateVerdict:
    ts_utc: datetime
    trace_id: str

    decision: Decision
    grade: Grade

    reason_codes: List[str] = field(default_factory=list)

    policy_ref: Optional[str] = None
    emitter_id: Optional[str] = None  # who produced this verdict (optional)

    def __post_init__(self):
        object.__setattr__(self, "ts_utc", require_utc_aware(self.ts_utc))

        if not isinstance(self.trace_id, str) or self.trace_id.strip() == "":
            raise ValueError("GateVerdict.trace_id must not be blank")

        if not isinstance(self.decision, Decision):
            raise TypeError("GateVerdict.decision must be Decision enum")

        if not isinstance(self.grade, Grade):
            raise TypeError("GateVerdict.grade must be Grade enum")

        if not isinstance(self.reason_codes, list):
            raise TypeError("GateVerdict.reason_codes must be list[str]")

        for i, rc in enumerate(self.reason_codes):
            if not isinstance(rc, str) or rc.strip() == "":
                raise ValueError(f"GateVerdict.reason_codes[{i}] must be non-empty str")

        if self.policy_ref is not None and (not isinstance(self.policy_ref, str) or self.policy_ref.strip() == ""):
            raise ValueError("GateVerdict.policy_ref must be non-empty str when provided")

        if self.emitter_id is not None and (not isinstance(self.emitter_id, str) or self.emitter_id.strip() == ""):
            raise ValueError("GateVerdict.emitter_id must be non-empty str when provided")