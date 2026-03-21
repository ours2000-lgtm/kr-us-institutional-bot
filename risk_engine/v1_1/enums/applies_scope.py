from enum import Enum

class AppliesScope(str, Enum):
    ACCOUNT = "ACCOUNT"
    STRATEGY = "STRATEGY"
    ORDER = "ORDER"
