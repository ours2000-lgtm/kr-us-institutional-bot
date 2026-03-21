# ======================================================================
# CryptoSessionDetector V29.4
# 24H 시장 기반 글로벌 세션 + Trend-aware + Spike/FakePump/Reversal
# Fallback-safe + 디버그 확장 + Stock V29.7과 동일한 구조
# ======================================================================

from datetime import datetime, time
from zoneinfo import ZoneInfo


class CryptoSessionDetectorV29_4:
    """
    24시간 암호화폐 시장 전용 Session Detector (V29.4)

    특징:
    - 글로벌 세션(ASIA/EUROPE/US) 자동 판별
    - 자정 교차 세션(start > end) 완전 지원
    - spike-news / fake-pump / reversal-window 이벤트 감지
    - trend-aware 후보 강화
    - fallback-safe 구조
    - StockSessionDetector V29.7과 동일한 debug 구조
    """

    PRIORITY = [
        "spike-news",
        "fake-pump",
        "reversal-window",
        "us",
        "europe",
        "asia",
        "active",
        "quiet",
        "normal",
    ]

    def __init__(self, cfg, timezone="Asia/Seoul"):
        self.cfg = cfg or {}
        self.tz = timezone

        # Threshold 로드
        thr = self.cfg.get("crypto", {}).get("thresholds", {})
        self.spike_news_vol = thr.get("spike_news_vol", 1.0)
        self.spike_news_volume = thr.get("spike_news_volume", 2.0)
        self.fake_pump_vol = thr.get("fake_pump_vol", 2.0)
        self.fake_pump_volume = thr.get("fake_pump_volume", 0.8)
        self.quiet_vol = thr.get("quiet_vol", 0.9)
        self.funding_min_diff = thr.get("funding_min_diff", 0.005)

        # 세션(time ranges)
        self.sessions = self.cfg.get("crypto", {}).get("sessions", {
            "asia":       ("00:00", "08:00"),
            "europe":     ("08:00", "16:00"),
            "us":         ("16:00", "23:59"),
        })

    # ---------------------------------------------------------
    # Time parsing
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Session inclusion logic (supports midnight cross)
    # ---------------------------------------------------------
    def _in_session(self, now, start, end):
        if start is None or end is None:
            return False

        # Invalid definition
        if start == end:
            return True  # treat as 24h session

        if start < end:
            return start <= now < end
        else:
            # midnight cross
            return now >= start or now < end

    # ---------------------------------------------------------
    # Main detect()
    # ---------------------------------------------------------
    def detect(self, ctx, trend_signal=None):
        dt = datetime.now(ZoneInfo(self.tz))
        now_t = dt.time()

        dbg = {
            "timestamp_local": dt.isoformat(),
            "trend": trend_signal,
            "matches": [],
            "checked_sessions": [],
            "session_times": {},
            "reasons": {},
            "ctx_snapshot": {
                "volatility": ctx.get("volatility"),
                "avg_volatility": ctx.get("avg_volatility"),
                "volume": ctx.get("volume"),
                "avg_volume": ctx.get("avg_volume"),
                "funding": ctx.get("funding"),
                "avg_funding": ctx.get("avg_funding"),
            },
        }

        # Extract market signals
        vol = ctx.get("volatility")
        avg_vol = ctx.get("avg_volatility")
        volume = ctx.get("volume")
        avg_volume = ctx.get("avg_volume")
        funding = ctx.get("funding")
        avg_funding = ctx.get("avg_funding")

        # ------------------------------------------------------
        # Fallback safety for missing data
        # ------------------------------------------------------
        if avg_vol in (None, 0) or avg_volume in (None, 0):
            dbg["reasons"]["fallback"] = "missing_avg_vol_or_avg_volume"
            return {
                "session": "normal",
                "halt_trading": True,
                "priority_session": "normal",
                "debug": dbg,
            }

        # Ratios
        vol_ratio = vol / avg_vol if avg_vol else 1.0
        volume_ratio = volume / avg_volume if avg_volume else 1.0

        # ------------------------------------------------------
        # Spike-news (High volume / Low volatility)
        # ------------------------------------------------------
        if vol_ratio < self.spike_news_vol and volume_ratio > self.spike_news_volume:
            dbg["matches"].append("spike-news")
            dbg["reasons"]["spike-news"] = f"vol_ratio={vol_ratio:.2f}, volume_ratio={volume_ratio:.2f}"

        # ------------------------------------------------------
        # Fake-pump (High volatility / Low volume)
        # ------------------------------------------------------
        if vol_ratio > self.fake_pump_vol and volume_ratio < self.fake_pump_volume:
            dbg["matches"].append("fake-pump")
            dbg["reasons"]["fake-pump"] = f"vol_ratio={vol_ratio:.2f}, volume_ratio={volume_ratio:.2f}"

        # ------------------------------------------------------
        # Reversal-window (Funding sign flip + magnitude)
        # ------------------------------------------------------
        if (funding is not None and avg_funding is not None):
            if (funding * avg_funding < 0) and (abs(funding - avg_funding) > self.funding_min_diff):
                dbg["matches"].append("reversal-window")
                dbg["reasons"]["reversal-window"] = f"funding={funding}, avg_funding={avg_funding}"

        # ------------------------------------------------------
        # Global time-based sessions
        # ------------------------------------------------------
        for name, (st, ed) in self.sessions.items():
            s = self._to_time(st)
            e = self._to_time(ed)
            dbg["checked_sessions"].append(name)
            dbg["session_times"][name] = (st, ed)

            if self._in_session(now_t, s, e):
                dbg["matches"].append(name)
                dbg["reasons"][name] = "time_range_match"

        # ------------------------------------------------------
        # Trend-aware enhancement
        # ------------------------------------------------------
        if trend_signal == "up":
            if "us" not in dbg["matches"]:
                dbg["matches"].append("us")
                dbg["reasons"]["trend_us"] = "trend_up_reinforcement"
        elif trend_signal == "down":
            if "asia" not in dbg["matches"]:
                dbg["matches"].append("asia")
                dbg["reasons"]["trend_asia"] = "trend_down_reinforcement"

        # ------------------------------------------------------
        # Resolve priority
        # ------------------------------------------------------
        final = "normal"
        for p in self.PRIORITY:
            if p in dbg["matches"]:
                final = p
                break

        dbg["resolved"] = final

        return {
            "session": final,
            "priority_session": final,
            "halt_trading": False,
            "debug": dbg,
        }
