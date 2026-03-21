# tools/control_plane/gate_strict_v1.py
from __future__ import annotations

from tools.governance_validator.result_contract import (
    ChainValidationResult,
    ChainValidationStatus,
)


def evaluate_gate_strict_v1(res: ChainValidationResult) -> bool:
    """
    STRICT Gate Matrix v1

    BLOCK if:
      - status != PASS
      - any errors present

    ALLOW if:
      - PASS and no errors (warnings allowed)
    """
    if res.status != ChainValidationStatus.PASS:
        return False

    if res.errors and len(res.errors) > 0:
        return False

    return True