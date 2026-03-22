# ============================================================
# MarketSessionDetector V29
# - KR/US 주식 세션 판별
# - Crypto 변동성/거래량 기반 세션 판별
# - 자정 넘김 세션 처리 포함
# - 세션 누락 시 fallback = "mid" or "normal"
# ============================================================

import datetime

class MarketSessionDetectorV29:
    def __init__(self, cfg):
        """
        cfg 예시:
        cfg["markets"]["KR"]["sessions"] = {
            "open":  ["09:00", "10:00"],
            "mid":   ["10:00", "14:20"],
            "close": ["14:20", "15:20"]
        }
        cfg["crypto"] = { "vol_factor_spike": 2.0, "vol_factor_quiet": 0.5 }
        """
        self.cfg = cfg

    # ------------------------------
    # 시간 문자열을 datetime.time으로 변환
    # ------------------------------
    def _to_time(self, t_str):
        if t_str is None:
            return None
        return datetime.datetime.strptime(t_str, "%H:%M").time()

    # ------------------------------
    # 현재 시간이 세션 범위 안에 있는지 확인
    # 자정 넘김(start > end)도 처리
    # ------------------------------
    def _in_session(self, now_t, start_t, end_t):
        if start_t is None or end_t is None:
            return False
        
        # 정상 세션 (예: 09:00 ~ 15:20)
        if start_t <= end_t:
            return start_t <= now_t <= end_t
        
        # 자정 넘어가는 세션 (예: 23:30 ~ 05:00)
        return now_t >= start_t or now_t <= end_t

    # ------------------------------
    # KR / US 주식 시장 세션 판별
    # ------------------------------
    def _get_stock_session(self, market, now_t):
        sessions = self.cfg["markets"][market]["sessions"]

        for session_name, (start, end) in sessions.items():
            st = self._to_time(start)
            et = self._to_time(end)
            if self._in_session(now_t, st, et):
                return session_name
        
        # fallback
        return "mid"

    # ------------------------------
    # Crypto 전용 세션 판별
    # vol + volume + funding_rate 기반
    # ------------------------------
    def _get_crypto_session(self, vol, avg_vol, volume, avg_volume, funding_rate):
        if avg_vol is None or avg_vol == 0:
            return "normal"

        # 상대적 비율 계산
        vol_ratio = vol / (avg_vol + 1e-9)
        vol_up = vol_ratio > self.cfg["crypto"]["vol_factor_spike"]
        vol_down = vol_ratio < self.cfg["crypto"]["vol_factor_quiet"]

        vol_spike = vol_up
        vol_quiet = vol_down

        vol_based = None
        if vol_spike:
            vol_based = "spike"
        elif vol_quiet:
            vol_based = "quiet"
        else:
            vol_based = "active"

        # 뉴스 기반 spike
        if volume > avg_volume * 2 and vol_ratio < 1.0:
            return "spike-news"

        # fake-pump: 변동성만 높고 거래량 부족
        if vol_ratio > 2.0 and volume < avg_volume * 0.7:
            return "fake-pump"

        # funding_rate 급변 = reversal window
        if funding_rate is not None and abs(funding_rate) > self.cfg["crypto"].get("funding_rate_limit", 0.02):
            return "reversal-window"

        return vol_based

    # ------------------------------
    # 외부 호출 API
    # ------------------------------
    def detect(self, market, timestamp, price=None, volume=None, vol=None,
               avg_volume=None, avg_vol=None, funding_rate=None):
        
        now_t = timestamp.time()

        # 주식 시장
        if market in ("KR", "US"):
            session = self._get_stock_session(market, now_t)
            regime = session
            return {
                "market": market,
                "session": session,
                "regime": regime
            }

        # Crypto 시장
        if market == "CRYPTO":
            session = self._get_crypto_session(vol, avg_vol, volume, avg_volume, funding_rate)
            return {
                "market": market,
                "session": session,
                "regime": session
            }

        # 예외
        return {
            "market": market,
            "session": "unknown",
            "regime": "unknown"
        }
