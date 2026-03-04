from __future__ import annotations

from runtime.decision.reason_code import ReasonCode
from runtime.decision.runtime_decision import RuntimeDecision

def _raw_reason_or_placeholder(reason: str | None) -> str:
    s = (reason or "").strip()
    return s if s else "MISSING_REASON"


def build_runtime_decision(
    outcome: ValidationOutcome,
    reason: str | None,
    *,
    engine_version: str = DEFAULT_ENGINE_VERSION,
) -> RuntimeDecision:
    """
    Build a canonical RuntimeDecision from (outcome, raw reason).

    Policy note:
    - ALLOW     => decision=ALLOW, fail_closed=False
    - BLOCK     => decision=DENY,  fail_closed=False (policy/risk/validation rejection)
    - HARD_STOP => decision=DENY,  fail_closed=True  (terminal fail-closed safety)

    Unknown outcome handling (LOCK intent):
    - Any unmapped outcome MUST degrade to ("UNKNOWN", True) fail-closed safety.
    - In STRICT mode (RUNTIME_STRICT_OUTCOME_MAPPING=1), unmapped outcome MUST raise.

    raw_reason:
    - Always persisted as a non-empty string for audit friendliness.
      ("MISSING_REASON" placeholder is used when absent.)
    """

    # Unmapped outcome handling
    if outcome not in OUTCOME_TO_DECISION:
        if STRICT_OUTCOME_MAPPING:
            raise KeyError(f"Unmapped ValidationOutcome: {outcome!r}")

        return RuntimeDecision(
            decision="UNKNOWN",
            fail_closed=True,
            reason_code=ReasonCode.FAILED_UNKNOWN,
            outcome=outcome,
            raw_reason="UNKNOWN_OUTCOME",
            engine_version=engine_version,
        )

    decision, fail_closed = OUTCOME_TO_DECISION[outcome]

    # Map reason -> ReasonCode (constitutional). If taxonomy drifts, mapper returns FAILED_UNKNOWN.
    rc = map_reason_to_code(reason)

    return RuntimeDecision(
        decision=decision,
        fail_closed=fail_closed,
        reason_code=rc,
        outcome=outcome,
        raw_reason=_raw_reason_or_placeholder(reason),
        engine_version=engine_version,
    )
