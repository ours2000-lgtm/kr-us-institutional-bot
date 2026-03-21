# =====================================================================
# Stock SessionDetector V29
# - KR / US 시장 시간 기반 세션 판별
# - preopen / open / mid / close / afterhours / power-hour 지원
# - midnight crossing (e.g., 22:30 → 05:00) 지원
# - trend_signal 반영 (up/down/flat)
# - candidates + priority 기반 session 선택
# - debug 정보 강화
# =====================================================================

import logging
from datetime import datetime, time


class StockSessionDetectorV29:
    """
    Stock 시장 세션 판별기 (KR/US)
    - market: "KR", "US"
    - now_time: datetime.time
    - ctx: {"trend_signal": "up/down/flat", ...}
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg

        # 세션 우선순위 (priority-based resolution)
        # 앞에 있을수록 우선 적용됨
        self.priority = [
            "open",
            "preopen",
            "power-hour",
            "spike-news",
            "fake-pump",
            "lunch-dip",
            "mid",
            "close",
            "afterhours",
            "quiet",
            "normal",
        ]

    # -------------------------------------------------
    # 시간 문자열/객체 안전 변환
    # -------------------------------------------------
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

    # -------------------------------------------------
    # start-end 구간 판별 (자정 넘김 지원)
    # -------------------------------------------------
    def _in_session(self, now_t: time, start: time, end: time):
        if start is None or end is None:
            return False

        # 잘못된 세션 정의 예외 방어
        if start == end:
            return False

        # 정상 구간
        if start < end:
            return start <= now_t <= end

        # 자정 넘김 구간
        return now_t >= start or now_t <= end

    # -------------------------------------------------
    # 후보 중 우선순위로 최종 세션 결정
    # -------------------------------------------------
    def _resolve_priority(self, candidates: list, dbg):
        if not candidates:
            dbg["resolved"] = "normal"
            return "normal"

        for p in self.priority:
            if p in candidates:
                dbg["resolved"] = p
                return p

        dbg["resolved"] = "normal"
        return "normal"

    # -------------------------------------------------
    # Stock 세션 탐지
    # -------------------------------------------------
    def detect(self, market: str, now_time: time, ctx: dict):
        market = market.upper()

        dbg = {
            "checked_sessions": [],
            "candidates": [],
            "trend_signal": ctx.get("trend_signal"),
            "now_time": now_time.isoformat(),
        }

        sessions_cfg = (
            self.cfg.get("markets", {})
                    .get(market, {})
                    .get("sessions", {})
        )

        if not sessions_cfg:
            # 세션 정의 없음 → fallback
            dbg["reason"] = "no_session_defined"
            return {
                "market": market,
                "session": "normal",
                "candidates": [],
                "debug": dbg,
                "timestamp": datetime.utcnow().isoformat(),
                "fallback": True,
            }

        # ---------------------------------------------
        # ① 시간 기반 세션 후보 추출
        # ---------------------------------------------
        for name, (st, en) in sessions_cfg.items():
            start = self._to_time(st)
            end = self._to_time(en)
            dbg["checked_sessions"].append(name)

            if self._in_session(now_time, start, end):
                dbg["candidates"].append(name)

        # ---------------------------------------------
        # ② Trend 기반 후보 보정
        # ---------------------------------------------
        trend = ctx.get("trend_signal")

        if trend == "up":
            # 상승 추세 → open, power-hour 강화
            if "open" in dbg["candidates"]:
                dbg["candidates"].append("power-hour")

        elif trend == "down":
            # 하락 추세 → quiet or lunch-dip 강화
            if "mid" in dbg["candidates"]:
                dbg["candidates"].append("quiet")
                dbg["candidates"].append("lunch-dip")

        elif trend == "flat":
            # 횡보 → mid/quiet 강화
            if "mid" in dbg["candidates"]:
                dbg["candidates"].append("quiet")

        # ---------------------------------------------
        # ③ 최종 우선순위 결정
        # ---------------------------------------------
        final_session = self._resolve_priority(dbg["candidates"], dbg)

        # ---------------------------------------------
        # ④ 결과 반환
        # ---------------------------------------------
        return {
            "market": market,
            "session": final_session,
            "candidates": list(set(dbg["candidates"])),
            "debug": dbg,
            "timestamp": datetime.utcnow().isoformat(),
            "fallback": False,
        }


# =====================================================================
# Example config
# =====================================================================

"""
예시 CFG 구조:

cfg = {
    "markets": {
        "KR": {
            "sessions": {
                "preopen": ("08:00", "08:59"),
                "open": ("09:00", "09:29"),
                "mid": ("09:30", "14:19"),
                "close": ("14:20", "15:20"),
                "afterhours": ("15:21", "18:00")
            }
        },
        "US": {
            "sessions": {
                "preopen": ("21:00", "22:29"),
                "open": ("22:30", "23:29"),
                "mid": ("23:30", "03:59"),
                "power-hour": ("04:00", "05:00"),
                "afterhours": ("05:01", "08:00")
            }
        }
    }
}
"""

