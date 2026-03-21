from dataclasses import dataclass
from typing import Dict, Any

from .outcome import ValidationOutcome


@dataclass(frozen=True)
class ValidationResult:
    """
    ValidationResult (v1.1)

    Captures the result of a validation step, including
    the outcome and contextual information for observability,
    debugging, and replay.

    This structure is intentionally immutable.
    """

    outcome: ValidationOutcome
    reason: str
    validator: str
    grades: Dict[str, Any]

    def is_terminal(self) -> bool:
        """
        Convenience proxy for outcome.is_terminal().
        """
        return self.outcome.is_terminal()
