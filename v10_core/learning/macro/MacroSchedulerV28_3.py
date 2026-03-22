# ================================================================
# MacroScheduler V28.3
#  - 주식/암호화폐 시장 공통 매크로 제어 스케줄러
#  - market_mult + session_mult + freeze/boost 통합
#  - 이벤트 로그, 세션 누락 방어, Crypto 확장 기반
# ================================================================

import datetime
import numpy as np


class MacroSchedulerV28_3:
    """
    Macro-level learning rate control:
      - Market session detection
      - Crypto 24h session classification
      - Freeze / Boost combined logic
      - market_mult × session_mult × freeze × boost
      - Deep debugging support
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg or {}

        # Market multipliers
        self.market_mult = self.cfg.get("market_mult", {
            "KR": 1.0,
            "US": 1.0,
            "CRYPTO": 1.0,
        })

        # Session multipliers
        self.session_mult = self.cfg.get("session_mult", {
            "open": 1.0,
            "close": 1.0,
            "mid": 1.0,
            "quiet": 1.0,
            "active": 1.0,
        })

        # Freeze/Boost multipliers
        self.freeze_thresholds = self.cfg.get("freeze_thresholds", {
            "max_dd": 0.12,
            "vol_spike": 0.04
        })
        self.freeze_values = self.cfg.get("freeze_values", {
            "dd": 0.5,
            "vol": 0.7,
        })

        self.boost_values = self.cfg.get("boost_values", {
            "morning_momentum": 1.15,
            "trend_day": 1.10,
        })

        # Minimum freeze value (avoid LR collapse)
        self.min_freeze_mult = self.cfg.get("min_freeze_mult", 0.15)

        # Debug level
        self.debug_level = self.cfg.get("debug_level", "basic").lower()

        # Market time setup
        self.market_sessions = self.cfg.get("market_sessions", {
            "KR": {
                "open": "09:00-10:00",
                "mid": "10:00-14:20",
                "close": "14:20-15:20"
            },
            "US": {
                "open": "22:30-23:30",
                "mid": "23:30-05:00",
                "close": "05:00-06:00"
            }
        })

    # ---------------------------------------------------------
    # 시간 문자열 → datetime.time 변환
    # ---------------------------------------------------------
    def _to_time(self, s):
        if s is None:
            return None
        try:
            h, m = s.split(":")
            return datetime.time(int(h), int(m))
        except:
            return None

    # ---------------------------------------------------------
    # 시간대 판별 (자정 넘김 처리 지원)
    # ---------------------------------------------------------
    def _in_session(self, now: datetime.time, session_str: str):
        if not session_str or "-" not in session_str:
            return False

        start_s, end_s = session_str.split("-")
        start = self._to_time(start_s)
        end = self._to_time(end_s)

        if not start or not end:
            return False

        # 24시간 세션 지원
        if start == end:
            return True

        # Normal case: same day interval
        if start <= end:
            return start <= now <= end

        # Cross-midnight case
        return now >= start or now <= end

    # ---------------------------------------------------------
    # 주식 시장 세션 판정
    # ---------------------------------------------------------
    def _get_stock_session(self, market: str, now: datetime.time):
        sessions = self.market_sessions.get(market.upper(), {})
        for name, rng in sessions.items():
            if self._in_session(now, rng):
                return name
        return "mid"  # fallback

    # ---------------------------------------------------------
    # Crypto 세션 판정 (vol + volume 기반)
    # ---------------------------------------------------------
    def _get_crypto_session(self, vol: float, volume: float,
                            avg_vol: float, avg_volume: float):
        if avg_vol <= 0 or avg_volume <= 0:
            return "active"

        # 상대적 변화율 반영
        vol_ratio = vol / avg_vol
        volm_ratio = volume / avg_volume

        if vol_ratio > 3.0 or volm_ratio > 3.0:
            return "spike"  # big news / fake pump candidate

        if vol_ratio < 0.5 and volm_ratio < 0.5:
            return "quiet"

        return "active"

    # ---------------------------------------------------------
    # Freeze 로직
    # ---------------------------------------------------------
    def _compute_freeze(self, max_dd, vol):
        freeze_mult = 1.0
        events = []

        if max_dd >= self.freeze_thresholds.get("max_dd", 0.12):
            freeze_mult *= self.freeze_values.get("dd", 0.5)
            events.append("freeze_dd")

        if vol >= self.freeze_thresholds.get("vol_spike", 0.04):
            freeze_mult *= self.freeze_values.get("vol", 0.7)
            events.append("freeze_vol")

        # 하한선 적용
        freeze_mult = max(freeze_mult, self.min_freeze_mult)
        return freeze_mult, events

    # ---------------------------------------------------------
    # Boost 로직
    # ---------------------------------------------------------
    def _compute_boost(self, sharpe, trend_signal: bool):
        boost_mult = 1.0
        events = []

        if trend_signal:
            boost_mult *= self.boost_values.get("trend_day", 1.10)
            events.append("boost_trend")

        if sharpe and sharpe > 1.5:
            boost_mult *= self.boost_values.get("morning_momentum", 1.15)
            events.append("boost_momentum")

        return boost_mult, events

    # ---------------------------------------------------------
    # 최종 multiplier 계산
    # ---------------------------------------------------------
    def get_macro_multiplier(self,
                             market: str,
                             now: datetime.time,
                             vol=None,
                             volume=None,
                             avg_vol=None,
                             avg_volume=None,
                             sharpe=None,
                             max_dd=None,
                             trend_signal=False):
        dbg = {}

        market = (market or "DEFAULT").upper()
        now = now or datetime.datetime.now().time()

        # 시장 기반 multiplier
        m_mult = self.market_mult.get(market, 1.0)

        # 세션 판별
        if market == "CRYPTO":
            session = self._get_crypto_session(vol or 0, volume or 0,
                                               avg_vol or 1, avg_volume or 1)
        else:
            session = self._get_stock_session(market, now)

        s_mult = self.session_mult.get(session, 1.0)

        # Freeze
        freeze_mult, freeze_events = self._compute_freeze(max_dd or 0, vol or 0)

        # Boost (freeze가 있으면 자동 차단)
        boost_mult, boost_events = self._compute_boost(sharpe, trend_signal)
        if freeze_events:
            boost_mult = 1.0
            boost_events = []

        raw_final_mult = m_mult * s_mult * freeze_mult * boost_mult
        clamped_mult = max(0.05, min(raw_final_mult, 5.0))

        if self.debug_level != "off":
            dbg = {
                "market": market,
                "session": session,
                "market_mult": m_mult,
                "session_mult": s_mult,
                "freeze_mult": freeze_mult,
                "boost_mult": boost_mult,
                "freeze_events": freeze_events,
                "boost_events": boost_events,
                "raw_final_mult": raw_final_mult,
                "clamped_mult": clamped_mult,
            }

        return clamped_mult, dbg
