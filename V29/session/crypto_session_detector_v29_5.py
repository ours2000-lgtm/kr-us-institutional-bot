# ======================================================================
# Crypto Session Detector — V29.5
# ----------------------------------------------------------------------
# 업그레이드 포인트:
#   ✔ 사용자 정의 글로벌 세션 (asia/europe/us → cfg override)
#   ✔ quiet/active 자동 판별 (vol & volume 기반)
#   ✔ 확장된 halt_trading 안전장치
#   ✔ trend flat 처리 (quiet 바이어스)
#   ✔ 종합 debug 정보 (candidates, reasons, ctx_snapshot)
# ======================================================================

from datetime import datetime, time


class CryptoSessionDetectorV29_5:
    """
    Crypto Session Detector V29.5
    - time-based 글로벌 세션 + vol/volume 기반 quiet/active 세션
    - trend-aware, fallback-safe 구조
    """

    DEFAULT_SESSIONS = {
        "asia":    ("00:00", "08:00"),
        "europe":  ("08:00", "16:00"),
        "us":      ("16:00", "24:00"),
    }

    DEFAULT_PRIORITY = ["us", "europe", "asia", "active", "quiet"]

    def __init__(self, cfg=None, local_tz=None):
        self.cfg = cfg or {}
        self.local_tz = local_tz  # Stock과 동일 구조

        # 외부 세션 오버라이드
        self.sessions = self.cfg.get("crypto", {}).get("sessions", self.DEFAULT_SESSIONS)

        # 외부 우선순위 오버라이드
        self.priority = self.cfg.get("crypto", {}).get("priority", self.DEFAULT_PRIORITY)

        # quiet/active thresholds
        thr = self.cfg.get("crypto", {}).get("thresholds", {})
        self.quiet_vol = thr.get("quiet_vol", 0.9)
        self.quiet_volume = thr.get("quiet_volume", 1.0)
        self.active_vol = thr.get("active_vol", 1.2)
        self.active_volume = thr.get("active_volume", 1.2)

        # halt 조건
        self.max_vol_ratio = thr.get("max_vol_ratio", 8.0)
        self.min_volume_ratio = thr.get("min_volume_ratio", 0.2)
        self.funding_reversal_threshold = thr.get("funding_reversal_threshold", 0.005)

    # -------------------------------------------------------------
    def _to_time(self, t):
        """문자 or time object → time 객체 변환"""
        if isinstance(t, time):
            return t
        if isinstance(t, str):
            try:
                h, m = t.split(":")
                return time(int(h), int(m))
            except Exception:
                return None
        return None

    # -------------------------------------------------------------
    def _in_session(self, now, start, end):
        """자정 교차 포함 세션 판별"""
        if start is None or end is None:
            return False
        if start == end:
            return True  # 24시간 세션
        if start < end:
            return start <= now < end
        return now >= start or now < end  # 자정 넘어가는 경우

    # -------------------------------------------------------------
    def _resolve_priority(self, candidates):
        """우선순위 테이블로 최종 세션 선택"""
        for p in self.priority:
            if p in candidates:
                return p
        return "quiet"  # default fallback

    # -------------------------------------------------------------
    def detect(self, ctx=None):
        """
        ctx expected keys:
            - volatility, avg_volatility
            - volume, avg_volume
            - trend_signal: up/down/flat
            - funding_rate, avg_funding_rate
        """
        ctx = ctx or {}
        dbg = {
            "candidates": [],
            "reasons": {},
            "parsed_sessions": {},
            "ctx_snapshot": {k: ctx.get(k) for k in (
                "volatility", "avg_volatility", "volume", "avg_volume",
                "trend_signal", "funding_rate", "avg_funding_rate"
            )}
        }

        now_dt = datetime.now()
        now_time = now_dt.time()

        # ---------------------------------------------------------
        # 1) Time-based 글로벌 세션
        # ---------------------------------------------------------
        parsed = {}

        for name, (start_s, end_s) in self.sessions.items():
            start_t = self._to_time(start_s)
            end_t = self._to_time(end_s)
            parsed[name] = (start_t, end_t)
            dbg["parsed_sessions"][name] = (str(start_t), str(end_t))

            if self._in_session(now_time, start_t, end_t):
                dbg["candidates"].append(name)
                dbg["reasons"][name] = "time_match"

        # ---------------------------------------------------------
        # 2) quiet/active 자동 판별
        # ---------------------------------------------------------
        vol = ctx.get("volatility")
        avg_vol = ctx.get("avg_volatility")
        volume = ctx.get("volume")
        avg_volume = ctx.get("avg_volume")

        # 안전장치: 데이터 누락 → halt
        if any(v is None for v in [vol, avg_vol, volume, avg_volume]):
            return {
                "market": "CRYPTO",
                "session": "quiet",
                "halt_trading": True,
                "reason": "missing_core_data",
                "debug": dbg,
                "timestamp": now_dt.isoformat()
            }

        # ratio 계산
        vol_ratio = vol / max(avg_vol, 1e-9)
        volume_ratio = volume / max(avg_volume, 1e-9)

        dbg["vol_ratio"] = vol_ratio
        dbg["volume_ratio"] = volume_ratio

        # Halt 조건
        if vol_ratio > self.max_vol_ratio or volume_ratio < self.min_volume_ratio:
            return {
                "market": "CRYPTO",
                "session": "quiet",
                "halt_trading": True,
                "reason": "extreme_market_conditions",
                "debug": dbg,
                "timestamp": now_dt.isoformat()
            }

        # quiet / active 판별
        if vol_ratio < self.quiet_vol and volume_ratio < self.quiet_volume:
            dbg["candidates"].append("quiet")
            dbg["reasons"]["quiet"] = "low_vol_low_volume"

        if vol_ratio > self.active_vol and volume_ratio > self.active_volume:
            dbg["candidates"].append("active")
            dbg["reasons"]["active"] = "high_vol_high_volume"

        # ---------------------------------------------------------
        # 3) funding reversal check
        # ---------------------------------------------------------
        f = ctx.get("funding_rate")
        f_avg = ctx.get("avg_funding_rate")

        if f is not None and f_avg is not None:
            if abs(f - f_avg) > self.funding_reversal_threshold:
                dbg["candidates"].append("reversal")
                dbg["reasons"]["reversal"] = f"funding_jump:{round(f - f_avg,6)}"

        # ---------------------------------------------------------
        # 4) Trend-aware 보정
        # ---------------------------------------------------------
        trend = ctx.get("trend_signal")
        if trend == "up":
            dbg["candidates"].append("active")
            dbg["reasons"]["trend_up"] = "active_bias"
        elif trend == "down":
            dbg["candidates"].append("quiet")
            dbg["reasons"]["trend_down"] = "quiet_bias"
        else:  # flat
            dbg["candidates"].append("quiet")
            dbg["reasons"]["trend_flat"] = "quiet_bias"

        # ---------------------------------------------------------
        # 최종 세션 결정
        # ---------------------------------------------------------
        unique_candidates = list(set(dbg["candidates"]))
        final_session = self._resolve_priority(unique_candidates)
        dbg["final_session"] = final_session

        return {
            "market": "CRYPTO",
            "session": final_session,
            "halt_trading": False,
            "debug": dbg,
            "timestamp": now_dt.isoformat(),
        }
