# ============================================================
# Snapshot Grades (CANONICAL SCHEMA)
# Constitution Appendix Version: v1.0
#
# This file defines canonical, fail-closed snapshot grade enums
# used across Decision, Snapshot, Validator, Executor, Audit,
# and ML systems.
#
# These enums MUST NOT be reinterpreted or remapped by consumers.
# ============================================================

from enum import Enum


class SnapshotQualityGrade(str, Enum):
    """
    Constitution v1.0 — Snapshot Quality Grade Specification

    Ordering is intentional (higher risk → lower risk):

    UNKNOWN
    DEGRADED
    GOOD
    HEALTHY

    Semantics:
    - UNKNOWN  : Snapshot cannot be validated. FAIL-CLOSED.
    - DEGRADED : Snapshot partially invalid or stale. FAIL-CLOSED.
    - GOOD     : Snapshot valid with minor issues. PASS with caution.
    - HEALTHY  : Snapshot fully valid. PASS.

    This enum is canonical and MUST be interpreted consistently
    across Decision, Snapshot, Validator, Executor, Audit and ML systems.
    """

    UNKNOWN = "UNKNOWN"
    DEGRADED = "DEGRADED"
    GOOD = "GOOD"
    HEALTHY = "HEALTHY"

    # Severity scale: higher = worse (canonical 0–9 scale)
    _SEVERITY_MAP: dict[str, int] = {
        "HEALTHY": 0,
        "GOOD": 3,
        "DEGRADED": 6,
        "UNKNOWN": 9,
    }

    @property
    def severity(self) -> int:
        """
        Severity level in the canonical 0–9 scale.

        - 0 = best (HEALTHY)
        - 3 = minor issues (GOOD)
        - 6 = degraded
        - 9 = worst (UNKNOWN)

        Higher means worse.
        """
        return self._SEVERITY_MAP[self.value]

    @property
    def is_safe(self) -> bool:
        """True if this grade is acceptable for decision making."""
        return self in {SnapshotQualityGrade.GOOD, SnapshotQualityGrade.HEALTHY}

    @property
    def is_fail_closed(self) -> bool:
        """True if this grade MUST trigger fail-closed behavior."""
        return not self.is_safe


class SystemHealthGrade(str, Enum):
    """
    Constitution v1.0 — System Health Grade Specification

    Ordering is intentional (higher risk → lower risk):

    UNKNOWN
    UNSTABLE
    STABLE
    HEALTHY

    Semantics:
    - UNKNOWN  : Health state cannot be determined. FAIL-CLOSED.
    - UNSTABLE : System unstable or partially failing. FAIL-CLOSED.
    - STABLE   : System operational with minor issues. PASS with caution.
    - HEALTHY  : System fully operational. PASS.

    This enum is canonical and MUST be interpreted consistently
    across Decision, Snapshot, Validator, Executor, Audit and ML systems.
    """

    UNKNOWN = "UNKNOWN"
    UNSTABLE = "UNSTABLE"
    STABLE = "STABLE"
    HEALTHY = "HEALTHY"

    # Severity scale: higher = worse (canonical 0–9 scale)
    _SEVERITY_MAP: dict[str, int] = {
        "HEALTHY": 0,
        "STABLE": 3,
        "UNSTABLE": 6,
        "UNKNOWN": 9,
    }

    @property
    def severity(self) -> int:
        """
        Severity level in the canonical 0–9 scale.

        - 0 = best (HEALTHY)
        - 3 = minor issues (STABLE)
        - 6 = unstable
        - 9 = worst (UNKNOWN)

        Higher means worse.
        """
        return self._SEVERITY_MAP[self.value]

    @property
    def is_safe(self) -> bool:
        """True if this grade is acceptable for decision making."""
        return self in {SystemHealthGrade.STABLE, SystemHealthGrade.HEALTHY}

    @property
    def is_fail_closed(self) -> bool:
        """True if this grade MUST trigger fail-closed behavior."""
        return not self.is_safe
