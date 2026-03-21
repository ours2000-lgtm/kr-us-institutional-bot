# risk_engine/v1_1/validation/orchestrator.py

from dataclasses import dataclass
from typing import List, Protocol

from risk_engine.v1_1.validation.outcome import ValidationOutcome


class Validator(Protocol):
    def validate(self, decision) -> ValidationOutcome:  # pragma: no cover (skeleton)
        ...


@dataclass
class ValidationOrchestrator:
    validators: List[Validator]

    def run(self, decision):
        """
        v1.1 skeleton.

        Orchestrator behavior is intentionally undefined in v1.1.
        Behavioral contract will be introduced in v1.2+.
        """
        raise NotImplementedError(
            "ValidationOrchestrator behavior is defined in v1.2+."
        )
