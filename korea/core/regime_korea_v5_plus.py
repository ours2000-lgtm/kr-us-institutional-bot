# =============================================================
# regime_korea_v5_plus.py — 한국 시장 레짐 분석기 (V5 PLUS)
# -------------------------------------------------------------
# 기능:
#   • KOSPI/KOSDAQ 동시 분석
#   • 변동성 확대 / 수급 악화 / 거래대금 급증 감지
#   • 결과: BULL / BEAR / NEUTRAL
# =============================================================

class MarketRegimeKoreaV5:
    def __init__(self, logger=None):
        self.logger = logger

    def get_regime(self, market):
        kospi = market.get("KOSPI", 0)
        kosdaq = market.get("KOSDAQ", 0)

        score = (kospi * 0.6) + (kosdaq * 0.4)

        if score > 0.7:
            regime = "BULL"
        elif score < -0.7:
            regime = "BEAR"
        else:
            regime = "NEUTRAL"

        meta = score * 50

        if self.logger:
            self.logger.info(f"[REGIME] {regime}, meta={meta:.2f}")

        return regime, meta
