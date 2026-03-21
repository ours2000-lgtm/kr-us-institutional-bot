# KR_US_INSTITUTIONAL_BOT/src/fsm/validate.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple

from .canonicalize import canonicalize_events, CanonicalizeError
from .policy import ValidationPolicy, DefaultFailClosedPolicy
from .violations import InvariantViolation, Severity, Layer

from .invariants.layer1_shape import check_shape_and_order
from .invariants.layer2_transitions import check_allowed_transitions
from .invariants.layer3_semantics import check_semantics


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    fail_closed: bool
    violations: List[InvariantViolation] = field(default_factory=list)
    by_layer: Dict[Layer, List[InvariantViolation]] = field(default_factory=dict)
    policy_id: str = "unknown"


def _as_violation(
    layer: Layer,
    code: str,
    message: str,
    *,
    event_index: int = -1,
    context: Dict[str, Any] | None = None,
) -> InvariantViolation:
    return InvariantViolation(
        layer=layer,
        code=code,
        message=message,
        event_index=event_index,
        context=context or {},
        severity=Severity.CRITICAL,
    )


def _compute_ok(violations: List[InvariantViolation], fail_closed: bool, ok_mode: str) -> bool:
    mode = (ok_mode or "STRICT_ALL").upper()
    if mode == "STRICT_ALL":
        return len(violations) == 0
    if mode == "STRICT_CRITICAL":
        return not any(v.severity == Severity.CRITICAL for v in violations)
    if mode == "POLICY":
        return not fail_closed
    return len(violations) == 0


