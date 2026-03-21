from __future__ import annotations

from datetime import datetime
from typing import Literal

Session = Literal["KR_PRE", "KR_OPEN", "US_PRE", "US_OPEN", "CLOSED"]


def detect_session_v0_3(*, ts_utc: datetime) -> Session:
    """
    v0.3 stub:
    - 지금은 로직을 단순화(시간대/휴장/공휴일 미반영)
    - v0.4에서 KR/US 실제 세션 디텍터로 교체
    """
    # 최소 stub: 항상 CLOSED
    return "CLOSED"