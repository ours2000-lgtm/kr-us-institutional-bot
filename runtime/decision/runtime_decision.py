from __future__ import annotations

from dataclasses import dataclass

from runtime.decision.reason_code import ReasonCode

@dataclass(frozen=True)
class RuntimeDecision:
    """
    Canonical runtime decision object.

    LOCK (Core axis):
      - decision: "ALLOW" | "DENY" | "UNKNOWN"
      - fail_closed: bool
      - reason_code: ReasonCode  (constitutional reason code)

    Extended (Replay/Audit helpful, non-LOCK but persisted):
      - outcome: ValidationOutcome (raw validator outcome)
      - raw_reason: str (raw reason string from validator; ALWAYS non-empty via placeholders)
      - engine_version: str (rule-set / engine marker; replay-critical metadata)
    """

    decision: DecisionType
    fail_closed: bool
    reason_code: ReasonCode

    # Extended fields (persisted, but non-LOCK)
    outcome: Optional[ValidationOutcome] = None
    raw_reason: str = "MISSING_REASON"
    engine_version: str = "risk_engine_v1_1"