def validate_trace(
    events: List[Dict[str, Any]],
    *,
    allowed_transitions: Set[Tuple[str, str]],
    terminal_states: Set[str],
    require_genesis: bool = True,
    policy: ValidationPolicy | None = None,

    # Backward-compatible "ok" toggle (legacy API support)
    # - strict_ok=True  : STRICT_ALL (any violation => ok=False)
    # - strict_ok=False : STRICT_CRITICAL (WARNING-only => ok=True)
    #
    # NOTE:
    # - ok_mode가 명시적으로 넘어오면(ok_mode != "STRICT_ALL" 등) ok_mode가 우선입니다.
    strict_ok: bool | None = None,

    # ok semantics:
    # - STRICT_ALL: any violation (WARNING 포함) => ok=False
    # - STRICT_CRITICAL: CRITICAL만 있으면 ok=False (WARNING-only => ok=True)
    # - POLICY: ok = not fail_closed
    ok_mode: str = "STRICT_ALL",

    # Layer1 controls
    l1_require_init_state: str = "S0_INIT",
    l1_enforce_seq_gap: bool = True,
    l1_seq_gap_severity: Severity = Severity.CRITICAL,
    l1_allow_same_timestamp: bool = True,
    l1_timestamp_skew_tolerance_sec: int = 0,
    l1_duplicate_policy: str = "DROP_IDENTICAL_FAIL_CONFLICT",
    l1_primary_violation_per_event: bool = True,

    # Layer2 controls
    l2_require_init_state: str | None = "S0_INIT",
    l2_fail_closed_state: str = "SX_FAIL_CLOSED",
    l2_treat_fail_closed_as_terminal: bool = True,
    l2_discontinuity_severity: Severity = Severity.WARNING,
    l2_primary_violation_per_event: bool = True,

    # Layer3 controls
    l3_finality_policy: str = "WARN_INCOMPLETE",  # WARN_INCOMPLETE | FAIL_INCOMPLETE | IGNORE_INCOMPLETE
    l3_fail_closed_state: str = "SX_FAIL_CLOSED",
    l3_treat_fail_closed_as_terminal: bool = True,
    l3_primary_violation_per_event: bool = True,

    # output hygiene
    include_empty_layers: bool = False,
) -> ValidationResult:
    # strict_ok -> ok_mode (compat shim)
    # ok_mode를 사용자가 이미 바꿔서 넘겼다면(ok_mode != 기본) 그 값을 존중한다.
    if strict_ok is not None and ok_mode == "STRICT_ALL":
        ok_mode = "STRICT_ALL" if strict_ok else "STRICT_CRITICAL"

    if policy is None:
        policy = DefaultFailClosedPolicy()

    # 1) canonicalize
    try:
        canon = canonicalize_events(events, require_genesis=require_genesis)
    except CanonicalizeError as e:
        v = InvariantViolation(
            layer=Layer.GENESIS,
            code=e.code,
            message=e.message,
            event_index=e.event_index,
            context=e.context,
            severity=Severity.CRITICAL,
        )
        decision = policy.decide([v])
        ok = _compute_ok([v], decision.fail_closed, ok_mode)
        return ValidationResult(
            ok=ok,
            fail_closed=decision.fail_closed,
            violations=[v],
            by_layer={Layer.GENESIS: [v]},
            policy_id=decision.policy_id,
        )
    except Exception as e:
        v = _as_violation(Layer.GENESIS, "G_CANONICALIZE_EXCEPTION", f"canonicalize raised: {type(e).__name__}: {e}")
        decision = policy.decide([v])
        ok = _compute_ok([v], decision.fail_closed, ok_mode)
        return ValidationResult(
            ok=ok,
            fail_closed=decision.fail_closed,
            violations=[v],
            by_layer={Layer.GENESIS: [v]},
            policy_id=decision.policy_id,
        )

    # 2) invariants (defensive)
    try:
        l1 = check_shape_and_order(
            canon.transitions,
            require_init_state=l1_require_init_state,
            allow_same_timestamp=l1_allow_same_timestamp,
            timestamp_skew_tolerance_sec=l1_timestamp_skew_tolerance_sec,
            duplicate_policy=l1_duplicate_policy,
            enforce_seq_gap=l1_enforce_seq_gap,
            seq_gap_severity=l1_seq_gap_severity,
            primary_violation_per_event=l1_primary_violation_per_event,
        )
    except Exception as e:
        l1 = [_as_violation(Layer.L1_SHAPE, "L1_EXCEPTION", f"Layer1 raised: {type(e).__name__}: {e}")]

    try:
        l2 = check_allowed_transitions(
            canon.transitions,
            allowed=allowed_transitions,
            terminal_states=terminal_states,
            require_init_state=l2_require_init_state,
            fail_closed_state=l2_fail_closed_state,
            treat_fail_closed_as_terminal=l2_treat_fail_closed_as_terminal,
            discontinuity_severity=l2_discontinuity_severity,
            primary_violation_per_event=l2_primary_violation_per_event,
        )
    except TypeError as e:
        l2 = [_as_violation(Layer.L2_TRANSITION, "L2_SIGNATURE_MISMATCH", f"Layer2 signature mismatch: {e}")]
    except Exception as e:
        l2 = [_as_violation(Layer.L2_TRANSITION, "L2_EXCEPTION", f"Layer2 raised: {type(e).__name__}: {e}")]

    try:
        l3 = check_semantics(
            canon.transitions,
            terminal_states=terminal_states,
            finality_policy=l3_finality_policy,
            fail_closed_state=l3_fail_closed_state,
            treat_fail_closed_as_terminal=l3_treat_fail_closed_as_terminal,
            primary_violation_per_event=l3_primary_violation_per_event,
        )
    except TypeError as e:
        l3 = [_as_violation(Layer.L3_SEMANTIC, "L3_SIGNATURE_MISMATCH", f"Layer3 signature mismatch: {e}")]
    except Exception as e:
        l3 = [_as_violation(Layer.L3_SEMANTIC, "L3_EXCEPTION", f"Layer3 raised: {type(e).__name__}: {e}")]

    by_layer: Dict[Layer, List[InvariantViolation]] = {
        Layer.L1_SHAPE: l1,
        Layer.L2_TRANSITION: l2,
        Layer.L3_SEMANTIC: l3,
    }
    if not include_empty_layers:
        by_layer = {k: v for k, v in by_layer.items() if v}

    violations = l1 + l2 + l3
    decision = policy.decide(violations)
    ok = _compute_ok(violations, decision.fail_closed, ok_mode)

    return ValidationResult(
        ok=ok,
        fail_closed=decision.fail_closed,
        violations=violations,
        by_layer=by_layer,
        policy_id=decision.policy_id,
    )
