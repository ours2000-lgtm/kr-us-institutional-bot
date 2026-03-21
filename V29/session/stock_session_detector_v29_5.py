# stock_session_detector_v29_5.py
import datetime
from datetime import datetime as dt, time

class StockSessionDetectorV29_5:
    """
    Stock Session Detector — V29.5
    개선 사항:
        1) parsed_times 기록 → 디버그 강화
        2) trend == flat 처리 → mid 강화
        3) priority 외부 오버라이드 가능
        4) invalid time format 감지 및 기록
    """

    DEFAULT_PRIORITY = [
        "open", "morning", "mid", "close", "power-hour", "afterhours"
    ]

    def __init__(self, cfg: dict):
        self.cfg = cfg

        # priority external override
        market_cfg = cfg.get("markets", {}).get("KR", {})
        self.priority = market_cfg.get("session_priority", self.DEFAULT_PRIORITY)

    # ----------------------------------------------------------
    # 안전한 time 파싱 + 디버그에 invalid 기록
    # ----------------------------------------------------------
    def _to_time(self, t, dbg):
        if isinstance(t, time):
            return t

        if isinstance(t, str):
            try:
                h, m = t.split(":")
                return time(int(h), int(m))
            except Exception:
                dbg["invalid_time_format"].append(t)
                return None

        dbg["invalid_time_format"].append(str(t))
        return None

    # ----------------------------------------------------------
    # 범용 세션 판별 (자정 교차 포함)
    # ----------------------------------------------------------
    def _in_session(self, now_t: time, start: time, end: time) -> bool:
        if start is None or end is None:
            return False

        if start == end:
            return True

        if start < end:
            return start <= now_t <= end
        else:
            return now_t >= start or now_t <= end

    # ----------------------------------------------------------
    # 세션 후보 집계
    # ----------------------------------------------------------
    def _gather_candidates(self, sessions: dict, now_t: time, dbg: dict):
        parsed_times = {}
        for name, (st_raw, ed_raw) in sessions.items():
            st = self._to_time(st_raw, dbg)
            ed = self._to_time(ed_raw, dbg)

            parsed_times[name] = (st, ed)

            if self._in_session(now_t, st, ed):
                if name not in dbg["candidates"]:
                    dbg["candidates"].append(name)
                    dbg["reasons"][name] = "time_in_session"

        dbg["parsed_times"] = parsed_times

    # ----------------------------------------------------------
    # 트렌드 적용 (flat 처리 추가)
    # ----------------------------------------------------------
    def _apply_trend_bias(self, trend_signal, dbg: dict):
        if trend_signal == "up":
            # 오전 장 uptrend 강화
            if "morning" not in dbg["candidates"]:
                dbg["candidates"].append("morning")
                dbg["reasons"]["morning"] = "trend_up_bias"

        elif trend_signal == "down":
            # close 약세 처리
            if "close" not in dbg["candidates"]:
                dbg["candidates"].append("close")
                dbg["reasons"]["close"] = "trend_down_bias"

        elif trend_signal == "flat":
            # flat일 때 mid 강화
            if "mid" not in dbg["candidates"]:
                dbg["candidates"].append("mid")
                dbg["reasons"]["mid"] = "trend_flat_mid_boost"

    # ----------------------------------------------------------
    # 우선순위 선출 + debug 기록
    # ----------------------------------------------------------
    def _resolve_priority(self, dbg: dict):
        cands = list(set(dbg["candidates"]))  # 중복 제거

        if not cands:
            dbg["resolved"] = "mid"
            dbg["reasons"]["mid"] = "fallback_default"
            return "mid"

        for p in self.priority:
            if p in cands:
                dbg["resolved"] = p
                return p

        dbg["resolved"] = "mid"
        return "mid"

    # ----------------------------------------------------------
    # Public Detect API
    # ----------------------------------------------------------
    def detect(self, market: str, now_time: time, trend_signal=None):
        dbg = {
            "candidates": [],
            "reasons": {},
            "priority": self.priority,
            "checked_sessions": [],
            "invalid_time_format": [],
        }

        market = market.upper()
        markets_cfg = self.cfg.get("markets", {})

        if market not in markets_cfg:
            dbg["reasons"]["invalid_market"] = f"{market} not in config"
            return {
                "market": market,
                "session": "mid",
                "debug": dbg,
                "timestamp": dt.utcnow().isoformat(),
            }

        sessions = markets_cfg[market].get("sessions", {})

        dbg["checked_sessions"] = list(sessions.keys())

        # Step 1: 시간 기반 후보 집계
        self._gather_candidates(sessions, now_time, dbg)

        # Step 2: trend 반영
        if trend_signal:
            self._apply_trend_bias(trend_signal, dbg)

        # Step 3: 우선순위 기반 최종 세션 선택
        final_session = self._resolve_priority(dbg)

        return {
            "market": market,
            "session": final_session,
            "debug": dbg,
            "timestamp": dt.utcnow().isoformat(),
            "candidates": dbg["candidates"],
        }
