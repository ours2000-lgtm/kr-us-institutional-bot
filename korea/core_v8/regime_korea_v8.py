# =============================================================
# regime_korea_v8.py — 한국장 Market Regime Engine (V8)
# -------------------------------------------------------------
# 특징:
#   • 코스피/코스닥 동시 감지
#   • 변동성 기반 6종 레짐
#   • 지수포착/삼각형 패턴 반영 가능한 구조
# =============================================================

class MarketRegimeKoreaV8:
    def __init__(self, logger=None):
        self.logger = logger
        
        self.last_regime = "NEUTRAL"

        if logger:
            logger.info("[INIT] MarketRegimeKoreaV8 Loaded")

    def update(self, kospi_tick, kosdaq_tick):
        # 단순 계산 (V8에서 후에 강화)
        p1 = kospi_tick["price"]
        p2 = kosdaq_tick["price"]

        vol1 = kospi_tick["volume"]
        vol2 = kosdaq_tick["volume"]

        if p1 > 2600 and vol1 > 800000:
            self.last_regime = "BULL"
        elif p1 < 2500:
            self.last_regime = "BEAR"
        else:
            self.last_regime = "NEUTRAL"

    def get_regime(self):
        return self.last_regime
