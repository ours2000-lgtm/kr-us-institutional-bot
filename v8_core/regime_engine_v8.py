# ======================================================================
# regime_engine_v8.py — 시장 레짐 엔진 (강세/약세/변동성)
# ======================================================================

from utils_v8 import safe_log

class RegimeEngineV8:

    def __init__(self):
        self.state = "NEUTRAL"
        safe_log("[RegimeEngine V8] 초기화 완료")

    # ------------------------------------------------------------------
    # 시장 레짐 업데이트
    # ------------------------------------------------------------------
    def update(self, tick):
        if not tick:
            return

        price = tick.get("price", 0)
        vol = tick.get("volume", 0)

        if price == 0:
            self.state = "NEUTRAL"
            return

        # 강세장 판단
        if vol > 150000 and tick.get("trend_5m", 0) > 0.6:
            self.state = "BULL"
        # 약세장 판단
        elif tick.get("trend_5m", 0) < 0:
            self.state = "BEAR"
        else:
            self.state = "NEUTRAL"

    def get_regime(self):
        return self.state
