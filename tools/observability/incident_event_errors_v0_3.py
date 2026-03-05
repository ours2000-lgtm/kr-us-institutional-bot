from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class IncidentEventError(Exception):
    """
    Domain error for incident pipeline (v0.3).
    - code: SSOT error code (INCIDENT_ERROR_CODES_v0_3)
    - message: human readable reason (short)
    - context: minimal structured fields for debugging (NO payload dump)
    """

    code: str
    message: str
    context: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        if not self.context:
            return f"[{self.code}] {self.message}"
        return f"[{self.code}] {self.message} | ctx={self.context}"