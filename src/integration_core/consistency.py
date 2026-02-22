from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ConsistencyMode(str, Enum):
    warn = "warn"
    block = "block"


@dataclass(frozen=True, slots=True)
class ConsistencyResult:
    ok: bool
    message: str
    drift_code: str | None = None


class ConsistencyChecker(Protocol):
    """
    Cross-domain consistency checker interface.

    MVP: implementations MAY only log/emit metrics (warn-mode default).
    v1.1+: block-mode may prevent state transitions for critical drift.
    """

    def check(self) -> ConsistencyResult: ...


def enforce(result: ConsistencyResult, *, mode: ConsistencyMode) -> None:
    """
    Enforce a consistency result.
    - warn: never raises
    - block: raises RuntimeError on drift
    """
    if result.ok:
        return
    if mode == ConsistencyMode.warn:
        return
    raise RuntimeError(f"Consistency check failed: {result.drift_code or 'DRIFT'}: {result.message}")