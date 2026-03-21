# =============================================================
# data_korea_v6_plus.py — 한국 주식 실시간 데이터 엔진 (V6 PLUS)
# -------------------------------------------------------------
# 기능:
#   • 실시간 체결가/호가/체결강도
#   • 거래대금 급증, 변동성 증가 탐지
#   • 1초/3초/30초 모멘텀 계산
#   • 코스피/코스닥 지수 포함
# =============================================================

import random
from datetime import datetime

class DataKoreaV6Plus:
    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()

        self.universe = [
            "005930", "000660", "035420",
            "068270", "051910", "035720",
            "207940", "373220", "066570",
            "005935"
        ]

        if logger:
            logger.info(f"[INIT] DataKoreaV6Plus (mode={self.mode}) 초기화 완료")

    def _mock_tick(self, code):
        price = random.uniform(50000, 350000)
        volume = random.randint(10000, 500000)
        bid = price - random.uniform(10, 50)
        ask = price + random.uniform(10, 50)

        return {
            "code": code,
            "price": price,
            "volume": volume,
            "bid": bid,
            "ask": ask,
            "strength": random.uniform(20, 250),
            "vwap": price * random.uniform(0.99, 1.01),
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

    def collect(self):
        """MOCK: 실시간 데이터 수집 시뮬레이션"""
        data = {}

        for code in self.universe:
            tick = self._mock_tick(code)
            data[code] = tick

        # 시장 지표 추가
        data["KOSPI"] = random.uniform(-1.5, 1.5)
        data["KOSDAQ"] = random.uniform(-2.0, 2.0)

        return data
