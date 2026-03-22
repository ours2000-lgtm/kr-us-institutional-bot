# path: runtime/evidence/control_plane/control_plane_evidence_schema.py

from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
import json
from pathlib import Path
import uuid


CONTROL_PLANE_EVIDENCE_SCHEMA_VERSION = "control_plane_evidence_v1"


def _json_default(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if is_dataclass(value):
        return asdict(value)

    return str(value)


@dataclass
class ControlPlaneEvidence:
    schema_version: str
    category: str
    event_type: str
    component: Optional[str]
    occurred_at: str
    state: Optional[str]
    symbol: Optional[str]
    side: Optional[str]
    reason: Optional[str]
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_control_plane_evidence(
    base_dir: str,
    category: str,
    event_type: str,
    component: Optional[str] = None,
    state: Optional[str] = None,
    symbol: Optional[str] = None,
    side: Optional[str] = None,
    reason: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> str:
    payload = payload or {}

    evidence = ControlPlaneEvidence(
        schema_version=CONTROL_PLANE_EVIDENCE_SCHEMA_VERSION,
        category=str(category).strip().lower(),
        event_type=str(event_type).strip(),
        component=None if component is None else str(component).strip(),
        occurred_at=utc_now_iso(),
        state=None if state is None else str(state).strip().upper(),
        symbol=None if symbol is None else str(symbol).strip(),
        side=None if side is None else str(side).strip().upper(),
        reason=None if reason is None else str(reason).strip(),
        payload=payload,
    )

    event_dir = Path(base_dir) / evidence.category
    event_dir.mkdir(parents=True, exist_ok=True)

    timestamp = (
        evidence.occurred_at
        .replace(":", "")
        .replace("-", "")
        .replace("+00:00", "Z")
    )
    suffix = uuid.uuid4().hex[:8]
    filename = f"{timestamp}_{suffix}.json"
    path = event_dir / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            evidence.to_dict(),
            f,
            ensure_ascii=False,
            indent=2,
            default=_json_default,
        )

    return str(path)