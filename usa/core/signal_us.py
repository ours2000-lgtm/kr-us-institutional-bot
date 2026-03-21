# ===============================================================
#  signal_us.py — 미국시장 신호 엔진 (V4: Pre/Regular/After)
# ===============================================================

from typing import Dict, Optional


class USSignalEngine:
    """
    미국 신호 엔진 (V4)
    - 프리마켓: 갭업/갭다운 감지, 강한 거래대금 증가
    - 정규장: 오픈모멘텀 + 눌림목 + 스캘핑 신호
    - 애프터: 변동성 축소 구간만 선택적 대응
    """

    def __init__(self, logger):
        self.logger = logger
        self.logger.info("[INIT] USSignalEngine 초기화 완료")

    # ----------------------------------------------------------
    # 프리마켓 신호 (17:00 ~ 23:30)
    # ----------------------------------------------------------
    def _pre_market_signal(self, symbol_data):
        price = symbol_data["price"]
        ret = symbol_data["return"]
        volume = symbol_data["volume"]

        # 강한 갭업 / 갭다운 기준
        if ret >= 3.0 and volume > 120_000:
            return {"action": "BUY", "reason": "PRE_GAP_UP"}

        if ret <= -3.0 and volume > 100_000:
            return {"action": "SELL", "reason": "PRE_GAP_DOWN"}

        return None

    # ----------------------------------------------------------
    # 정규장 신호 (23:30 ~ 06:00)
    # ----------------------------------------------------------
    def _regular_signal(self, symbol_data):
        price = symbol_data["price"]
        ret = symbol_data["return"]
        volume = symbol_data["volume"]

        # KR_OPEN10 스타일 + 미국형 변동성 조정
        if ret > 1.8 and volume > 150_000:
            return {"action": "BUY", "reason": "US_OPEN_MOMENTUM"}

        # 스캘핑: 초단타 반등 구간
        if -1.0 < ret < 0.5 and volume > 200_000:
            return {"action": "BUY", "reason": "US_SCALP_PULLBACK"}

        # 변동성 급락 → 청산 신호
        if ret < -2.8:
            return {"action": "SELL", "reason": "US_VOLATILITY_DROP"}

        return None

    # ----------------------------------------------------------
    # 애프터(After-hours) 신호 (06:00 ~ 08:00)
    # ----------------------------------------------------------
    def _after_market_signal(self, symbol_data):
        price = symbol_data["price"]
        ret = symbol_data["return"]
        volume = symbol_data["volume"]

        # 애프터는 변동성 낮기 때문에 보수적
        if 0.8 < ret < 2.0 and volume > 50_000:
            return {"action": "BUY", "reason": "AFTER_STEADY_TREND"}

        if ret <= -2.0:
            return {"action": "SELL", "reason": "AFTER_DROP"}

        return None

    # ----------------------------------------------------------
    # 메인 신호 계산
    # ----------------------------------------------------------
    def compute(self, market_data: Dict) -> Optional[Dict]:
        if market_data is None:
            return None

        session = market_data["session"]
        symbols = market_data["data"]

        results = {}

        for sym, sdata in symbols.items():
            if session == "PRE":
                sig = self._pre_market_signal(sdata)
            elif session == "REGULAR":
                sig = self._regular_signal(sdata)
            elif session == "AFTER":
                sig = self._after_market_signal(sdata)
            else:
                sig = None

            if sig:
                results[sym] = sig

        if results:
            self.logger.info("[SIGNAL] 감지된 신호: %s", results)

        return results if results else None
