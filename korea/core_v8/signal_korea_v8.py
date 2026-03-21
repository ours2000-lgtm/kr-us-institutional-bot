# =============================================================
# signal_korea_v8.py — 한국 시그널 엔진 (V8)
# -------------------------------------------------------------
# 전략들:
#   • 초기 변동성(09:00~10:00) 패턴
#   • 지수포착 + 삼각형 전략
#   • VWAP Break / 거래대금 폭발
#   • ML Quality Gate (추가 슬롯)
# =============================================================

from datetime import datetime

class KoreaSignalMasterV8:
    def __init__(self, logger=None):
        self.logger = logger

        if logger:
            logger.info("[INIT] KoreaSignalMasterV8 Loaded")

    def generate(self, market, regime, index_strength):
        results = []
        now = datetime.now().time()

        for code, t in market.items():
            price = t["price"]
            vol = t["volume"]

            score = 0

            # 1) 초반 변동성 (09:00~10:00)
            if 9 <= now.hour < 10 and vol > 100000:
                score += 1.5

            # 2) 지수포착 영향
            if index_strength > 0:
                score += 1.2

            # 3) 거래량 기반
            if vol > 200000:
                score += 1.0

            if score >= 2.2:
                results.append({
                    "symbol": code,
                    "score": round(score, 2),
                    "tp": 2.5,
                    "sl": -1.2,
                })

        return results
