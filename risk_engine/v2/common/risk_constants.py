# risk_constants.py

# ============================================================
# AccountRiskGuard – Global Constants
# Constitution Appendix Version: v2.0.1 FINAL
# ============================================================

MODEL_VERSION = "v2.0.1"

from enum import Enum


class AccountRiskAction(str, Enum):
    """
    AccountRiskGuard Action Enum
    - Enum name == serialized value (JSON/DB safe)
    - No default allowed (must be explicitly provided)
    """

    ALLOW = "ALLOW"
    REDUCE = "REDUCE"
    BLOCK = "BLOCK"
    HARD_STOP = "HARD_STOP"

class AccountRiskReason(str, Enum):
    """
    Primary reason for AccountRiskDecision.
    Only ONE dominant reason is allowed.

    NOTE:
    - New reasons require Constitution + Enum change together.
    """

    ACCOUNT_KILL_SWITCH = "ACCOUNT_KILL_SWITCH"
    DAILY_LOSS_LIMIT_EXCEEDED = "DAILY_LOSS_LIMIT_EXCEEDED"
    TECHNICAL_FAILURE = "TECHNICAL_FAILURE"

    # Throttle / flow control related
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Optional but practical
    SNAPSHOT_QUALITY_DEGRADED = "SNAPSHOT_QUALITY_DEGRADED"
    MANUAL_BLOCK = "MANUAL_BLOCK"


