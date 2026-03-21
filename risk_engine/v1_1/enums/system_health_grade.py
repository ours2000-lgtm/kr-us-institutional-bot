from enum import Enum

class SystemHealthGrade(Enum):
    GOOD = "good"
    FAIL_CLOSED = "fail_closed"
    UNKNOWN = "unknown"
