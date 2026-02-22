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
# v1 고정: DOMAIN_PREFIX-UUIDv4
# - prefix: UPPERCASE letters + digits + underscore만 허용 (소문자 FAIL-CLOSED)
# - separator: single "-"
# - uuid: canonical lowercase UUID string
#
# Extension policy:
# - 기본 prefix set은 LOCK
# - 운영 환경 확장만 허용(환경변수) -> Governance에서 관리/증거화 가능
_DEFAULT_PREFIXES: FrozenSet[str] = frozenset({"PLAN", "VAL", "ROLLOUT"})


def allowed_prefixes() -> FrozenSet[str]:
    """
    Prefix registry root.

    Extension via env (optional):
      TRACE_ID_PREFIXES=PLAN,VAL,ROLLOUT,CHAOS

    Governance note:
    - Default set is LOCK.
    - Extensions MUST be controlled and evidenced (env/config is policy-managed).
    """
    env = os.getenv("TRACE_ID_PREFIXES")
    if not env:
        return _DEFAULT_PREFIXES

    # env는 추가 확장만 허용 (대문자로 normalize)
    extra = {p.strip().upper() for p in env.split(",") if p.strip()}
    return frozenset(set(_DEFAULT_PREFIXES) | extra)


def _normalize_prefix(prefix: str) -> str:
    if not isinstance(prefix, str):
        raise TraceabilityIdError("prefix must be a string")

    p_raw = prefix.strip()
    if not p_raw:
        raise TraceabilityIdError("prefix must be non-empty")

    # ❗️Fail-closed: 자동 upper() 보정 금지
    # - plan / Plan / pLaN 등은 모두 거부
    if p_raw != p_raw.upper():
        raise TraceabilityIdError(f"invalid prefix (must be uppercase): {p_raw}")

    p = p_raw  # already uppercase

    if not all(ch.isupper() or ch.isdigit() or ch == "_" for ch in p):
        raise TraceabilityIdError(f"invalid prefix: {p}")

    return p


def _format_tid(prefix: str, u: UUID) -> str:
    # canonical: PREFIX-uuid (uuid lower)
    return f"{prefix}-{str(u)}"


@dataclass(frozen=True)
class TraceabilityId:
    """
    Canonical traceability identifier.

    Format:
      PREFIX-UUIDv4
    Example:
      PLAN-123e4567-e89b-12d3-a456-426614174000

    Invariants:
    - prefix is normalized uppercase
    - uuid is UUID object (version=4 enforced at creation/parse)
    - value is canonical string representation
    """

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
    Generate a new TraceabilityId with a supported prefix.

    Fail-closed:
    - Unsupported prefix raises TraceabilityIdError.
    - Lowercase/mixedcase prefix raises TraceabilityIdError.
    """
    return TraceabilityId.create(prefix)


def parse_id(raw: str, *, prefixes: Optional[Sequence[str]] = None) -> TraceabilityId:
    """
    Parse and validate a traceability ID string.

    Args:
        raw: candidate string in PREFIX-UUID form
        prefixes: optional allowed prefix list override (filter). If provided,
                  the parsed prefix must be in this list.

    Raises:
        TraceabilityIdError on any parse/validation failure.
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

    # UUID parse + v4 enforcement
    try:
        u = UUID(uuid_part)
    except Exception as e:
        raise TraceabilityIdError(f"invalid UUID format: {uuid_part}") from e

    if u.version != 4:
        raise TraceabilityIdError(f"invalid UUID version: expected v4, got v{u.version}")

    canonical = _format_tid(p, u)
    return TraceabilityId(prefix=p, uuid=u, value=canonical)


def validate_id(raw: str, *, prefixes: Optional[Sequence[str]] = None) -> bool:
    """
    Return True iff raw parses as a valid traceability ID.

    This is a non-throwing convenience wrapper.
    """
    try:
        parse_id(raw, prefixes=prefixes)
        return True
    except TraceabilityIdError:
        return False