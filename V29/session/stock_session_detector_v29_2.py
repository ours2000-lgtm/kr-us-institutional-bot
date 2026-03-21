# ================================================================
# StockSessionDetector V29.2
#  - 안정성 강화
#  - trend_signal 활용 강화
#  - 중복 후보 방지
#  - _to_time() 예외 처리
#  - debug 상세 정보 포함
# ================================================================

from datetime import datetime, time

class StockSessionDetectorV29_2:
    """
    한국/미국 주식 시장 세션 감지기 V29.2
    - session priority 명확화
    - trend 영향 반영
    - debug 확장
    """

    PRIORITY = [
        "open",
        "morning",
        "mid",
        "close",
        "power-hour",
        "afterhours"
    ]

    def __init__(self, cfg: dict):
        self.cfg = cfg

    # -----------------------------------------------------------
    # 시간 파싱 안전 처리
    # -----------------------------------------------------------
    def _to_time(self, val):
        if isinstance(val, time):
            return val
        if isinstance(val, str):
            try:
                h, m = val.split(":")
                return time(int(h), int(m))
            except Exception:
                return None
        return None

    # -----------------------------------------------------------
    # 세션 시간 포함 여부 체크
    # -----------------------------------------------------------
    def _in_session(self, now, start, end):
        if start is None or end is None:
            return False
        if start <= end:
            return start <= now <= end
        # 자정 넘김
        return now >= start or now <= end

    # -----------------------------------------------------------
    # 후보 추가 (중복 방지)
    # -----------------------------------------------------------
    def _add_candidate(self, dbg, name, reason):
        if name not in dbg["candidates"]:
            dbg["candidates"].append(name)
            dbg["reasons"][name] = reason

    # -----------------------------------------------------------
    # 우선순위 해석
    # -----------------------------------------------------------
    def _resolve_priority(self, dbg):
        for key in self.PRIORITY:
            if key in dbg["candidates"]:
                dbg["resolved"] = key
                return key
        dbg["resolved"] = "normal"
        return "normal"

    # -----------------------------------------------------------
    # MAIN: 주식 시장 세션 탐지
    # -----------------------------------------------------------
    def detect_stock(self, market, now_time, ctx):
        """
        ctx 예시:
        {
            "trend_signal": "up" / "down" / "flat"
        }
        """

        cfg = self.cfg.get("markets", {}).get(market.upper(), {})
        sessions = cfg.get("sessions", {})

        dbg = {
            "market": market,
            "now_time": now_time.isoformat(),
            "candidates": [],
            "checked": list(sessions.keys()),
            "reasons": {},
            "trend": ctx.get("trend_signal"),
        }

        # -------------------------------
        # 모든 세션 조건 체크
        # -------------------------------
        for name, sj in sessions.items():
            start = self._to_time(sj.get("start"))
            end = self._to_time(sj.get("end"))

            if start is None or end is None:
                dbg["reasons"][name] = "invalid_time_format"
                continue

            if self._in_session(now_time, start, end):
                self._add_candidate(
                    dbg,
                    name,
                    reason=f"in_session-{start}-{end}"
                )

        # -------------------------------
        # trend 영향 반영
        # -------------------------------
        trend = ctx.get("trend_signal")
        if trend == "up":
            self._add_candidate(dbg, "open", "trend_up")
        elif trend == "down":
            self._add_candidate(dbg, "close", "trend_down")
        elif trend == "flat":
            dbg["trend_influence"] = "flat_recorded"

        # -------------------------------
        # 우선순위로 최종 세션 선택
        # -------------------------------
        final_session = self._resolve_priority(dbg)

        return {
            "market": market,
            "session": final_session,
            "candidates": dbg["candidates"],
            "resolved": final_session,
            "debug": dbg,
            "timestamp": datetime.utcnow().isoformat(),
        }
