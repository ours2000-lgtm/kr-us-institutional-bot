# path: engine/incident_rate_limiter.py

from __future__ import annotations

import time
from collections import defaultdict, deque
from logging import getLogger
from typing import Deque, Dict


logger = getLogger(__name__)


class IncidentRateLimiter:
    """
    동일 incident 폭주 방지

    정책:
    - 동일 reason 기준
    - window_sec 내 max_events 초과 시 차단
    """

    def __init__(self, max_events: int = 5, window_sec: int = 10):
        if max_events <= 0:
            raise ValueError("max_events must be > 0")

        if window_sec <= 0:
            raise ValueError("window_sec must be > 0")

        self.max_events = max_events
        self.window_sec = window_sec

        self._events: Dict[str, Deque[float]] = defaultdict(deque)

    # =====================================================
    # MAIN
    # =====================================================

    def allow(self, reason: str) -> bool:
        now = time.time()
        q = self._events[reason]

        # 오래된 이벤트 제거
        while q and (now - q[0]) > self.window_sec:
            q.popleft()

        if len(q) >= self.max_events:
            logger.warning(
                "INCIDENT_RATE_LIMITED reason=%s count=%s window=%s",
                reason,
                len(q),
                self.window_sec,
            )
            return False

        q.append(now)
        return True