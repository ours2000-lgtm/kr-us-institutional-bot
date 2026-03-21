# E:\KR_US_INSTITUTIONAL_BOT\runtime\governance\trace_emitter.py
"""
TraceBundle emitter + atomic writer.

- Emits a minimal governance-relevant TraceBundle (JSON dict).
- Writes trace JSON atomically (temp file -> replace).
- No policy logic here. Pure data emission.

Expected TraceBundle minimum keys (v0):
- trace_id: str (uuid4 hex)
- created_at_utc: str (ISO8601, Z-normalized)
- decision: "ALLOW" | "DENY" | "UNKNOWN"
- fail_closed: bool
- reason_code: str
- actor_id: str
- context: dict
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4
import json
import os
import tempfile


DecisionStr = str  # keep runtime flexible (LOCK is in docs/tests)


def _utc_now_z() -> str:
    # Always Z-normalized
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _jsonable(v: Any) -> Any:
    # Best-effort JSON compatibility for Enums / dataclasses / primitives.
    if v is None:
        return None
    if hasattr(v, "value"):
        # Enum-like
        return getattr(v, "value")
    if is_dataclass(v):
        return {k: _jsonable(val) for k, val in asdict(v).items()}
    if isinstance(v, dict):
        return {str(k): _jsonable(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    return v


def emit_trace_bundle(
    *,
    decision: DecisionStr,
    fail_closed: bool,
    reason_code: str,
    actor_id: str = "UNKNOWN_ACTOR",
    context: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    created_at_utc: Optional[str] = None,
    outcome: Any = None,
    raw_reason: Optional[str] = None,
    engine_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a TraceBundle dict.

    Notes:
    - outcome may be Enum; it will be serialized as .value
    - raw_reason will be normalized to a non-empty sentinel string
    """
    tid = trace_id or uuid4().hex
    ts = created_at_utc or _utc_now_z()

    rr = (raw_reason or "").strip()
    if not rr:
        rr = "MISSING_REASON"

    bundle = {
        "trace_id": tid,
        "created_at_utc": ts,
        "decision": decision,
        "fail_closed": bool(fail_closed),
        "reason_code": str(reason_code),
        "actor_id": str(actor_id),
        "context": _jsonable(context or {}),
        # Extended (optional, replay helpful)
        "outcome": _jsonable(outcome),
        "raw_reason": rr,
        "engine_version": str(engine_version) if engine_version else None,
    }
    return bundle


def write_trace_bundle(
    trace_bundle: Dict[str, Any],
    traces_dir: Path,
    *,
    filename: Optional[str] = None,
) -> Path:
    """
    Atomically write TraceBundle JSON to disk.
    Returns written file path.
    """
    traces_dir = Path(traces_dir)
    traces_dir.mkdir(parents=True, exist_ok=True)

    trace_id = trace_bundle.get("trace_id")
    if not trace_id:
        raise ValueError("TraceBundle missing trace_id")

    if filename is None:
        # Safe filename: YYYYMMDDTHHMMSSffffffZ
        ts = trace_bundle.get("created_at_utc") or _utc_now_z()
        # Make compact timestamp
        compact = (
            ts.replace("-", "")
            .replace(":", "")
            .replace(".", "")
            .replace("+00:00", "Z")
        )
        filename = f"trace_{compact}_{trace_id}.json"

    out_path = traces_dir / filename

    # Atomic write: temp -> replace
    data = json.dumps(trace_bundle, ensure_ascii=False, indent=2)

    fd, tmp_path = tempfile.mkstemp(prefix="._trace_", suffix=".tmp", dir=str(traces_dir))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        Path(tmp_path).replace(out_path)
    finally:
        # If replace failed, cleanup temp
        try:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink(missing_ok=True)  # py3.8+ compat via try/except
        except Exception:
            pass

    return out_path
