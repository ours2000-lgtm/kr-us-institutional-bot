# KR_US_INSTITUTION_BOT/src/fsm/policy.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Set

from .violations import InvariantViolation, Severity


@dataclass(frozen=True)
class PolicyDecision:
    fail_closed: bool
    criticals: List[InvariantViolation]
    warnings: List[InvariantViolation]
    ignored: List[InvariantViolation] = field(default_factory=list)
    policy_id: str = "DefaultFailClosedPolicy/v1"


class ValidationPolicy:
    def decide(self, violations: Iterable[InvariantViolation]) -> PolicyDecision:
        raise NotImplementedError


@dataclass(frozen=True)
class DefaultFailClosedPolicy(ValidationPolicy):
    """
    Default:
    - Any CRITICAL triggers fail_closed=True
    - WARNING does not trigger fail_closed
    - ignored_codes: treat matching codes as ignored (even if CRITICAL)
    """
    ignored_codes: Set[str] = field(default_factory=set)
    policy_id: str = "DefaultFailClosedPolicy/v1"

    def decide(self, violations: Iterable[InvariantViolation]) -> PolicyDecision:
        criticals: List[InvariantViolation] = []
        warnings: List[InvariantViolation] = []
        ignored: List[InvariantViolation] = []

        for v in violations:
            if v.code in self.ignored_codes:
                ignored.append(v)
                continue

            if v.severity == Severity.WARNING:
                warnings.append(v)
            else:
                criticals.append(v)

        return PolicyDecision(
            fail_closed=(len(criticals) > 0),
            criticals=criticals,
            warnings=warnings,
            ignored=ignored,
            policy_id=self.policy_id,
        )
