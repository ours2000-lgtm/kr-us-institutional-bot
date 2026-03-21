# stock_session_detector_v29_6.py
import datetime
from datetime import datetime as dt, time


class StockSessionDetectorV29_6:
    """
    Stock Session Detector — V29.6
    추가 개선:
      - start == end 의심 설정 기록 (invalid_range_same_start_end)
      - trend 기본값을 flat 처리 (일관적 동작)
      - 세션 정의 누락 시 명확한 fallback 이유 기록
      - UTC + local timestamp 동시 기록
    """

    DEFAULT_PRIORITY = [
        "open", "morning", "mid", "close", "power-hour", "afterhours"
    ]

    def __init__(self, cfg: dict, local_timezone="Asia/Seoul"):
        self.cfg = cfg
        self.local_timezone = local_timezone

        market_cfg = cfg.get("markets", {}).get("KR", {})
        self.priority = market_cfg.get("session_priority", self.DEFAULT_PRIORITY)

    # ---------------------------------------------------------
    # 안전한 time 파싱
    # ---------------------------------------------------------
    def _to_time(self, raw, dbg):
        if isinstance(raw, time):
            return raw

        if isinstance(raw, str):
            try:
                h, m = raw.split(":")
                return time(int(h), int(m))
            except Exception:
                dbg["invalid_time_format"].append(raw)
                return None

        dbg["invalid_time_format"].append(str(raw))
        return None

    # ---------------------------------------------------------
    # 세션 범위 체크 (자정 교차 포함)
    # ---------------------------------------------------------
    def _in_session(self, now_t: time, start: time, end: time, name: str, dbg):
        if start is None or end is None:
            return False

        # start == end → 의심 설정 → 기록 후 True (24시간 세션처럼 동작)
        if start == end:
            dbg["invalid_range_same_start_end"].append(name)
            return True

        # 일반 범위
        if start < end:
            return start <= now_t <= end

        # 자정 교차
        return now_t >= start or now_t <= end

    # ---------------------------------------------------------
    # 시간 기반 후보 탐색
    # ---------------------------------------------------------
    def _gather_candidates(self, sessions: dict, now_t: time, dbg: dict):
        parsed = {}

        for name, (st_raw, ed_raw) in sessions.items():
            st = self._to_time(st_raw, dbg)
            ed = self._to_time(ed_raw, dbg)

            parsed[name] = (st, ed)

            if self._in_session(now_t, st, ed, name, dbg):
                if name not in dbg["candidates"]:
                    dbg["candidates"].append(name)
                    dbg["reasons"][name] = "time_in_session"

        dbg["parsed_times"] = parsed

    # ---------------------------------------------------------
    # trend 적용 (flat 기본값)
    # ---------------------------------------------------------
    def _apply_trend_bias(self, trend, dbg: dict):
        # 기본값 flat
        if trend is None:
            trend = "flat"

        if trend == "up":
            if "morning" not in dbg["candidates"]:
                dbg["candidates"].append("morning")
                dbg["reasons"]["morning"] = "trend_up_bias"

        elif trend == "down":
            if "close" not in dbg["candidates"]:
                dbg["candidates"].append("close")
                dbg["reasons"]["close"] = "trend_down_bias"

        elif trend == "flat":
            if "mid" not in dbg["candidates"]:
                dbg["candidates"].append("mid")
                dbg["reasons"]["mid"] = "trend_flat_mid_boost"

    # ---------------------------------------------------------
    # 우선순위 기반 최종 선출 + debug 기록
    # ---------------------------------------------------------
    def _resolve_priority(self, dbg):
        cands = list(set(dbg["candidates"]))

        if not cands:
            dbg["resolved"] = "mid"
            dbg["reasons"]["mid"] = "fallback_no_candidates"
            return "mid"

        for p in self.priority:
            if p in cands:
                dbg["resolved"] = p
                return p

        dbg["resolved"] = "mid"
        dbg["reasons"]["mid"] = "fallback_priority_not_matched"
        return "mid"

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------
    def detect(self, market: str, now_time: time, trend_signal=None):
        dbg = {
            "candidates": [],
            "reasons": {},
            "priority": self.priority,
            "checked_sessions": [],
            "invalid_time_format": [],
            "invalid_range_same_start_end": [],
        }

        market = market.upper()
        mk_cfg = self.cfg.get("markets", {}).get(market, {})

        if not mk_cfg:
            dbg["reasons"]["no_sessions_defined"] = True
            return {
                "market": market,
                "session": "mid",
                "debug": dbg,
                "timestamp_utc": dt.utcnow().isoformat(),
                "timestamp_local": dt.now().isoformat(),
            }

        sessions = mk_cfg.get("sessions", {})
        dbg["checked_sessions"] = list(sessions.keys())

        # Step 1 — 시간 기반 후보 집계
        self._gather_candidates(sessions, now_time, dbg)

        # Step 2 — trend 반영 (flat 기본)
        self._apply_trend_bias(trend_signal, dbg)

        # Step 3 — 우선순위 결정
        final_session = self._resolve_priority(dbg)

        return {
            "market": market,
            "session": final_session,
            "candidates": dbg["candidates"],
            "debug": dbg,
            "timestamp_utc": dt.utcnow().isoformat(),
            "timestamp_local": dt.now().isoformat(),
        }
