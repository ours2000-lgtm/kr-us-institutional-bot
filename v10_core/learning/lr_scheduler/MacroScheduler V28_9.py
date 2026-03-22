# ======================================================================
# MacroScheduler V28.9
#  - Market baseline multiplier 복원
#  - Freeze 발생 시 boost 감산
#  - Session-based boost 복원 (open, spike-news 등)
#  - fallback 시 session='normal', halt_trading=True 통일
#  - Crypto/Stock 모두 안정화
# ======================================================================

from datetime import datetime, time


class MacroSchedulerV28_9:

    def __init__(self, cfg):
        self.cfg = cfg

        # 시장별 baseline multiplier
        self.market_mult_map = cfg.get("market_mult", {
            "KR": 1.0,
            "US": 1.0,
            "CRYPTO": 1.0
        })

        # 시장별 clamp
        self.clamp_map = {
            "KR": tuple(cfg.get("lr_clamp_kr", (0.3, 2.0))),
            "US": tuple(cfg.get("lr_clamp_us", (0.2, 2.0))),
            "CRYPTO": tuple(cfg.get("lr_clamp_crypto", (0.1, 3.0))),
        }

        # Boost & Freeze 규칙
        self.boost_rules = cfg.get("boost_rules", {
            "sharpe_min": 1.5,
            "sessions": ["open", "spike-news"]
        })
        self.freeze_rules = cfg.get("freeze_rules", {
            "dd_limit": 0.15,
            "vol_spike_ratio": 3.0
        })

        # Quiet/FakePump/News thresholds
        self.crypto_thr = cfg.get("crypto", {}).get("thresholds", {
            "spike_news_vol": 1.0,
            "spike_news_volume": 2.0,
            "fake_pump_vol": 2.0,
            "fake_pump_volume": 0.8,
            "quiet_vol": 0.9
        })

    # ------------------------------------------------------------------
    # 내부 유틸: time 변환
    # ------------------------------------------------------------------
    def _to_time(self, t):
        if isinstance(t, time):
            return t
        if isinstance(t, str):
            hh, mm = t.split(":")
            return time(int(hh), int(mm))
        return None

    # ------------------------------------------------------------------
    # 자정 넘김 세션 지원
    # ------------------------------------------------------------------
    def _in_session(self, now, start, end):
        if start is None or end is None:
            return False
        if start == end:
            # 24시간 세션 선언은 정상 처리
            return True
        if start < end:
            return start <= now <= end
        else:
            # 자정 넘김
            return now >= start or now <= end

    # ==================================================================
    # Stock 세션 판별
    # ==================================================================
    def detect_stock_session(self, market, now_time):
        sessions = (
            self.cfg.get("markets", {})
            .get(market.upper(), {})
            .get("sessions", {})
        )

        if not sessions:
            return ("normal", True, {"reason": "missing_sessions"})

        for name, sess in sessions.items():
            start = self._to_time(sess.get("start"))
            end = self._to_time(sess.get("end"))
            if self._in_session(now_time, start, end):
                return (name, False, {"session": name})

        return ("normal", True, {"reason": "no_matching_session"})

    # ==================================================================
    # Crypto 세션 판별
    # ==================================================================
    def detect_crypto_session(self, ctx):
        vol = ctx.get("volatility")
        avg_vol = ctx.get("avg_volatility")
        volume = ctx.get("volume")
        avg_volume = ctx.get("avg_volume")
        funding = ctx.get("funding_rate")
        avg_funding = ctx.get("avg_funding_rate")

        # 데이터 누락 -> safe fallback
        if vol is None or avg_vol is None or avg_vol == 0 or volume is None or avg_volume is None or avg_volume == 0:
            return ("normal", True, {"reason": "insufficient_data"})

        thr = self.crypto_thr

        vol_ratio = vol / max(avg_vol, 1e-9)
        volume_ratio = volume / max(avg_volume, 1e-9)

        dbg = {
            "vol_ratio": vol_ratio,
            "volume_ratio": volume_ratio,
            "funding": funding,
            "avg_funding": avg_funding,
        }

        # --------------------------------------------------------------
        # 우선순위 1: spike-news (저변동 + 고거래량)
        # --------------------------------------------------------------
        if vol_ratio < thr["spike_news_vol"] and volume_ratio > thr["spike_news_volume"]:
            return ("spike-news", False, {**dbg, "trigger": "spike_news"})

        # --------------------------------------------------------------
        # 우선순위 2: fake-pump (고변동 + 거래량 감소)
        # --------------------------------------------------------------
        if vol_ratio > thr["fake_pump_vol"] and volume_ratio < thr["fake_pump_volume"]:
            return ("fake-pump", False, {**dbg, "trigger": "fake_pump"})

        # --------------------------------------------------------------
        # 우선순위 3: funding reversal
        # funding 방향 반대 + 최소 magnitude
        # --------------------------------------------------------------
        if (
            funding is not None
            and avg_funding is not None
            and funding * avg_funding < 0
            and abs(funding - avg_funding) > 0.005
        ):
            return ("reversal-window", False, {**dbg, "trigger": "funding_reversal"})

        # --------------------------------------------------------------
        # Quiet zone
        # --------------------------------------------------------------
        if vol_ratio < thr["quiet_vol"]:
            return ("quiet", False, {**dbg, "trigger": "quiet"})

        return ("active", False, {**dbg, "trigger": "active"})

    # ==================================================================
    # Public: Crypto/Stock 통합 세션 판별
    # ==================================================================
    def detect_session(self, market, now_time, ctx):
        market = market.upper()

        if market in ("KR", "US"):
            return self.detect_stock_session(market, now_time)

        if market == "CRYPTO":
            return self.detect_crypto_session(ctx)

        return ("normal", True, {"reason": "unknown_market"})

    # ==================================================================
    # Freeze/Boost 계산 + 시장별 baseline multiplier
    # ==================================================================
    def get_macro_multiplier(self, market, session_name, ctx, trend_signal=None):

        # clamp 범위
        lr_min, lr_max = self.clamp_map.get(market.upper(), (0.1, 3.0))

        # 시장 baseline
        market_mult = self.market_mult_map.get(market.upper(), 1.0)

        dd = ctx.get("dd")
        vol_ratio = ctx.get("vol_ratio") or (
            ctx.get("volatility", 0) / max(ctx.get("avg_volatility", 1e-9), 1e-9)
        )
        sharpe = ctx.get("sharpe")

        # 핵심 데이터 누락 → 즉시 halt
        if dd is None or vol_ratio is None or sharpe is None:
            return self._pack(
                multiplier=lr_min,
                session="normal",
                events=["halt_missing_data"],
                halt=True,
            )

        freeze_mult = 1.0
        boost_mult = 1.0
        events = []

        # --------------------------------------------------------------
        # Freeze Rules
        # --------------------------------------------------------------
        if dd > self.freeze_rules.get("dd_limit", 0.15):
            freeze_mult *= 0.5
            events.append("freeze_dd")

        if vol_ratio > self.freeze_rules.get("vol_spike_ratio", 3.0):
            freeze_mult *= 0.7
            events.append("freeze_vol")

        # --------------------------------------------------------------
        # Boost Rules
        # --------------------------------------------------------------
        if sharpe > self.boost_rules.get("sharpe_min", 1.5):
            boost_mult *= 1.2
            events.append("boost_sharpe")

        if session_name in self.boost_rules.get("sessions", []):
            boost_mult *= 1.1
            events.append("boost_session")

        # --------------------------------------------------------------
        # Trend signal 반영
        # --------------------------------------------------------------
        if trend_signal == "up":
            boost_mult *= 1.1
            events.append("boost_trend")
        elif trend_signal == "down":
            freeze_mult *= 0.9
            events.append("freeze_trend")

        # --------------------------------------------------------------
        # Freeze → Boost 감산
        # --------------------------------------------------------------
        if freeze_mult < 1.0:
            boost_mult *= 0.8
            events.append("boost_reduced_by_freeze")

        # --------------------------------------------------------------
        # 최종 multiplier 계산
        # --------------------------------------------------------------
        raw_mult = market_mult * freeze_mult * boost_mult

        # clamp
        final_mult = max(lr_min, min(raw_mult, lr_max))

        # clamp 이벤트
        if final_mult == lr_min:
            events.append("clamp_min_hit")
        elif final_mult == lr_max:
            events.append("clamp_max_hit")

        return self._pack(
            multiplier=final_mult,
            session=session_name,
            events=events,
            halt=False,
            debug={
                "raw_mult": raw_mult,
                "freeze_mult": freeze_mult,
                "boost_mult": boost_mult,
                "market_mult": market_mult,
            }
        )

    # ------------------------------------------------------------------
    # pack統一 출력
    # ------------------------------------------------------------------
    def _pack(self, multiplier, session, events=None, halt=False, debug=None):
        return {
            "multiplier": multiplier,
            "session": session,
            "events": events or [],
            "halt_trading": halt,
            "timestamp": datetime.utcnow().isoformat(),
            "debug": debug or {},
        }
