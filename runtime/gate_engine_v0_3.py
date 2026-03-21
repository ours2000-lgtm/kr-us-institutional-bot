from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

Decision = str  # "ALLOW" | "BLOCK"
Grade = str     # "PASS" | "WARN" | "FAIL"


def evaluate_gate_v0_3(
    *,
    ts_utc: datetime,
    trace_id: Optional[str],
    session: str,
) -> Dict[str, Any]:
    """
    v0.3 stub:
    - 실제로는 governance validator / health evaluator 결과를 읽어서 gate 결정을 내림
    - 지금은 FAIL-CLOSED 예시를 위해 기본 BLOCK 반환
    """
    # FAIL-CLOSED default
    return {
        "decision": "BLOCK",
        "grade": "FAIL",
        "policy_ref": "POLICY-VALAGG-CRIT-001",
        "reason": "v0.3 stub: fail-closed default",
        "session": session,
    }