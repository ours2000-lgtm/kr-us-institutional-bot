# tools/governance_validator/result_contract.py
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict, Callable


# ---------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------
class ChainValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


class RuleCode(str, Enum):
    # R1
    MISSING_THIS_HASH = "MISSING_THIS_HASH"
    # R2
    MISSING_PREV_REFERENCE = "MISSING_PREV_REFERENCE"
    # R3
    HEAD_MISMATCH = "HEAD_MISMATCH"
    # R4
    DUPLICATE_THIS_HASH = "DUPLICATE_THIS_HASH"
    # R5
    MULTIPLE_GENESIS = "MULTIPLE_GENESIS"
    # R6
    TIME_DRIFT = "TIME_DRIFT"

    # IO / shape issues
    EVIDENCE_READ_ERROR = "EVIDENCE_READ_ERROR"
    EVIDENCE_SCHEMA_ERROR = "EVIDENCE_SCHEMA_ERROR"


# ---------------------------------------------------------------------
# Time helpers (stable formatting)
# ---------------------------------------------------------------------
def utc_now_z_seconds() -> str:
    # Stable, second-granularity ISO8601 Z
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------
# Violation
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class Violation:
    rule: RuleCode
    severity: Severity
    message: str

    # identification / debugging hints
    evidence_path: Optional[str] = None
    trace_id: Optional[str] = None

    # chain hints
    prev_hash: Optional[str] = None
    this_hash: Optional[str] = None

    # time hints
    created_at_utc: Optional[str] = None
    prev_created_at_utc: Optional[str] = None
    skew_ms: Optional[int] = None

    # extensibility
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["rule"] = self.rule.value
        d["severity"] = self.severity.value
        return d


# ---------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class ChainStats:
    total_evidence: int
    genesis_count: int

    head_hash: Optional[str]
    tail_hash: Optional[str]

    # time range convenience
    head_created_at_utc: Optional[str] = None
    tail_created_at_utc: Optional[str] = None

    orphan_count: int = 0
    duplicate_this_hash_count: int = 0

    # TIME_DRIFT observations
    max_negative_skew_ms: int = 0
    max_positive_skew_ms: int = 0

    # operational debug
    scanned_dir: Optional[str] = None
    chain_head_path: Optional[str] = None
    chain_head_last_hash: Optional[str] = None
    chain_head_state: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class ChainValidationResult:
    status: ChainValidationStatus
    errors: List[Violation] = field(default_factory=list)
    warnings: List[Violation] = field(default_factory=list)
    stats: Optional[ChainStats] = None

    validated_at_utc: str = field(default_factory=utc_now_z_seconds)
    contract_version: str = "chain_validation_result_v1"

    def is_pass(self) -> bool:
        return self.status == ChainValidationStatus.PASS and len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "validated_at_utc": self.validated_at_utc,
            "status": self.status.value,
            "errors": [v.to_dict() for v in self.errors],
            "warnings": [v.to_dict() for v in self.warnings],
            "stats": self.stats.to_dict() if self.stats else None,
        }


# ---------------------------------------------------------------------
# TypedDict views (optional for structural typing)
# ---------------------------------------------------------------------
class ViolationDict(TypedDict, total=False):
    rule: str
    severity: str
    message: str
    evidence_path: str
    trace_id: str
    prev_hash: str
    this_hash: str
    created_at_utc: str
    prev_created_at_utc: str
    skew_ms: int
    context: Dict[str, Any]


class ChainStatsDict(TypedDict, total=False):
    total_evidence: int
    genesis_count: int
    head_hash: str
    tail_hash: str
    head_created_at_utc: str
    tail_created_at_utc: str
    orphan_count: int
    duplicate_this_hash_count: int
    max_negative_skew_ms: int
    max_positive_skew_ms: int
    scanned_dir: str
    chain_head_path: str
    chain_head_last_hash: str
    chain_head_state: str


class ChainValidationResultDict(TypedDict, total=False):
    contract_version: str
    validated_at_utc: str
    status: str
    errors: List[ViolationDict]
    warnings: List[ViolationDict]
    stats: Optional[ChainStatsDict]


# ---------------------------------------------------------------------
# Extensibility hook (optional, default no-op)
# ---------------------------------------------------------------------
ResultHook = Callable[[ChainValidationResult], None]


def _noop_hook(_: ChainValidationResult) -> None:
    return


# ---------------------------------------------------------------------
# Helper builders (pure by default; hook is optional)
# ---------------------------------------------------------------------
def make_pass(
    *,
    stats: Optional[ChainStats] = None,
    warnings: Optional[List[Violation]] = None,
    hook: ResultHook = _noop_hook,
) -> ChainValidationResult:
    res = ChainValidationResult(
        status=ChainValidationStatus.PASS,
        errors=[],
        warnings=warnings or [],
        stats=stats,
    )
    hook(res)
    return res


def make_fail(
    *,
    errors: List[Violation],
    stats: Optional[ChainStats] = None,
    warnings: Optional[List[Violation]] = None,
    hook: ResultHook = _noop_hook,
) -> ChainValidationResult:
    res = ChainValidationResult(
        status=ChainValidationStatus.FAIL,
        errors=errors,
        warnings=warnings or [],
        stats=stats,
    )
    hook(res)
    return res
