import datetime

class MacroSchedulerV28_7:
    """
    Macro-level LR control:
    - Session detection (stock, crypto)
    - Freeze/Boost logic (with priority)
    - Safety: fallback detection → halt_trading
    - trend_signal integrated
    """

    def __init__(self, cfg):
        self.cfg = cfg

        # 시장별 기본 multiplier
        self.market_mult = cfg.get("market_mult", {
            "KR": 1.0, "US": 1.0, "CRYPTO": 1.0
        })

        # 시장별 clamp 범위
        self.lr_clamp = cfg.get("lr_clamp", {
            "KR": (0.3, 2.0),
            "US": (0.2, 2.0),
            "CRYPTO": (0.1, 3.0),
            "DEFAULT": (0.3, 2.0)
        })

        self.min_freeze_mult = cfg.get("min_freeze_mult", 0.1)

        # freeze/boost threshold
        self.freeze_rules = cfg.get("freeze_rules", {
            "dd_limit": 0.15,
            "vol_spike_ratio": 2.5
        })

        self.boost_rules = cfg.get("boost_rules", {
            "sharpe_min": 1.5,
            "trend_up_mult": 1.1,
            "trend_down_mult": 0.9
        })

        # Crypto 세션 threshold
        self.crypto_thr = cfg.get("crypto_thresholds", {
            "spike_news_vol": 1.0,
            "spike_news_volume": 2.0,
            "fake_pump_vol": 2.0,
            "fake_pump_volume": 0.8,
            "quiet_vol": 0.7
        })

        # 우선순위 테이블
        self.crypto_priority = [
            "spike-news",
            "fake-pump",
            "reversal-window",
            "quiet",
            "active"
        ]

    # ------------------------------------------
    # 유틸: 세션 시간 판별
    # ------------------------------------------
    def _in_session(self, start, end, now):
        """자정 넘김 포함 세션 판별"""
        if start is None or end is None:
            return False
        if start == end:
            # 24시간 세션인지, 설정 오류인지 → 여기선 False 안정 처리
            return False

        if start <= end:
            return start <= now <= end
        else:
            # 자정 넘김 세션
            return now >= start or now <= end

    # ------------------------------------------
    # Stock session 판별
    # ------------------------------------------
    def _get_stock_session(self, market, now):
        sessions = self.cfg.get("markets", {}).get(market, {}).get("sessions", {})
        if not sessions:
            return ("normal", {"fallback": True})

        for name, t in sessions.items():
            try:
                start = datetime.time.fromisoformat(t["start"])
                end = datetime.time.fromisoformat(t["end"])
            except:
                continue

            if self._in_session(start, end, now):
                return (name, {"fallback": False})

        return ("normal", {"fallback": True})

    # ------------------------------------------
    # Crypto session 판별 (우선순위 기반)
    # ------------------------------------------
    def _get_crypto_session(self, ctx):
        dbg = {}
        vol = ctx.get("vol")
        avg_vol = ctx.get("avg_vol")
        volume = ctx.get("volume")
        avg_volume = ctx.get("avg_volume")
        funding = ctx.get("funding_rate")
        avg_funding = ctx.get("avg_funding_rate")

        # 빈 값 → 즉시 안전장치 발동
        if None in (vol, avg_vol, volume, avg_volume):
            return ("normal", {"fallback": True, "reason": "missing_data"})

        # ratio 계산
        vol_ratio = vol / max(avg_vol, 1e-9)
        volm_ratio = volume / max(avg_volume, 1e-9)
        dbg.update({"vol_ratio": vol_ratio, "volume_ratio": volm_ratio})

        candidates = []

        # 1) spike-news (최우선)
        if vol_ratio > self.crypto_thr["spike_news_vol"] and volm_ratio > self.crypto_thr["spike_news_volume"]:
            candidates.append("spike-news")

        # 2) fake-pump
        if vol_ratio > self.crypto_thr["fake_pump_vol"] and volm_ratio < self.crypto_thr["fake_pump_volume"]:
            candidates.append("fake-pump")

        # 3) reversal-window (funding rate 급변)
        if funding is not None and avg_funding is not None:
            if funding * avg_funding < 0:
                candidates.append("reversal-window")

        # 4) quiet
        if vol_ratio < self.crypto_thr["quiet_vol"]:
            candidates.append("quiet")

        # 아무 조건 안 맞으면 active
        if not candidates:
            candidates = ["active"]

        # 우선순위 적용
        for key in self.crypto_priority:
            if key in candidates:
                return (key, {"fallback": False, "debug": dbg, "candidates": candidates})

        return ("active", {"fallback": True, "debug": dbg})

    # ------------------------------------------
    # freeze/boost 계산
    # ------------------------------------------
    def get_macro_multiplier(self, market, session, ctx, trend_signal=None, debug=False):
        """
        ctx:
          dd, vol_ratio, sharpe, ...
        """
        dd = ctx.get("dd", 0)
        vol_ratio = ctx.get("vol_ratio", 1.0)
        sharpe = ctx.get("sharpe", 0.0)

        freeze_mult = 1.0
        boost_mult = 1.0
        events = []

        # 1) Freeze 조건
        if dd > self.freeze_rules["dd_limit"]:
            freeze_mult *= 0.5
            events.append("freeze_dd")

        if vol_ratio > self.freeze_rules["vol_spike_ratio"]:
            freeze_mult *= 0.7
            events.append("freeze_vol")

        # freeze 하한
        if freeze_mult < self.min_freeze_mult:
            freeze_mult = self.min_freeze_mult
            events.append("freeze_floor")

        # 2) Boost 조건
        if sharpe > self.boost_rules["sharpe_min"]:
            boost_mult *= 1.1
            events.append("boost_sharpe")

        # trend_signal 반영
        if trend_signal == "up":
            boost_mult *= self.boost_rules["trend_up_mult"]
            events.append("boost_trend")
        elif trend_signal == "down":
            freeze_mult *= self.boost_rules["trend_down_mult"]
            events.append("freeze_trend")

        # freeze가 있으면 boost는 약화 (무효화 X)
        if freeze_mult < 1.0:
            boost_mult *= 0.8

        raw_mult = freeze_mult * boost_mult

        # 시장별 clamp
        clamp_min, clamp_max = self.lr_clamp.get(market, self.lr_clamp["DEFAULT"])
        final_mult = max(clamp_min, min(raw_mult, clamp_max))

        if debug:
            return {
                "raw_mult": raw_mult,
                "final_mult": final_mult,
                "freeze_mult": freeze_mult,
                "boost_mult": boost_mult,
                "events": events,
            }

        return final_mult
