# KR_US_INSTITUTIONAL_BOT/src/fsm/invariants/layer1_shape.py
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from ..violations import InvariantViolation, Severity, Layer


def _json_safe(v: Any) -> Any:
    """
    Make values JSON-serializable in a stable, conservative way.
    - datetime-like: isoformat()
    - bytes: hex
    - fallback: str(v)
    """
    if v is None:
        return None

    if hasattr(v, "isoformat") and callable(getattr(v, "isoformat")):
        try:
            return v.isoformat()
        except Exception:
            return str(v)

    if isinstance(v, (bytes, bytearray)):
        return v.hex()

    try:
        json.dumps(v)
        return v
    except Exception:
        return str(v)


def _stable_fingerprint(event: Dict[str, Any]) -> str:
    """
    Stable fingerprint for idempotency detection.

    NOTE:
    - Internal keys (_*) are excluded.
    - Non-JSON-safe objects are normalized.
    """
    clean = {
        k: _json_safe(v)
        for k, v in event.items()
        if not str(k).startswith("_")
    }
    payload = json.dumps(
        clean,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def check_shape_and_order(
    transitions: List[Dict[str, Any]],
    *,
    require_init_state: str = "S0_INIT",
    allow_same_timestamp: bool = True,
    timestamp_skew_tolerance_sec: int = 0,
    duplicate_policy: str = "DROP_IDENTICAL_FAIL_CONFLICT",
    enforce_seq_gap: bool = True,
    seq_gap_severity: Severity = Severity.CRITICAL,
    primary_violation_per_event: bool = True,
) -> List[InvariantViolation]:
    """
    Layer1: Shape/Ordering invariants (Time-travel & Gap & Idempotency).

    This layer validates TRANSITION records only; non-TRANSITION events
    (RUN_START / METRIC / LOG, etc.) are ignored by design.

    Input assumptions:
    - 'transitions' are already canonicalized:
      - GENESIS(RUN_START) removed
      - deep-copied (no caller side effects)
      - internal fields may be present (optional):
          _seq_int: Optional[int]
          _ts_dt: Optional[datetime]

    Policies:
    - First TRANSITION must start from require_init_state (default S0_INIT).
    - First TRANSITION seq must be >= 1 (GENESIS is not part of transitions).
    - Sequence gap detection (optional): 1,2,4 => L1_SEQ_GAP.
    - Timestamp monotonicity with tolerance.
    - Idempotency:
        * identical fingerprint duplicated => WARNING (DROP*) or CRITICAL (FAIL*)
        * same seq but different payload => CRITICAL (L1_SEQ_CONFLICT)
    """
    violations: List[InvariantViolation] = []

    if not transitions:
        violations.append(
            InvariantViolation(
                layer=Layer.L1_SHAPE,
                code="L1_EMPTY_TRACE",
                message="No transitions present",
                severity=Severity.CRITICAL,
            )
        )
        return violations

    # --- Find first TRANSITION event and enforce init state ---
    first_idx: Optional[int] = None
    first: Optional[Dict[str, Any]] = None
    for i, e in enumerate(transitions):
        if e.get("event_type") == "TRANSITION":
            first_idx = i
            first = e
            break

    if first is None:
        violations.append(
            InvariantViolation(
                layer=Layer.L1_SHAPE,
                code="L1_NO_TRANSITION",
                message="No TRANSITION event found",
                severity=Severity.CRITICAL,
            )
        )
        return violations

    # 1) init state invariant
    fr0 = first.get("from_state")
    if fr0 != require_init_state:
        violations.append(
            InvariantViolation(
                layer=Layer.L1_SHAPE,
                code="L1_MISSING_INIT",
                message=f"First transition must start from {require_init_state}",
                event_index=first_idx if first_idx is not None else 0,
                context={"from_state": fr0, "expected": require_init_state},
                severity=Severity.CRITICAL,
            )
        )

    # 2) first seq >= 1 invariant (A-옵션1: GENESIS는 별도, transitions는 1부터)
    first_seq = first.get("_seq_int")
    if first_seq is not None and first_seq < 1:
        violations.append(
            InvariantViolation(
                layer=Layer.L1_SHAPE,
                code="L1_FIRST_SEQ_INVALID",
                message="First TRANSITION seq must be >= 1 (GENESIS is not part of transitions)",
                event_index=first_idx if first_idx is not None else 0,
                context={"seq": first_seq},
                severity=Severity.CRITICAL,
            )
        )

    # --- duplicate severity decided once ---
    dup_identical_severity = Severity.WARNING if duplicate_policy.upper().startswith("DROP") else Severity.CRITICAL
    dup_identical_code = (
        "L1_DUPLICATE_IDENTICAL_DROP"
        if dup_identical_severity == Severity.WARNING
        else "L1_DUPLICATE_IDENTICAL_FAIL"
    )

    # --- Tracking for seq/idempotency/time ---
    last_seq: Optional[int] = None
    last_ts = None  # datetime | None

    seen_fp_first_index: Dict[str, int] = {}
    seen_seq_fp: Dict[int, str] = {}

    def add_primary(v: InvariantViolation) -> None:
        """
        If primary_violation_per_event=True:
        - keep at most one CRITICAL per event_index (reduce noise)
        - WARNINGS may still be recorded unless a CRITICAL already exists at same index
        """
        if not primary_violation_per_event or v.event_index < 0:
            violations.append(v)
            return

        # already has a CRITICAL at the same index -> skip anything else
        for existing in violations:
            if existing.event_index == v.event_index and existing.severity == Severity.CRITICAL:
                return
        violations.append(v)

    for i, e in enumerate(transitions):
        if e.get("event_type") != "TRANSITION":
            continue

        fp = _stable_fingerprint(e)

        # --- identical duplicate (idempotency) ---
        if fp in seen_fp_first_index:
            first_i = seen_fp_first_index[fp]
            add_primary(
                InvariantViolation(
                    layer=Layer.L1_SHAPE,
                    code=dup_identical_code,
                    message=(
                        "Identical event duplicated (idempotent retry possible)"
                        if dup_identical_severity == Severity.WARNING
                        else "Identical event duplicated"
                    ),
                    event_index=i,
                    context={"first_index": first_i},
                    severity=dup_identical_severity,
                )
            )
        else:
            seen_fp_first_index[fp] = i

        # --- seq rules ---
        seq = e.get("_seq_int")
        if seq is not None:
            # same seq conflict: CRITICAL
            if seq in seen_seq_fp and seen_seq_fp[seq] != fp:
                add_primary(
                    InvariantViolation(
                        layer=Layer.L1_SHAPE,
                        code="L1_SEQ_CONFLICT",
                        message="Same seq but different event payload (conflict)",
                        event_index=i,
                        context={"seq": seq},
                        severity=Severity.CRITICAL,
                    )
                )
            else:
                seen_seq_fp.setdefault(seq, fp)

            if last_seq is not None:
                if seq <= last_seq:
                    add_primary(
                        InvariantViolation(
                            layer=Layer.L1_SHAPE,
                            code="L1_SEQ_NOT_STRICTLY_INCREASING",
                            message=f"seq must be strictly increasing (prev={last_seq}, got={seq})",
                            event_index=i,
                            context={"prev_seq": last_seq, "seq": seq},
                            severity=Severity.CRITICAL,
                        )
                    )
                elif enforce_seq_gap and seq != last_seq + 1:
                    gap_size = (seq - last_seq - 1) if seq > last_seq else None
                    add_primary(
                        InvariantViolation(
                            layer=Layer.L1_SHAPE,
                            code="L1_SEQ_GAP",
                            message=f"Sequence gap: expected {last_seq + 1}, got {seq}",
                            event_index=i,
                            context={"prev_seq": last_seq, "seq": seq, "gap_size": gap_size},
                            severity=seq_gap_severity,
                        )
                    )

            last_seq = seq

        # --- timestamp monotonicity ---
        ts = e.get("_ts_dt")
        if ts is not None:
            if last_ts is not None:
                reversed_ = ts < last_ts if allow_same_timestamp else ts <= last_ts
                if reversed_:
                    delta_sec = (last_ts - ts).total_seconds()
                    # if allow_same_timestamp=False, equality (delta=0) is also forbidden
                    violates = (delta_sec > timestamp_skew_tolerance_sec) or (not allow_same_timestamp and delta_sec == 0)
                    if violates:
                        add_primary(
                            InvariantViolation(
                                layer=Layer.L1_SHAPE,
                                code="L1_TIME_TRAVEL",
                                message=(
                                    "Timestamp reversed beyond tolerance"
                                    if delta_sec > 0
                                    else "Timestamp not strictly increasing (policy disallows equality)"
                                ),
                                event_index=i,
                                context={
                                    "prev_ts": last_ts.isoformat(),
                                    "ts": ts.isoformat(),
                                    "delta_sec": delta_sec,
                                    "tolerance_sec": timestamp_skew_tolerance_sec,
                                    "allow_same_timestamp": allow_same_timestamp,
                                },
                                severity=Severity.CRITICAL,
                            )
                        )
            last_ts = ts

    return violations
