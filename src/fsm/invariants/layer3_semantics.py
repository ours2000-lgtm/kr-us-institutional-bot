# KR_US_INSTITUTIONAL_BOT/src/fsm/invariants/layer3_semantics.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

from ..violations import InvariantViolation, Severity, Layer


# -------------------------
# Rule Definitions
# -------------------------

ValidatorFunc = Callable[[Dict[str, Any]], Iterable[Tuple[str, str]]]
# returns iterable of (field_name, error_message) for invalid content


@dataclass(frozen=True)
class RequiredPayloadRule:
    """
    Rule: when entering 'to_state', payload must contain these fields.
    Optional validator can additionally validate content/format.
    """
    to_state: str
    required_fields: Set[str]
    code_missing: str
    message_missing: str
    severity_missing: Severity = Severity.CRITICAL

    code_invalid: str = "L3_PAYLOAD_INVALID_VALUE"
    message_invalid: str = "Payload field value is invalid"
    severity_invalid: Severity = Severity.CRITICAL

    validator: Optional[ValidatorFunc] = None
    # future-proof: you can add event_type filter if needed


@dataclass(frozen=True)
class OrderingRule:
    required_before: str
    must_follow: str
    code: str
    message: str
    severity: Severity = Severity.CRITICAL


# -------------------------
# Default Rules (v1)
# -------------------------

def _validate_rehearsal_payload(payload: Dict[str, Any]) -> Iterable[Tuple[str, str]]:
    # Minimal content checks (v1): types + simple format sanity
    rid = payload.get("rehearsal_id")
    if rid is not None and not isinstance(rid, str):
        yield ("rehearsal_id", "must be a string")

    ph = payload.get("proof_hash")
    if ph is not None:
        if not isinstance(ph, str):
            yield ("proof_hash", "must be a string")
        else:
            # accept hex-ish; do not over-constrain in v1
            s = ph.lower().strip()
            if len(s) < 16:
                yield ("proof_hash", "too short")
            if any(c not in "0123456789abcdef" for c in s):
                yield ("proof_hash", "must look like hex string")


DEFAULT_REQUIRED_RULES: List[RequiredPayloadRule] = [
    RequiredPayloadRule(
        to_state="S2_REHEARSAL_PROVEN",
        required_fields={"rehearsal_id", "proof_hash"},
        code_missing="L3_PAYLOAD_MISSING_FIELD",
        message_missing="S2_REHEARSAL_PROVEN requires payload.rehearsal_id and payload.proof_hash",
        severity_missing=Severity.CRITICAL,
        validator=_validate_rehearsal_payload,
        code_invalid="L3_REHEARSAL_PAYLOAD_INVALID",
        message_invalid="S2_REHEARSAL_PROVEN payload fields are invalid",
        severity_invalid=Severity.CRITICAL,
    ),
    RequiredPayloadRule(
        to_state="SX_FAIL_CLOSED",
        required_fields={"halt_reason_code", "fail_closed_summary"},
        code_missing="L3_FAIL_CLOSED_MISSING_REASON",
        message_missing="SX_FAIL_CLOSED requires payload.halt_reason_code and payload.fail_closed_summary",
        severity_missing=Severity.CRITICAL,
    ),
]

DEFAULT_ORDERING_RULES: List[OrderingRule] = [
    OrderingRule(
        required_before="S2_REHEARSAL_PROVEN",
        must_follow="S3_ACTIVATED",
        code="L3_ACTIVATED_BEFORE_PROVEN",
        message="S3_ACTIVATED must occur after S2_REHEARSAL_PROVEN",
        severity=Severity.CRITICAL,
    ),
]


# -------------------------
# Helpers
# -------------------------

def _get_payload(e: Dict[str, Any]) -> Dict[str, Any]:
    p = e.get("payload")
    return p if isinstance(p, dict) else {}


def _missing_fields(payload: Dict[str, Any], fields: Set[str]) -> List[str]:
    missing: List[str] = []
    for f in fields:
        if f not in payload or payload.get(f) in (None, "", []):
            missing.append(f)
    return missing


# -------------------------
# Layer3 Main
# -------------------------

