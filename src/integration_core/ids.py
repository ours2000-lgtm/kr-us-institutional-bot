from __future__ import annotations

import os
from dataclasses import dataclass
from typing import FrozenSet, Optional, Sequence
from uuid import UUID, uuid4


# -----------------------------
# Errors
# -----------------------------
class TraceabilityIdError(ValueError):
    """Raised when a traceability ID is malformed or fails validation."""


# -----------------------------
# Constants / Registry
# -----------------------------
# DOMAIN_PREFIX-UUIDv4
# prefix: STRICT UPPERCASE letters + digits + underscore
_DEFAULT_PREFIXES: FrozenSet[str] = frozenset({"PLAN", "VAL", "ROLLOUT"})


def allowed_prefixes() -> FrozenSet[str]:
    """
    Prefix registry root.

    Optional extension via env:
      TRACE_ID_PREFIXES=PLAN,VAL,ROLLOUT,CHAOS
    """
    env = os.getenv("TRACE_ID_PREFIXES")
    if not env:
        return _DEFAULT_PREFIXES

    extra = {p.strip().upper() for p in env.split(",") if p.strip()}
    return frozenset(set(_DEFAULT_PREFIXES) | extra)


# -----------------------------
# Helpers
# -----------------------------
def _normalize_prefix(prefix: str) -> str:
    """
    STRICT normalization.

    Fail-closed:
    - must already be uppercase
    - no auto-upper conversion
    """
    if not isinstance(prefix, str):
        raise TraceabilityIdError("prefix must be a string")

    p = prefix.strip()
    if not p:
        raise TraceabilityIdError("prefix must be non-empty")

    if p != p.upper():
        raise TraceabilityIdError(f"prefix must be uppercase: {p}")

    if not all(ch.isupper() or ch.isdigit() or ch == "_" for ch in p):
        raise TraceabilityIdError(f"invalid prefix: {p}")

    return p


def _format_tid(prefix: str, u: UUID) -> str:
    return f"{prefix}-{str(u)}"


# -----------------------------
# Core Model
# -----------------------------
@dataclass(frozen=True)
class TraceabilityId:
    prefix: str
    uuid: UUID
    value: str

    @staticmethod
    def create(prefix: str) -> "TraceabilityId":
        p = _normalize_prefix(prefix)

        if p not in allowed_prefixes():
            raise TraceabilityIdError(f"unsupported prefix: {p}")

        u = uuid4()
        return TraceabilityId(prefix=p, uuid=u, value=_format_tid(p, u))


# -----------------------------
# Public API
# -----------------------------
def generate_id(prefix: str) -> TraceabilityId:
    """
    Generate new ID.

    Fail-closed:
    unsupported prefix -> error
    """
    return TraceabilityId.create(prefix)


def parse_id(raw: str, *, prefixes: Optional[Sequence[str]] = None) -> TraceabilityId:
    """
    Parse + validate ID.

    Format:
      PREFIX-UUIDv4
    """
    if not isinstance(raw, str):
        raise TraceabilityIdError("id must be a string")

    s = raw.strip()
    if not s:
        raise TraceabilityIdError("id must be non-empty")

    if "-" not in s:
        raise TraceabilityIdError("missing '-' separator")

    prefix_part, uuid_part = s.split("-", 1)
    p = _normalize_prefix(prefix_part)

    if p not in allowed_prefixes():
        raise TraceabilityIdError(f"unsupported prefix: {p}")

    if prefixes is not None:
        filt = {_normalize_prefix(x) for x in prefixes}
        if p not in filt:
            raise TraceabilityIdError(f"prefix not allowed by filter: {p}")

    try:
        u = UUID(uuid_part)
    except Exception as e:
        raise TraceabilityIdError(f"invalid UUID format: {uuid_part}") from e

    if u.version != 4:
        raise TraceabilityIdError(
            f"invalid UUID version: expected v4, got v{u.version}"
        )

    return TraceabilityId(prefix=p, uuid=u, value=_format_tid(p, u))


def validate_id(raw: str, *, prefixes: Optional[Sequence[str]] = None) -> bool:
    """
    Non-throwing validator.
    """
    try:
        parse_id(raw, prefixes=prefixes)
        return True
    except TraceabilityIdError:
        return False