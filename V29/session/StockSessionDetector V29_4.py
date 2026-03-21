# =====================================================================
# StockSessionDetector V29.4 — 안정화 패치
#  - afterhours 후보 누락 문제 해결
#  - fallback 이유 기록 추가
#  - 세션 정의 누락(no_sessions_defined) 로그 추가
#  - 중복 후보 자동 제거
#  - trend 영향 보강
# =====================================================================

import datetime
from datetime import time

class StockSessionDetectorV294:

    PRIORITY = [
        "open",
        "morning",
        "mid",
        "close",
        "power-hour",
        "afterhours"
    ]

    def __init__(self, cfg=None):
        self.cfg = cfg or {}

    # -----------------------------
    # 유틸: 안전한 시간 파싱
    # -----------------------------
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

    def _in_session(self, now_time, start, end):
        """자정 넘김 포함 세션 범위 처리"""
        if not start or not end:
            return False

        if start == end:
            return False  # 잘못된 설정으로 간주

        if start < end:
            return start <= now_time < end

        # 자정 넘김 케이스
        return (now_time >= start) or (now_time < end)

    # -----------------------------
    # 세션 후보 판별
    # -----------------------------
    def detect(self, market, now_time, trend_signal="flat"):
        dbg = {
            "candidates": [],
            "reasons": {},
            "checked_sessions": [],
            "trend": trend_signal,
            "fallback": False
        }

        sessions_cfg = (
            self.cfg.get("markets", {})
            .get(market, {})
            .get("sessions", {})
        )

        # -----------------------------
        # 세션 정의 누락 처리
        # -----------------------------
        if not sessions_cfg:
            dbg["fallback"] = True
            dbg["reasons"]["no_sessions_defined"] = True
            return {
                "market": market,
                "session": "mid",
                "debug": dbg,
                "resolved": "mid",
                "timestamp": now_time.isoformat(),
            }

        # -----------------------------
        # 모든 세션 체크
        # -----------------------------
        for name, se in sessions_cfg.items():
            dbg["checked_sessions"].append(name)

            start = self._to_time(se.get("start"))
            end = self._to_time(se.get("end"))

            if start is None or end is None:
                dbg["reasons"][name] = "invalid_time_format"
                continue

            if self._in_session(now_time, start, end):
                if name not in dbg["candidates"]:
                    dbg["candidates"].append(name)
                dbg["reasons"][name] = "time_match"

        # -----------------------------
        # Trend 보조 로직 확장
        # -----------------------------
        if trend_signal == "up" and "power-hour" in sessions_cfg:
            if "power-hour" not in dbg["candidates"]:
                dbg["candidates"].append("power-hour")
            dbg["reasons"]["power-hour_trend"] = "trend_up_boost"

        if trend_signal == "down" and "afterhours" in sessions_cfg:
            # ✔ V29.3 문제점: 후보에 추가되지 않던 오류 수정
            if "afterhours" not in dbg["candidates"]:
                dbg["candidates"].append("afterhours")
            dbg["reasons"]["afterhours_trend"] = "trend_down_weakening"

        # -----------------------------
        # 후보가 없는 경우 fallback
        # -----------------------------
        if not dbg["candidates"]:
            dbg["fallback"] = True
            dbg["reasons"]["fallback_default"] = True
            dbg["candidates"].append("mid")

        # 중복 제거 & 우선순위 결정
        candidates = list(set(dbg["candidates"]))
        resolved = self._resolve_priority(candidates)
        dbg["resolved"] = resolved

        return {
            "market": market,
            "session": resolved,
            "debug": dbg,
            "resolved": resolved,
            "timestamp": now_time.isoformat(),
        }

    # -----------------------------
    # 우선순위 기반 세션 결정
    # -----------------------------
    def _resolve_priority(self, candidates):
        if not candidates:
            return "mid"
        for p in self.PRIORITY:
            if p in candidates:
                return p
        return "mid"
