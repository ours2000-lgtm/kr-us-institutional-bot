# ========================================================================
# Macro Scheduler V28.5 — Crypto Session 안정화 버전
# ------------------------------------------------------------------------
# 핵심 개선:
#   ✓ Crypto 세션 판별 우선순위 정렬
#       spike-news → fake-pump → reversal-window → 기본 vol-based
#   ✓ avg_vol / avg_volume None 및 0 방어
#   ✓ debug 옵션 강화
#   ✓ freeze/boost 엔진에서 바로 사용할 수 있도록 session/regime 표준화
# ========================================================================

from datetime import datetime, time


class MacroSchedulerV28_5:
    def __init__(self, cfg: dict, debug: bool = False):
        self.cfg = cfg
        self.debug = debug

        # 시장별 클램프 범위 (시장마다 다르게 적용 가능)
        self.market_clamp = cfg.get("lr_clamp", {
            "KR": (0.3, 2.0),
            "US": (0.2, 2.5),
            "CRYPTO": (0.1, 3.0),
            "DEFAULT": (0.1, 3.0)
        })

        # freeze lower bound
        self.min_freeze_mult = cfg.get("min_freeze_mult", 0.1)

    # ------------------------------------------------------------
    # Stock Session 판별 (KR, US)
    # ------------------------------------------------------------
    def _to_time(self, tstr):
        if tstr is None:
            return None
        h, m = map(int, tstr.split(":"))
        return time(h, m)

    def _in_session(self, now_t: time, start: time, end: time):
        """자정 넘김 세션 처리 포함"""
        if start is None or end is None:
            return False

        if start == end:  # 24시간 세션
            return True

        if start <= end:
            return start <= now_t <= end
        else:
            # 자정 넘기는 세션
            return now_t >= start or now_t <= end

    def _get_stock_session(self, market: str, now: datetime):
        market = market.upper()
        now_t = now.time()

        sessions = self.cfg.get("markets", {}).get(market, {}).get("sessions", {})

        for sname, sdef in sessions.items():
            start = self._to_time(sdef.get("start"))
            end = self._to_time(sdef.get("end"))

            if self._in_session(now_t, start, end):
                return sname

        return "mid"  # fallback

    # ------------------------------------------------------------
    # Crypto Session 판별 안정화 버전 (V28.5)
    # ------------------------------------------------------------
    def _get_crypto_session(self, info: dict, debug=False):
        """
        Crypto 세션 판별 우선순위:
        1) spike-news        (volume ↑↑, vol ↓)
        2) fake-pump         (vol ↑↑, volume ↓)
        3) reversal-window   (funding 급변)
        4) spike             (vol ↑↑)
        5) quiet             (vol 매우 낮음)
        6) active            (기본)
        """

        vol = info.get("vol")
        avg_vol = info.get("avg_vol")
        volume = info.get("volume")
        avg_volume = info.get("avg_volume")
        funding = info.get("funding_rate")
        avg_funding = info.get("avg_funding_rate")

        dbg = {}

        # 방어 코드 (None or zero)
        if avg_vol is None or avg_vol == 0 or avg_volume is None or avg_volume == 0:
            return ("normal", {"reason": "insufficient_data"})

        vol_ratio = vol / (avg_vol + 1e-8)
        volume_ratio = volume / (avg_volume + 1e-8)

        dbg["vol_ratio"] = vol_ratio
        dbg["volume_ratio"] = volume_ratio
        dbg["funding"] = funding
        dbg["avg_funding"] = avg_funding

        # --------------------------------------------------------
        # 1) spike-news (뉴스 기반 급등)
        # --------------------------------------------------------
        if volume_ratio > 2.0 and vol_ratio < 1.0:
            return ("spike-news", dbg)

        # --------------------------------------------------------
        # 2) fake-pump (가짜 펌핑)
        # --------------------------------------------------------
        if vol_ratio > 2.0 and volume_ratio < 0.8:
            return ("fake-pump", dbg)

        # --------------------------------------------------------
        # 3) reversal-window (funding rate 급변)
        # --------------------------------------------------------
        if funding is not None and avg_funding is not None:
            if abs(funding - avg_funding) > self.cfg.get("crypto", {}).get("funding_jump", 0.002):
                return ("reversal-window", dbg)

        # --------------------------------------------------------
        # 4) spike (단순 변동성 급등)
        # --------------------------------------------------------
        if vol_ratio > 2.0:
            return ("spike", dbg)

        # --------------------------------------------------------
        # 5) quiet (저변동성)
        # --------------------------------------------------------
        if vol_ratio < 0.7:
            return ("quiet", dbg)

        # --------------------------------------------------------
        # 6) active (기본)
        # --------------------------------------------------------
        return ("active", dbg)

    # ------------------------------------------------------------
    # Public Interface
    # ------------------------------------------------------------
    def get_session(self, market: str, now: datetime, info: dict = None, debug=False):
        market = market.upper()

        if market in ["KR", "US"]:
            session = self._get_stock_session(market, now)
            return {"market": market, "session": session, "debug": {}}

        elif market == "CRYPTO":
            session, dbg = self._get_crypto_session(info or {}, debug=debug)
            return {"market": market, "session": session, "debug": dbg}

        else:
            return {"market": market, "session": "unknown", "debug": {}}
