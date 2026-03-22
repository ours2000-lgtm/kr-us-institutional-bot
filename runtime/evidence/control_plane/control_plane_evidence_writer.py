# path: runtime/evidence/control_plane/control_plane_evidence_writer.py

from logging import getLogger
from typing import Any, Dict, Optional

from runtime.evidence.control_plane.control_plane_evidence_schema import (
    write_control_plane_evidence,
)


logger = getLogger(__name__)


class ControlPlaneEvidenceWriter:
    def __init__(self, base_dir: str = "runtime/evidence/control_plane"):
        self.base_dir = str(base_dir)

    def write(
        self,
        category: str,
        event_type: str,
        component: Optional[str] = None,
        state: Optional[str] = None,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        reason: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        try:
            return write_control_plane_evidence(
                base_dir=self.base_dir,
                category=category,
                event_type=event_type,
                component=component,
                state=state,
                symbol=symbol,
                side=side,
                reason=reason,
                payload=payload,
            )
        except Exception:
            logger.exception(
                "CONTROL_PLANE_EVIDENCE_WRITE_FAILED "
                "category=%s event_type=%s component=%s state=%s symbol=%s side=%s reason=%s",
                category,
                event_type,
                component,
                state,
                symbol,
                side,
                reason,
            )
            return None