def check_semantics(
    transitions: List[Dict[str, Any]],
    *,
    terminal_states: Set[str],
    require_transition_type: str = "TRANSITION",
    required_rules: Optional[List[RequiredPayloadRule]] = None,
    ordering_rules: Optional[List[OrderingRule]] = None,
    # Finality policy:
    # - "WARN_INCOMPLETE": last state not terminal => WARNING
    # - "FAIL_INCOMPLETE": last state not terminal => CRITICAL
    # - "IGNORE_INCOMPLETE": do nothing
    finality_policy: str = "WARN_INCOMPLETE",
    # terminal handling:
    fail_closed_state: str = "SX_FAIL_CLOSED",
    treat_fail_closed_as_terminal: bool = True,
    # noise control:
    primary_violation_per_event: bool = True,
) -> List[InvariantViolation]:
    """
    Layer3: Semantics / provenance binding / finality.

    This layer validates TRANSITION records only; non-TRANSITION events are ignored by design.
    GENESIS(RUN_START) is not handled here (A-옵션1).

    1) Required payload presence (+ optional content validators)
    2) Ordering constraints (generalized via OrderingRule list)
    3) Finality invariant (warn/fail/ignore)
    """
    violations: List[InvariantViolation] = []
    required_rules = required_rules or DEFAULT_REQUIRED_RULES
    ordering_rules = ordering_rules or DEFAULT_ORDERING_RULES

    terminal_set = set(terminal_states)
    if treat_fail_closed_as_terminal:
        terminal_set.add(fail_closed_state)

    def add_primary(v: InvariantViolation) -> None:
        if not primary_violation_per_event or v.event_index < 0:
            violations.append(v)
            return
        if not any(
            existing.event_index == v.event_index and existing.severity == Severity.CRITICAL
            for existing in violations
        ):
            violations.append(v)

    # milestone: which states have been reached so far (for ordering rules)
    reached: Set[str] = set()

    last_to_state: Optional[str] = None
    last_transition_index: Optional[int] = None

    for i, e in enumerate(transitions):
        if e.get("event_type") != require_transition_type:
            continue

        to_state = e.get("to_state")
        last_to_state = to_state
        last_transition_index = i

        payload = _get_payload(e)

        # (1) required payload presence + content validators
        for r in required_rules:
            if to_state != r.to_state:
                continue

            missing = _missing_fields(payload, r.required_fields)
            if missing:
                add_primary(
                    InvariantViolation(
                        layer=Layer.L3_SEMANTIC,
                        code=r.code_missing,
                        message=r.message_missing,
                        event_index=i,
                        context={"to_state": to_state, "missing": missing},
                        severity=r.severity_missing,
                    )
                )
                # if required fields missing, skip value validation to avoid noise
                continue

            if r.validator is not None:
                invalids = list(r.validator(payload))
                if invalids:
                    add_primary(
                        InvariantViolation(
                            layer=Layer.L3_SEMANTIC,
                            code=r.code_invalid,
                            message=r.message_invalid,
                            event_index=i,
                            context={
                                "to_state": to_state,
                                "invalid": [{"field": f, "error": msg} for (f, msg) in invalids],
                            },
                            severity=r.severity_invalid,
                        )
                    )

        # (2) ordering constraints
        # mark reached AFTER checks for "must follow" at this event
        # because "S3_ACTIVATED must follow S2" should fire if S2 not reached prior.
        if to_state is not None:
            for rule in ordering_rules:
                if to_state == rule.must_follow and rule.required_before not in reached:
                    add_primary(
                        InvariantViolation(
                            layer=Layer.L3_SEMANTIC,
                            code=rule.code,
                            message=rule.message,
                            event_index=i,
                            context={"must_follow": rule.must_follow, "required_before": rule.required_before},
                            severity=rule.severity,
                        )
                    )

            reached.add(to_state)

    # (3) finality invariant
    if last_transition_index is None:
        # No TRANSITION at all; Layer1 already handles. Keep Layer3 silent.
        return violations

    if finality_policy != "IGNORE_INCOMPLETE":
        if last_to_state not in terminal_set:
            sev = Severity.WARNING if finality_policy == "WARN_INCOMPLETE" else Severity.CRITICAL
            violations.append(
                InvariantViolation(
                    layer=Layer.L3_SEMANTIC,
                    code="L3_TRACE_INCOMPLETE",
                    message="Trace ended without reaching a terminal state",
                    event_index=last_transition_index,
                    context={
                        "last_to_state": last_to_state,
                        "terminal_states": sorted(list(terminal_set)),
                        "finality_policy": finality_policy,
                    },
                    severity=sev,
                )
            )

    return violations
