# =====================================================================
# MacroScheduler V28.7 — Safety Patch Version
# ---------------------------------------------------------------------
# 포함된 즉시 패치:
#   1) fallback 발생 시 halt_trading=True
#   2) spike-news 조건 → 저변동 + 고거래량으로 수정
#   3) funding reversal magnitude 조건 추가
#   4) final_mult = market_mult × freeze_mult × boost_mult 구조 적용
#   5) 반환 구조 완전 통일 + debug 정보 확장
# =====================================================================

import datetime

class MacroSchedulerV28_7:
    def __init__(self, cfg):
        self.cfg = cfg

        # 시장별 multiplier (필수 적용)
        self.market_mult_map = cfg.get("market_mult", {
            "KR": 1.0,
            "US": 1.0,
            "CRYPTO": 1.0
        })

        # crypto thresholds 외부화
        self.crypto_thr = cfg.get("crypto", {}).get("thresholds", {
            "spike_news_vol": 1.0,       # vol_ratio < 1.0 (저변동)
            "spike_news_volume": 2.0,    # volume_ratio > 2.0 (거래량 급증)
            "fake_pump_vol": 2.0,        # 고변동
            "fake_pump_volume": 0.8,     # 거래량 감소
            "quiet_vol": 0.7
        })

        # freeze 조건값
        fz = cfg.get("freeze_rules", {})
        self.dd_limit = fz.get("dd_limit", 0.15)
        self.vol_spike_ratio = fz.get("vol_spike_ratio", 3.0)

        # boost 조건값
        br = cfg.get("boost_rules", {})
        self.sharpe_min = br.get("sharpe_min", 1.2)

        # funding reversal 조건
        self.funding_change_min = cfg.get("crypto", {}).get("funding_change_min", 0.005)

        # clamp
        self.lr_clamp = cfg.get("lr_clamp", (0.1, 3.0))

    # ---------------------------------------------------------
    # 유틸: 반환 구조 통일
    # ---------------------------------------------------------
    def _pack(self, session, halt, events, freeze_mult, boost_mult, market_mult, final_mult, debug):
        return {
            "session": session,
            "halt_trading": halt,
            "events": events,
            "freeze_mult": freeze_mult,
            "boost_mult": boost_mult,
            "market_mult": market_mult,
            "final_mult": final_mult,
            "debug": debug
        }

    # ---------------------------------------------------------
    # STOCK 세션 판별
    # ---------------------------------------------------------
    def detect_stock_session(self, market, now_time):
        sessions = self.cfg.get("markets", {}).get(market, {}).get("sessions", {})
        if not sessions:
            return "normal", True, {"reason": "no_session_defined"}

        for name, (start, end) in sessions.items():
            if start <= now_time <= end:
                return name, False, {}

        return "normal", False, {"reason": "no_match"}

    # ---------------------------------------------------------
    # CRYPTO 세션 판별
    # ---------------------------------------------------------
    def detect_crypto_session(self, ctx):
        vol = ctx.get("volatility")
        avg_vol = ctx.get("avg_volatility")
        volume = ctx.get("volume")
        avg_volume = ctx.get("avg_volume")
        funding = ctx.get("funding_rate")
        avg_funding = ctx.get("avg_funding_rate")

        # fallback 체크
        if avg_vol is None or avg_vol == 0 or avg_volume is None or avg_volume == 0:
            return "normal", True, {"fallback_reason": "missing_avg_values"}

        # ratio 계산
        vol_ratio = vol / max(avg_vol, 1e-9)
        volume_ratio = volume / max(avg_volume, 1e-9)

        dbg = {
            "vol_ratio": vol_ratio,
            "volume_ratio": volume_ratio,
            "funding": funding,
            "avg_funding": avg_funding
        }

        # ----------------------------
        # 1) spike-news (저변동 + 고거래량)
        # ----------------------------
        if vol_ratio < self.crypto_thr["spike_news_vol"] and volume_ratio > self.crypto_thr["spike_news_volume"]:
            return "spike-news", False, {**dbg, "selected": "spike-news"}

        # ----------------------------
        # 2) fake-pump (고변동 + 거래량 감소)
        # ----------------------------
        if vol_ratio > self.crypto_thr["fake_pump_vol"] and volume_ratio < self.crypto_thr["fake_pump_volume"]:
            return "fake-pump", False, {**dbg, "selected": "fake-pump"}

        # ----------------------------
        # 3) funding reversal (방향 + magnitude)
        # ----------------------------
        if (funding is not None and avg_funding is not None):
            if funding * avg_funding < 0 and abs(funding - avg_funding) > self.funding_change_min:
                return "reversal-window", False, {**dbg, "selected": "funding-reversal"}

        # ----------------------------
        # 4) quiet zone
        # ----------------------------
        if vol_ratio < self.crypto_thr["quiet_vol"]:
            return "quiet", False, {**dbg, "selected": "quiet"}

        # ----------------------------
        # 5) active (기본)
        # ----------------------------
        return "active", False, {**dbg, "selected": "active"}

    # ---------------------------------------------------------
    # 종합 multiplier 계산
    # ---------------------------------------------------------
    def get_macro_multiplier(self, market, ctx):
        now_time = ctx.get("time", datetime.datetime.utcnow().time())

        # ---------------------------------------------
        # SESSION DETECT
        # ---------------------------------------------
        if market in ("KR", "US"):
            session, fallback, dbg_session = self.detect_stock_session(market, now_time)
        else:
            session, fallback, dbg_session = self.detect_crypto_session(ctx)

        events = []
        freeze_mult = 1.0
        boost_mult = 1.0
        halt_trading = False

        # fallback 발생 시 즉시 거래 중단
        if fallback:
            halt_trading = True
            session = "normal"
            debug_final = {
                "reason": "fallback_detected",
                "session_dbg": dbg_session
            }
            return self._pack(
                session, True, ["halt_fallback"],
                freeze_mult, boost_mult,
                self.market_mult_map.get(market,1.0), 1.0, debug_final
            )

        # ---------------------------------------------
        # 핵심 지표 누락 시 halt
        # ---------------------------------------------
        dd = ctx.get("drawdown")
        sharpe = ctx.get("sharpe")
        vol_ratio = ctx.get("vol_ratio")

        if dd is None or sharpe is None:
            halt_trading = True
            return self._pack(
                session, True, ["halt_missing_data"],
                freeze_mult, boost_mult,
                self.market_mult_map.get(market,1.0), 1.0,
                {"reason": "missing_dd_or_sharpe", "session_dbg": dbg_session}
            )

        # ---------------------------------------------
        # FREEZE LOGIC
        # ---------------------------------------------
        if dd > self.dd_limit:
            freeze_mult *= 0.5
            events.append("freeze_dd")

        if vol_ratio is not None and vol_ratio > self.vol_spike_ratio:
            freeze_mult *= 0.7
            events.append("freeze_vol")

        # ---------------------------------------------
        # BOOST LOGIC
        # ---------------------------------------------
        if sharpe > self.sharpe_min:
            boost_mult *= 1.2
            events.append("boost_sharpe")

        if session in ("open", "spike-news"):
            boost_mult *= 1.1
            events.append("boost_session")

        # ---------------------------------------------
        # FINAL MULTIPLIER (시장별 적용)
        # ---------------------------------------------
        market_mult = self.market_mult_map.get(market, 1.0)
        raw_mult = market_mult * freeze_mult * boost_mult

        # clamp
        lr_min, lr_max = self.lr_clamp
        final_mult = max(lr_min, min(raw_mult, lr_max))

        debug_final = {
            "session": session,
            "freeze_mult": freeze_mult,
            "boost_mult": boost_mult,
            "market_mult": market_mult,
            "raw_mult": raw_mult,
            "clamped_mult": final_mult,
            "session_dbg": dbg_session
        }

        return self._pack(
            session, halt_trading, events,
            freeze_mult, boost_mult,
            market_mult, final_mult,
            debug_final
        )
