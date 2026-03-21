# KR_US_INSTITUTION_BOT/src/fsm/violations.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class Layer(str, Enum):
    GENESIS = "G"
    L1_SHAPE = "L1"
    L2_TRANSITION = "L2"
    L3_SEMANTIC = "L3"


class Severity(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class InvariantViolation:
    layer: Layer
    code: str
    message: str
    event_index: int = -1
    context: Dict[str, Any] = field(default_factory=dict)
    severity: Severity = Severity.CRITICAL
