# 경로: E:\AI_TRADING\KR_US_INSTITUTIONAL_BOT\v2\utils\time_utils.py

from __future__ import annotations

from datetime import datetime, timezone


def now_iso_utc() -> str:
    """
    UTC 기준 ISO8601 문자열 (millisecond precision, 'Z' suffix).
    예: 2025-12-11T01:23:45.678Z
    """
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )
