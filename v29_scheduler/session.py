# v29_scheduler/session.py

from datetime import datetime


class SessionDetectorV29:

    def __init__(self, cfg):
        self.cfg = cfg
        self.crypto_thr = cfg.get("crypto", {}).get("thresholds", {})

    # -------------------------------
    # Helper: session time check
    # -------------------------------
    def _in_session(self, now, start, end):
        if start is None or end is None:
            return False
        if start == end:
            return True
        return (start <= now <= end) if start < end else (now >= start or now <= end)

    # -------------------------------
    # Stock Session Detection
    # -------------------------------
    def detect_stock(self, market, now_time):
        sessions = self.cfg.get("markets", {}).get(market, {}).get("sessions", {})
        for name, s in sessions.items():
            if self._in_session(now_time, s.get("start"), s.get("end")):
                return {"session": name, "fallback": False}
        return {"session": "normal", "fallback": True}

    # -------------------------------
    # Crypto Session Detection
    # -------------------------------
    def detect_crypto(self, ctx):
        vol = ctx.get("volatility")
        avg_vol = ctx.get("avg_vol")
        volume = ctx.get("volume")
        avg_volume = ctx.get("avg_volume")
        funding = ctx.get("funding_rate")
        avg_funding = ctx.get("avg_funding_rate")

        # Data missing fallback
        if any(v is None for v in [vol, avg_vol, volume, avg_volume]):
            return {"session": "normal", "fallback": True}

        vol_ratio = vol / max(avg_vol, 1e-9)
        volume_ratio = volume / max(avg_volume, 1e-9)

        thr = self.crypto_thr

        if vol_ratio < thr["spike_news_vol"] and volume_ratio > thr["spike_news_volume"]:
            return {"session": "spike-news", "fallback": False}

        if vol_ratio > thr["fake_pump_vol"] and volume_ratio < thr["fake_pump_volume"]:
            return {"session": "fake-pump", "fallback": False}

        if funding is not None and avg_funding is not None:
            if funding * avg_funding < 0:
                return {"session": "reversal-window", "fallback": False}

        if vol_ratio < thr["quiet_vol"]:
            return {"session": "quiet", "fallback": False}

        return {"session": "active", "fallback": False}

    # -------------------------------
    # Public API
    # -------------------------------
    def detect(self, market, now_time, ctx=None):
        market = market.upper()

        if market in ("KR", "US"):
            return self.detect_stock(market, now_time)

        if market == "CRYPTO":
            return self.detect_crypto(ctx or {})

        return {"session": "normal", "fallback": True}
