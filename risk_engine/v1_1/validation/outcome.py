from enum import Enum


class ValidationOutcome(str, Enum):
    """
    ValidationOutcome (v1.1)

    Represents the result of a single validation decision.

    NOTE:
    - This enum represents judgment, not execution behavior.
    - Mapping to engine actions is handled by policy/orchestration layers.
    """

    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    HARD_STOP = "HARD_STOP"

    def is_terminal(self) -> bool:
        """
        Returns True if this outcome must immediately terminate
        the validation chain.
        """
        return self is ValidationOutcome.HARD_STOP
