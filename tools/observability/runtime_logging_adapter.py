from __future__ import annotations

import logging
from typing import Any, Callable, Dict

from jsonschema import Draft7Validator, FormatChecker

from .errors import RuntimeLoggingInvariantError, RuntimeLoggingSchemaError
from .schema_loader import load_runtime_schema_v0_5
from .invariants import (
    is_decision_bearing,
    validate_runtime_invariants,
    enforce_rc_limit,
)

logger = logging.getLogger(__name__)

_SCHEMA = load_runtime_schema_v0_5()

# ✅ A: format strict enforcement
_VALIDATOR = Draft7Validator(_SCHEMA, format_checker=FormatChecker())

EmitFunc = Callable[[Dict[str, Any]], None]


def validate_runtime_log_event_v0_5(event: Dict[str, Any]) -> None:
    errors = sorted(_VALIDATOR.iter_errors(event), key=lambda e: list(e.path))
    if errors:
        msgs = []
        for e in errors:
            path = list(e.path)
            msgs.append(f"{path}: {e.message} (value={e.instance!r})")

        raise RuntimeLoggingSchemaError(
            message="Runtime log schema validation failed:\n" + "\n".join(msgs),
            errors=errors,
            event=_event_hint(event),
        )


def emit_runtime_event(event: Dict[str, Any], actual_emit: EmitFunc) -> None:
    """
    Enforcement policy (LOCK):
    - Decision-bearing events: schema/invariant violation => FAIL-FAST (raise)
    - Infra-only events: schema/invariant violation => WARNING + drop
    """
    decision_event = is_decision_bearing(event)

    try:
        validate_runtime_log_event_v0_5(event)
        validate_runtime_invariants(event)

        # rc policy (hash-external)
        enforce_rc_limit(event)

        # 🔒 trace_id MUST exist for decision-bearing (adapter MUST NOT create it)
        if decision_event and not event.get("trace_id"):
            raise RuntimeLoggingInvariantError(
                "Decision-bearing event MUST include trace_id (adapter MUST NOT generate trace_id)",
                event=_event_hint(event),
            )

    except (RuntimeLoggingSchemaError, RuntimeLoggingInvariantError) as e:
        if decision_event:
            raise
        logger.warning("Invalid infra-only log event dropped: %s", e)
        return

    actual_emit(event)


def _event_hint(event: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["ts_utc", "level", "component", "event", "emitter_id", "trace_id", "decision", "grade"]
    return {k: event.get(k) for k in keys if k in event}