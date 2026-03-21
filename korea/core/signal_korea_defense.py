# =============================================================
#  signal_korea_defense.py (V5)
#  - 안정형 / 하락장 대응 / 과매도 반등 / 리스크 최소화
# =============================================================

class KoreaSignalDefenseV5:
    """방어형 — 변동성 높은 장 / 약세장 전용 필터"""

    def __init__(self, logger, params):
        self.logger = logger
        self.params = params

        if logger:
            logger.info("[INIT] KoreaSignalDefense V5 (방어형) 초기화 완료")

    def generate(self, market):
        signals = []

        for code, tick in market.items():
            price = tick["price"]
            volume = tick["volume"]

            # 거래대금 기반 저위험 필터
            if volume < self.params["def_min_volume"]:
                continue

            # 시가 30분 단순 상승 조건
            if price < tick["open"] * 1.005:
                continue

            # 수급 안정
            if tick["buy_vol"] < tick["sell_vol"]:
                continue

            score = 0
            score += volume / 50000
            if price > tick["open"] * 1.01:
                score += 1.2

            if score >= self.params["def_threshold"]:
                signals.append({
                    "code": code,
                    "score": score,
                    "type": "BUY",
                    "mode": "DEFENSE"
                })

        return sorted(signals, key=lambda x: x["score"], reverse=True)
