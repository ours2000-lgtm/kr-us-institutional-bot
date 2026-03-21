from datetime import datetime, time
from zoneinfo import ZoneInfo

class StockSessionDetectorV29_7:
    """
    Stock Session Detector V29.7
    - KST timezone 적용
    - Trend 확장 적용
    - Debug 정보 강화
    - Invalid time format 기록
    - Session 정의 누락 처리 강화
    """

    # 세션 우선순위
    PRIORITY = ["open", "morning", "mid", "close", "power-hour", "afterhours"]

    def __init__(self, cfg):
        self.cfg = cfg

    # ---------------------------------------------------------
    # 안전한 time 파서
    # ---------------------------------------------------------
    def _to_time(self, t, dbg, session_name=None):
        if isinstance(t, time):
            return t
        if isinstance(t, str):
            try:
                h, m = t.split(":")
                return time(int(h), int(m))
            except Exception:
                if session_name:
                    dbg["invalid_time_format"].append(session_name)
                return None
        return None

    # ---------------------------------------------------------
    # 세션 포함 여부 판정
    # ---------------------------------------------------------
    def _in_session(self, now_t: time, start: time, end: time, dbg, session_name):
        if start is None or end is None:
            return False

        # start == end → 사실상 잘못된 정의 → 기록 후 False 처리
        if start == end:
            dbg["invalid_range_same_start_end"].append(session_name)
            return False

        if start < end:
            return start <= now_t <= end

        # 자정 넘김(예: 22:30~02:00)
        return now_t >= start or now_t <= end

    # ---------------------------------------------------------
    # 메인 세션 판별
    # ---------------------------------------------------------
    def detect(self, market: str, trend_signal=None):
        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
        now_t = now_kst.time()

        dbg = {
            "timestamp_local": now_kst.isoformat(),
            "checked_sessions": [],
            "parsed_times": {},
            "invalid_time_format": [],
            "invalid_range_same_start_end": [],
            "candidates": [],
            "trend_applied": None,
            "fallback": False,
            "reasons": {},
        }

        sessions = (
            self.cfg.get("markets", {})
            .get(market, {})
            .get("sessions", {})
        )

        # ---------------------------------------------------------
        # 세션 정의 누락 처리
        # ---------------------------------------------------------
        if not sessions:
            dbg["fallback"] = True
            dbg["reasons"]["no_sessions_defined"] = True
            final_session = "mid"
            dbg["resolved"] = final_session
            return {
                "market": market,
                "session": final_session,
                "debug": dbg,
            }

        # ---------------------------------------------------------
        # 세션별 시간 파싱 및 후보 탐색
        # ---------------------------------------------------------
        for name, span in sessions.items():
            dbg["checked_sessions"].append(name)

            start = self._to_time(span.get("start"), dbg, name)
            end = self._to_time(span.get("end"), dbg, name)
            dbg["parsed_times"][name] = (start, end)

            if self._in_session(now_t, start, end, dbg, name):
                if name not in dbg["candidates"]:
                    dbg["candidates"].append(name)
                    dbg["reasons"][name] = "time_range_match"

        # ---------------------------------------------------------
        # Trend signal 영향 반영
        # ---------------------------------------------------------
        if trend_signal == "up":
            dbg["trend_applied"] = "up"
            for boost_s in ["morning", "close", "power-hour"]:
                if boost_s in sessions and boost_s not in dbg["candidates"]:
                    dbg["candidates"].append(boost_s)
                    dbg["reasons"][boost_s] = "trend_up_boost"

        elif trend_signal == "down":
            dbg["trend_applied"] = "down"
            if "afterhours" in sessions and "afterhours" not in dbg["candidates"]:
                dbg["candidates"].append("afterhours")
                dbg["reasons"]["afterhours"] = "trend_down_bias"

        else:
            dbg["trend_applied"] = "flat"

        # ---------------------------------------------------------
        # 후보 없으면 mid fallback
        # ---------------------------------------------------------
        if not dbg["candidates"]:
            dbg["fallback"] = True
            dbg["reasons"]["fallback_default"] = "no_candidate_sessions"
            final_session = "mid"
            dbg["resolved"] = final_session
            return {
                "market": market,
                "session": final_session,
                "debug": dbg,
            }

        # ---------------------------------------------------------
        # 우선순위 적용
        # ---------------------------------------------------------
        for p in self.PRIORITY:
            if p in dbg["candidates"]:
                final_session = p
                dbg["resolved"] = p
                break

        return {
            "market": market,
            "session": final_session,
            "debug": dbg,
        }
