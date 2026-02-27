from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .errors import RuntimeLoggingInvariantError

MARKER_CODE = "COMPOSITE_MARKER"
RC_MAX_BYTES = 4096


def is_decision_bearing(event: Dict[str, Any]) -> bool:
    return "decision" in event and "grade" in event


def enforce_trace_id_presence_for_decision_events(event: Dict[str, Any]) -> None:
    if is_decision_bearing(event) and not event.get("trace_id"):
        raise RuntimeLoggingInvariantError(
            "Decision-bearing event MUST include trace_id (adapter MUST NOT generate trace_id)",
            event=_event_hint(event),
        )


def enforce_marker_reasoncode_bidirectional(event: Dict[str, Any]) -> None:
    reason_codes = event.get("reason_codes")
    marker = event.get("marker")

    if isinstance(reason_codes, list) and MARKER_CODE in reason_codes:
        if not isinstance(marker, dict):
            raise RuntimeLoggingInvariantError(
                f"{MARKER_CODE} in reason_codes requires marker object",
                event=_event_hint(event),
            )
        if marker.get("code") != MARKER_CODE:
            raise RuntimeLoggingInvariantError(
                "marker.code MUST match COMPOSITE_MARKER when COMPOSITE_MARKER is present",
                event=_event_hint(event),
            )

    if isinstance(marker, dict) and isinstance(reason_codes, list):
        code = marker.get("code")
        if code is not None and code not in reason_codes:
            raise RuntimeLoggingInvariantError(
                "marker.code MUST be present in reason_codes",
                event=_event_hint(event),
            )


def enforce_rc_limit(event: Dict[str, Any]) -> None:
    rc = event.get("rc")
    if not rc:
        return

    # canonical-ish for byte counting
    rc_json = json.dumps(rc, ensure_ascii=False, separators=(",", ":"))
    size = len(rc_json.encode("utf-8"))

    if size > RC_MAX_BYTES:
        # drop policy (simple and deterministic)
        event["rc"] = None
        event["rc_truncated"] = True


def validate_runtime_invariants(event: Dict[str, Any]) -> None:
    """
    Cross-field or runtime-policy invariants that schema cannot fully express.
    """
    enforce_trace_id_presence_for_decision_events(event)
    enforce_marker_reasoncode_bidirectional(event)


def _event_hint(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Small hint to attach to exceptions without leaking huge payloads.
    """
    keys = ["ts_utc", "level", "component", "event", "emitter_id", "trace_id", "decision", "grade"]
    hint = {k: event.get(k) for k in keys if k in event}
    return hint