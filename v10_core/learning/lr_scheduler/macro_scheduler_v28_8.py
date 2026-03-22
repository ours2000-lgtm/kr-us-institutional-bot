# ============================================================
# MacroScheduler V28.8  — 안정화 패치본
# ============================================================

from datetime import datetime

class MacroSchedulerV28_8:
    """
    시장별/세션별 매크로 환경을 기반으로 학습률 multiplier를 생성한다.
    - 시장별 clamp 적용
    - halt 발생 시 final_mult = lr_min
    - Crypto volatility key 호환 (vol / volatility)
    - vol_ratio 자동 계산
    - Freeze/Boost 이벤트 구조화
    - trend_signal 반영
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg

        # --------------------------------------------
        # 시장별 clamp 적용 (필수)
        # --------------------------------------------
        self.lr_clamp_map = cfg.get("lr_clamp", {
            "KR": (0.3, 2.0),
            "US": (0.2, 2.0),
            "CRYPTO": (0.1, 3.0),
            "DEFAULT": (0.1, 3.0)
        })

        # --------------------------------------------
        # freeze / boost parameters
        # --------------------------------------------
        freeze_cfg = cfg.get("freeze_rules", {})
        boost_cfg = cfg.get("boost_rules", {})

        self.dd_limit = freeze_cfg.get("dd_limit", 0.15)
        self.vol_spike_ratio = freeze_cfg.get("vol_spike_ratio", 3.0)
        self.min_freeze_mult = freeze_cfg.get("min_freeze_mult", 0.1)

        self.sharpe_min = boost_cfg.get("sharpe_min", 1.2)
        self.trend_boost = boost_cfg.get("trend_boost", 1.1)
        self.trend_freeze = boost_cfg.get("trend_freeze", 0.9)

    # =====================================================================
    # Crypto 세션 판별 (V28.8 안정화)
    # =====================================================================
    def detect_crypto_session(self, ctx: dict):
        """
        ctx:
            vol / avg_vol (또는 volatility / avg_volatility)
            volume / avg_volume
            funding_rate / avg_funding_rate
        """

        # ---- key 일관화 (필수 패치) ----
        vol = ctx.get("vol") or ctx.get("volatility")
        avg_vol = ctx.get("avg_vol") or ctx.get("avg_volatility")

        volume = ctx.get("volume")
        avg_volume = ctx.get("avg_volume")

        funding = ctx.get("funding_rate")
        avg_funding = ctx.get("avg_funding_rate")

        # ---- fallback 방어 ----
        if not vol or not avg_vol or not volume or not avg_volume:
            return {
                "session": "normal",
                "fallback": True,
                "reason": "missing_data",
                "debug": {}
            }

        # ---- ratio 계산 ----
        vol_ratio = vol / max(avg_vol, 1e-9)
        volume_ratio = volume / max(avg_volume, 1e-9)

        dbg = {
            "vol_ratio": vol_ratio,
            "volume_ratio": volume_ratio,
            "funding": funding,
            "avg_funding": avg_funding,
        }

        # ==========================================================
        # 우선순위: spike-news → fake-pump → reversal → quiet → active
        # ==========================================================

        # 1) spike-news (저변동 + 고거래량)
        thr = self.cfg.get("crypto", {}).get("thresholds", {})
        spike_vol = thr.get("spike_news_vol", 1.0)
        spike_volume = thr.get("spike_news_volume", 2.0)

        if vol_ratio < spike_vol and volume_ratio > spike_volume:
            return {
                "session": "spike-news",
                "fallback": False,
                "reason": "event_spike_news",
                "debug": dbg
            }

        # 2) fake-pump (고변동 + 거래량 부진)
        fake_vol = thr.get("fake_pump_vol", 2.0)
        fake_volume = thr.get("fake_pump_volume", 0.8)

        if vol_ratio > fake_vol and volume_ratio < fake_volume:
            return {
                "session": "fake-pump",
                "fallback": False,
                "reason": "event_fake_pump",
                "debug": dbg
            }

        # 3) funding reversal
        if (
            funding is not None
            and avg_funding is not None
            and (funding * avg_funding < 0)  # sign flip
            and abs(funding - avg_funding) > 0.005  # magnitude filter
        ):
            return {
                "session": "reversal-window",
                "fallback": False,
                "reason": "funding_reversal",
                "debug": dbg
            }

        # 4) quiet
        quiet_thr = thr.get("quiet_vol", 0.8)
        if vol_ratio < quiet_thr:
            return {
                "session": "quiet",
                "fallback": False,
                "reason": "low_volatility",
                "debug": dbg
            }

        # 5) active (default)
        return {
            "session": "active",
            "fallback": False,
            "reason": "default_active",
            "debug": dbg
        }

    # =====================================================================
    # 최종 Macro Multiplier 계산
    # =====================================================================
    def get_macro_multiplier(self, market: str, ctx: dict):
        market = market.upper()

        # ---- 시장별 clamp 적용 ----
        lr_min, lr_max = self.lr_clamp_map.get(market, self.lr_clamp_map["DEFAULT"])

        # ---- 기본값 ----
        freeze_mult = 1.0
        boost_mult = 1.0
        events = {"freeze": [], "boost": [], "halt": []}

        dd = ctx.get("dd")
        sharpe = ctx.get("sharpe")
        trend_signal = ctx.get("trend_signal")

        # ===============================
        # Crypto 세션 판별
        # ===============================
        if market == "CRYPTO":
            session_info = self.detect_crypto_session(ctx)
            session = session_info["session"]
            fallback = session_info["fallback"]

            if fallback:
                events["halt"].append("missing_crypto_data")
                final = lr_min
                return self._pack(final, freeze_mult, boost_mult, lr_min, lr_max, events, session)

        else:
            session = "normal"

        # ========================================================
        # 핵심 지표 누락 시 HALT (필수 안정장치)
        # ========================================================
        if dd is None or sharpe is None:
            events["halt"].append("missing_core_metrics")
            return self._pack(lr_min, freeze_mult, boost_mult, lr_min, lr_max, events, session)

        # ========================================================
        # Freeze Conditions
        # ========================================================
        if dd > self.dd_limit:
            freeze_mult *= 0.7
            events["freeze"].append("dd_freeze")

        vol_ratio = ctx.get("vol_ratio")
        if vol_ratio is None:
            # 자동 계산 패치
            v = ctx.get("vol") or ctx.get("volatility")
            av = ctx.get("avg_vol") or ctx.get("avg_volatility")
            if v and av:
                vol_ratio = v / max(av, 1e-9)

        if vol_ratio and vol_ratio > self.vol_spike_ratio:
            freeze_mult *= 0.7
            events["freeze"].append("vol_spike_freeze")

        # freeze 하한선
        if freeze_mult < self.min_freeze_mult:
            freeze_mult = self.min_freeze_mult
            events["freeze"].append("freeze_floor")

        # ========================================================
        # Boost Conditions
        # ========================================================
        if sharpe > self.sharpe_min:
            boost_mult *= 1.1
            events["boost"].append("sharpe_boost")

        # trend_signal 반영 (필수)
        if trend_signal == "up":
            boost_mult *= self.trend_boost
            events["boost"].append("trend_up_boost")
        elif trend_signal == "down":
            freeze_mult *= self.trend_freeze
            events["freeze"].append("trend_down_freeze")

        # ========================================================
        # final multiplier
        # ========================================================
        raw_mult = freeze_mult * boost_mult
        final_mult = max(lr_min, min(raw_mult, lr_max))

        return self._pack(final_mult, freeze_mult, boost_mult, lr_min, lr_max, events, session)

    # =====================================================================
    def _pack(self, final, freeze_mult, boost_mult, lr_min, lr_max, events, session):
        return {
            "final_mult": final,
            "freeze_mult": freeze_mult,
            "boost_mult": boost_mult,
            "lr_min": lr_min,
            "lr_max": lr_max,
            "session": session,
            "events": events,
            "timestamp": datetime.utcnow().isoformat(),
        }
