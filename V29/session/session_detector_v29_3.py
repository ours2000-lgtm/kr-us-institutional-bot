# session_detector_v29_3.py
# ===============================================================
# StockSessionDetector V29.3 — Trend-aware + Debug-Extended + Safe Mode
# ===============================================================

from datetime import datetime, time


class StockSessionDetectorV29_3:
    """
    V29.3 Upgrade:
    - Trend 영향 강화
    - 세션 정의 오류 검증(start=end / invalid format)
    - candidate 중복 방지
    - debug 정보 확장 (이유 기록)
    - 우선순위 확장 구조
    """

    PRIORITY = [
        "open", "preopen",
        "morning",
        "mid",
        "lunch-dip",
        "close",
        "power-hour",
        "afterhours",
        "quiet"
    ]

    def __init__(self, cfg):
        """
        cfg["markets"]["KR"]["sessions"]
        """
        self.cfg = cfg

    # -----------------------------------------------------------
    # Time parser with safe exception handling
    # -----------------------------------------------------------
    def _to_time(self, t):
        if isinstance(t, time):
            return t
        if isinstance(t, str):
            try:
                h, m = t.split(":")
                return time(int(h), int(m))
            except Exception:
                return None
        return None

    # -----------------------------------------------------------
    # Safe session range checker
    # -----------------------------------------------------------
    def _in_session(self, now_t, start_t, end_t, dbg, name):
        """Handle normal and midnight-crossing sessions with debug."""
        if start_t is None or end_t is None:
            dbg["errors"].append(f"invalid_time_format:{name}")
            return False

        # start == end → ambiguous range
        if start_t == end_t:
            dbg["errors"].append(f"invalid_range_same_start_end:{name}")
            return False

        # Normal range
        if start_t < end_t:
            return start_t <= now_t <= end_t

        # Midnight-crossing case
        return now_t >= start_t or now_t <= end_t

    # -----------------------------------------------------------
    # Priority resolver with candidate logging
    # -----------------------------------------------------------
    def _resolve_priority(self, candidates, dbg):
        """Choose highest priority session."""
        dbg["resolved_candidates"] = list(candidates)
        for p in self.PRIORITY:
            if p in candidates:
                dbg["resolved"] = p
                return p
        dbg["resolved"] = "mid"
        return "mid"

    # -----------------------------------------------------------
    # MAIN: Detect Stock Session
    # -----------------------------------------------------------
    def detect(self, market, now_time, trend_signal="flat"):
        sessions = self.cfg.get("markets", {}).get(market, {}).get("sessions", {})
        dbg = {
            "now": now_time.isoformat(),
            "trend": trend_signal,
            "checked_sessions": list(sessions.keys()),
            "candidates": [],
            "errors": [],
            "reasons": {}
        }

        now_t = now_time.time()

        # -------------------------------------------------------
        # 기본 세션 체크
        # -------------------------------------------------------
        for name, period in sessions.items():
            start = self._to_time(period.get("start"))
            end = self._to_time(period.get("end"))

            if self._in_session(now_t, start, end, dbg, name):
                if name not in dbg["candidates"]:
                    dbg["candidates"].append(name)
                    dbg["reasons"][name] = "time_range_match"

        # -------------------------------------------------------
        # Trend-based adjustments
        # -------------------------------------------------------
        if trend_signal == "up":
            # 강화 후보
            if "open" in sessions and "open" not in dbg["candidates"]:
                dbg["candidates"].append("open")
                dbg["reasons"]["open"] = "trend_up_priority"

            if "power-hour" in sessions and "power-hour" not in dbg["candidates"]:
                dbg["candidates"].append("power-hour")
                dbg["reasons"]["power-hour"] = "trend_up_late_session"

        elif trend_signal == "down":
            if "close" in sessions and "close" not in dbg["candidates"]:
                dbg["candidates"].append("close")
                dbg["reasons"]["close"] = "trend_down_priority"

            if "afterhours" in sessions:
                dbg["reasons"]["afterhours"] = "trend_down_weakening"

        else:
            # flat trend → quiet 후보 강화
            if "quiet" in sessions and "quiet" not in dbg["candidates"]:
                dbg["candidates"].append("quiet")
                dbg["reasons"]["quiet"] = "trend_flat_safety"

        # -------------------------------------------------------
        # Priority resolution
        # -------------------------------------------------------
        final_session = self._resolve_priority(dbg["candidates"], dbg)

        # -------------------------------------------------------
        # Return structure
        # -------------------------------------------------------
        return {
            "market": market,
            "session": final_session,
            "timestamp": now_time.isoformat(),
            "resolved": final_session,
            "debug": dbg,
        }
