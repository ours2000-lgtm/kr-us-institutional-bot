# ============================================================
# MacroScheduler V28.6 — Unified Macro Control
# - Stock + Crypto 세션 통합
# - spike-news / fake-pump / reversal-window 선처리
# - threshold 외부 설정
# - session fallback 강화
# - freeze/boost 이벤트 로그 강화
# - 시장별 clamp 적용
# ============================================================

from datetime import datetime, time

class MacroSchedulerV28_6:
    """
    시장(global) 흐름을 반영해 LR multiplier를 조정하는 상위 스케줄러.
    V28.6 특징:
      ✓ Stock/Crypto 통합 세션 판별
      ✓ spike-news → fake-pump → reversal-window → 기본 vol-based 순서
      ✓ threshold 외부화 (cfg["crypto"]["thresholds"])
      ✓ freeze/boost 중첩 시 Freeze 우선
      ✓ 시장별 clamp 범위 적용
      ✓ debug 정보 확장
      ✓ missing avg_vol, avg_volume 방어
    """

    def __init__(self, cfg):
        self.cfg = cfg

        # 시장별 clamp 범위
        self.market_clamp = cfg.get("market_clamp", {
            "KR": (0.3, 2.0),
            "US": (0.2, 2.5),
            "CRYPTO": (0.1, 3.0),
            "DEFAULT": (0.1, 5.0)
        })

        # Freeze 하한선
        self.min_freeze_mult = cfg.get("min_freeze_mult", 0.1)

        # Crypto threshold 외부화
        self.crypto_thr = cfg.get("crypto", {}).get("thresholds", {
            "spike_news_vol": 1.0,
            "spike_news_volume": 2.0,
            "fake_pump_vol": 2.0,
            "fake_pump_volume": 0.8,
            "quiet_vol": 0.7,
            "reversal_funding_jump": 0.01
        })

    # ------------------------------------------------------------
    # 시간 파싱 유틸
    # ------------------------------------------------------------
    def _to_time(self, t):
        if isinstance(t, time):
            return t
        if isinstance(t, str):
            try:
                h, m = map(int, t.split(":"))
                return time(h, m)
            except:
                return None
        return None

    def _in_session(self, now, start, end):
        """자정 넘김 세션도 정상 처리"""
        if start is None or end is None:
            return False

        if start == end:
            return True  # 24h session

        if start < end:
            return start <= now <= end
        else:
            return now >= start or now <= end

    # ------------------------------------------------------------
    # STOCK SESSION
    # ------------------------------------------------------------
    def _get_stock_session(self, market, now):
        mk = market.upper()
        sessions = self.cfg.get("markets", {}).get(mk, {}).get("sessions", {})
        
        for sess_name, se in sessions.items():
            st = self._to_time(se.get("start"))
            ed = self._to_time(se.get("end"))
            if self._in_session(now, st, ed):
                return sess_name.lower(), {}

        return "mid", {"fallback": True}

    # ------------------------------------------------------------
    # CRYPTO SESSION (V28.6 최종)
    # ------------------------------------------------------------
    def _get_crypto_session(self, ctx):
        """
        spike-news → fake-pump → reversal-window → 기본 vol-based
        """

        vol = ctx.get("vol")
        avg_vol = ctx.get("avg_vol")
        volume = ctx.get("volume")
        avg_volume = ctx.get("avg_volume")
        funding = ctx.get("funding_rate")
        avg_funding = ctx.get("avg_funding_rate")

        dbg = {}
        
        # 데이터 누락 방어
        if (avg_vol is None or avg_vol == 0 or
            avg_volume is None or avg_volume == 0):
            return "normal", {"fallback": "insufficient_data"}

        vol_ratio = vol / avg_vol if avg_vol else 1.0
        volume_ratio = volume / avg_volume if avg_volume else 1.0

        dbg.update({
            "vol_ratio": round(vol_ratio, 3),
            "volume_ratio": round(volume_ratio, 3),
            "funding": funding,
            "avg_funding": avg_funding
        })

        t = self.crypto_thr

        # --------------------------------------------------------
        # 1) spike-news
        # vol 낮음 + volume 빠르게 증가
        # --------------------------------------------------------
        if (vol_ratio < t["spike_news_vol"] and volume_ratio > t["spike_news_volume"]):
            return "spike-news", dbg

        # --------------------------------------------------------
        # 2) fake-pump
        # vol 높음 + 거래량 감소 → 가짜 펌핑 가능성
        # --------------------------------------------------------
        if (vol_ratio > t["fake_pump_vol"] and volume_ratio < t["fake_pump_volume"]):
            return "fake-pump", dbg

        # --------------------------------------------------------
        # 3) reversal-window
        # funding 급변 or sign change
        # --------------------------------------------------------
        if funding is not None and avg_funding is not None:
            if abs(funding - avg_funding) > t["reversal_funding_jump"]:
                return "reversal-window", dbg
            if funding * avg_funding < 0:
                return "reversal-window", dbg

        # --------------------------------------------------------
        # 4) 기본 vol 기반
        # --------------------------------------------------------
        if vol_ratio < t["quiet_vol"]:
            return "quiet", dbg
        else:
            return "active", dbg

    # ------------------------------------------------------------
    # 메인 엔트리
    # ------------------------------------------------------------
    def get_macro_multiplier(self, market, ctx, debug=False):
        """
        market: KR/US/CRYPTO
        ctx: {
            "now": datetime,
            "vol": float,
            "avg_vol": float,
            "volume": float,
            "avg_volume": float,
            "dd": float,
            "sharpe": float,
            "funding_rate": float,
            ...
        }
        """

        market = market.upper()
        now = ctx.get("now", datetime.utcnow())
        now_t = time(now.hour, now.minute)

        events = []
        dbg = {}

        # --------------------------------------------------------
        # 1) 세션 판별
        # --------------------------------------------------------
        if market == "CRYPTO":
            session, sdbg = self._get_crypto_session(ctx)
        else:
            session, sdbg = self._get_stock_session(market, now_t)

        dbg["session"] = session
        dbg["session_dbg"] = sdbg

        # --------------------------------------------------------
        # 2) freeze/boost 기본 설정
        # --------------------------------------------------------
        freeze_mult = 1.0
        boost_mult = 1.0

        dd = ctx.get("dd", 0)
        sharpe = ctx.get("sharpe", 0)
        vol = ctx.get("vol", 1.0)
        avg_vol = ctx.get("avg_vol", 1.0)
        vol_ratio = vol / avg_vol if avg_vol else 1.0

        # ---------------- FREEZE ----------------
        if dd > 0.15:
            freeze_mult *= 0.5
            events.append("freeze_dd")

        if vol_ratio > 2.5:
            freeze_mult *= 0.7
            events.append("freeze_vol")

        if freeze_mult < self.min_freeze_mult:
            freeze_mult = self.min_freeze_mult
            events.append("freeze_floor")

        # ---------------- BOOST ----------------
        if freeze_mult == 1.0:
            if sharpe > 2.0:
                boost_mult *= 1.08
                events.append("boost_sharpe")

            if session in ["open", "spike-news"]:
                boost_mult *= 1.05
                events.append("boost_open")

        # Freeze 우선권
        if freeze_mult < 1.0:
            boost_mult = 1.0

        # --------------------------------------------------------
        # 3) market/session multiplier
        # --------------------------------------------------------
        m_mult = self.cfg.get("market_mult", {}).get(market, 1.0)
        s_mult = self.cfg.get("session_mult", {}).get(session, 1.0)

        # --------------------------------------------------------
        # 4) 합성
        # --------------------------------------------------------
        raw_mult = m_mult * s_mult * freeze_mult * boost_mult

        # --------------------------------------------------------
        # 5) 시장별 clamp
        # --------------------------------------------------------
        lo, hi = self.market_clamp.get(market, self.market_clamp["DEFAULT"])
        final_mult = max(lo, min(raw_mult, hi))

        dbg.update({
            "market_mult": m_mult,
            "session_mult": s_mult,
            "freeze_mult": freeze_mult,
            "boost_mult": boost_mult,
            "raw_mult": raw_mult,
            "final_mult": final_mult,
            "events": events
        })

        return (final_mult, dbg) if debug else final_mult
