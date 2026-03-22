# ======================================================================
# MacroScheduler V28.4 — Market-Aware + Crypto-Aware + Freeze/Boost Engine
# ----------------------------------------------------------------------
# 특징:
#   ✔ 한국/미국 시장 세션 완전 대응 (자정 넘김 처리)
#   ✔ Crypto 24h 시장: normal / active / quiet / spike-news / fake-pump
#   ✔ Freeze/Boost 중첩 처리 + 우선순위 + 하한선 적용
#   ✔ market_mult × session_mult × freeze × boost × clamp 통합
#   ✔ Debug: raw_final vs clamped, freeze/boost 이벤트 상세 기록
# ======================================================================

from datetime import datetime, time

class MacroSchedulerV28_4:

    def __init__(self, cfg):
        """
        cfg 구조 예시:
        {
            "lr_clamp": {"KR": [0.3, 1.8], "US": [0.2, 2.0], "CRYPTO": [0.1, 3.0]},
            "market_mult": {"KR": 0.9, "US": 1.0, "CRYPTO": 1.1},
            "session_mult": {
                "KR": {"open": 1.15, "mid": 0.95, "late": 1.10},
                "US": {"open": 1.10, "mid": 1.00, "late": 1.05},
                "CRYPTO": {"active": 1.20, "normal": 1.00, "quiet": 0.85,
                           "spike_news": 1.35, "fake_pump": 0.70}
            },
            "freeze": {
                "dd_ratio": 0.12,
                "vol_ratio": 1.50,
                "freeze_mult": 0.6,
                "freeze_floor": 0.10
            },
            "boost": {
                "trend_signal": 0.65,
                "momentum_signal": 0.80,
                "boost_mult": 1.20
            },
            "stock_sessions": {
                "KR": {
                    "open": ["09:00", "09:20"],
                    "mid": ["09:21", "14:20"],
                    "late": ["14:21", "15:20"]
                },
                "US": {
                    "open": ["23:30", "01:00"],
                    "mid": ["01:01", "05:00"],
                    "late": ["05:01", "06:00"]
                }
            }
        }
        """
        self.cfg = cfg

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _to_time(self, s):
        if s is None:
            return None
        try:
            hh, mm = s.split(":")
            return time(int(hh), int(mm))
        except:
            return None

    def _in_session(self, now_t, start_t, end_t):
        """자정 넘김까지 완전 지원"""
        if start_t is None or end_t is None:
            return False

        if start_t == end_t:
            return True  # 24시간 세션 의미

        if start_t <= end_t:
            return start_t <= now_t <= end_t
        else:
            # 자정 넘김
            return (now_t >= start_t) or (now_t <= end_t)

    # ------------------------------------------------------------------
    # Stock market session detection (KR/US)
    # ------------------------------------------------------------------
    def _get_stock_session(self, market, now_t):
        market = market.upper()
        cfg_sess = self.cfg.get("stock_sessions", {}).get(market)

        if not cfg_sess:
            return "mid"  # 기본값

        for name, (s, e) in cfg_sess.items():
            st = self._to_time(s)
            et = self._to_time(e)
            if self._in_session(now_t, st, et):
                return name

        return "mid"

    # ------------------------------------------------------------------
    # Crypto 24h session detection
    # ------------------------------------------------------------------
    def _get_crypto_session(self, ctx):
        vol = ctx.get("volatility", 0)
        volume = ctx.get("volume", 0)
        avg_vol = ctx.get("avg_volatility", 1e-6)
        avg_volume = ctx.get("avg_volume", 1e-6)

        # 상대적 변화율
        vol_ratio = vol / avg_vol
        vol_up = vol_ratio >= 1.5
        vol_down = vol_ratio <= 0.7

        vol_change_rate = abs(vol_ratio - 1.0)

        # 뉴스성 급등
        if vol_down and (volume > avg_volume * 2.0):
            return "spike_news"

        # Fake pump (vol↑ but volume↓)
        if vol_up and (volume < avg_volume * 0.7):
            return "fake_pump"

        # 일반 active 구간
        if vol_ratio >= 1.2:
            return "active"

        if vol_ratio <= 0.8:
            return "quiet"

        return "normal"

    # ------------------------------------------------------------------
    # Main interface
    # ------------------------------------------------------------------
    def get_multiplier(self, market, ctx, debug_level="basic"):
        """
        ctx 필드:
        - volatility
        - volume
        - avg_volatility
        - avg_volume
        - dd (drawdown ratio)
        - trend_signal
        - momentum_signal
        - timestamp (datetime)
        """
        market = market.upper()
        dd = ctx.get("dd", 0)
        trend_sig = ctx.get("trend_signal", 0)
        mom_sig = ctx.get("momentum_signal", 0)
        now_dt = ctx.get("timestamp", datetime.utcnow())
        now_t = now_dt.time()

        # --------------------------------------------------------------
        # Market multiplier
        # --------------------------------------------------------------
        market_mult = self.cfg.get("market_mult", {}).get(market, 1.0)

        # --------------------------------------------------------------
        # Session multiplier
        # --------------------------------------------------------------
        if market in ("KR", "US"):
            session = self._get_stock_session(market, now_t)
        else:
            session = self._get_crypto_session(ctx)

        session_mult = (
            self.cfg.get("session_mult", {})
                .get(market, {})
                .get(session, 1.0)
        )

        # --------------------------------------------------------------
        # Freeze logic
        # --------------------------------------------------------------
        freeze_evts = []
        freeze_mult = 1.0
        f_cfg = self.cfg.get("freeze", {})
        dd_thresh = f_cfg.get("dd_ratio", 0.12)
        vol_thresh = f_cfg.get("vol_ratio", 1.50)
        f_mult = f_cfg.get("freeze_mult", 0.6)
        f_floor = f_cfg.get("freeze_floor", 0.10)

        vol = ctx.get("volatility", 0)
        avg_vol = ctx.get("avg_volatility", 1e-6)

        if dd >= dd_thresh:
            freeze_mult *= f_mult
            freeze_evts.append("freeze_dd")

        if vol >= avg_vol * vol_thresh:
            freeze_mult *= f_mult
            freeze_evts.append("freeze_vol")

        if freeze_mult < f_floor:
            freeze_mult = f_floor
            freeze_evts.append("freeze_floor")

        # --------------------------------------------------------------
        # Boost logic
        # --------------------------------------------------------------
        boost_evts = []
        b_cfg = self.cfg.get("boost", {})
        boost_mult = 1.0
        b_base = b_cfg.get("boost_mult", 1.20)

        if freeze_evts:
            boost_mult = 1.0
        else:
            if trend_sig >= b_cfg.get("trend_signal", 0.65):
                boost_mult *= b_base
                boost_evts.append("boost_trend")

            if mom_sig >= b_cfg.get("momentum_signal", 0.80):
                boost_mult *= b_base
                boost_evts.append("boost_momentum")

        # --------------------------------------------------------------
        # Combine multipliers
        # --------------------------------------------------------------
        raw_final = market_mult * session_mult * freeze_mult * boost_mult

        # --------------------------------------------------------------
        # Clamp
        # --------------------------------------------------------------
        cmin, cmax = self.cfg.get("lr_clamp", {}).get(market, [0.1, 3.0])
        cmin = float(cmin)
        cmax = float(cmax)

        clamped = max(cmin, min(raw_final, cmax))

        if debug_level == "off":
            return clamped, {}

        dbg = {
            "market": market,
            "session": session,
            "market_mult": market_mult,
            "session_mult": session_mult,
            "freeze_mult": freeze_mult,
            "boost_mult": boost_mult,
            "raw_final_mult": raw_final,
            "clamped_mult": clamped,
            "freeze_events": freeze_evts,
            "boost_events": boost_evts,
        }

        if debug_level == "basic":
            return clamped, dbg

        if debug_level == "full":
            dbg["ctx"] = ctx
            dbg["lr_clamp"] = [cmin, cmax]
            return clamped, dbg
