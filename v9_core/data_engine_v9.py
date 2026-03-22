# ======================================================================
#  data_engine_v9.py
#  V9 PLUS 데이터 수집 엔진 (한국/미국 공통)
# ======================================================================

import datetime
import random
from typing import Dict, Any


class DataCollectorV9:
    """
    한국/미국 자동매매 공통 데이터 수집 엔진.
    실제 HTS/API 연동 부분은 run_korea_v9_plus / run_us_v9_plus 내부에서 브로커가 처리함.
    여기서는 시세 변동/체결속도/OBV 등 가벼운 계산을 포함한 구조 제공.
    """

    def __init__(self, market: str = "KR"):
        self.market = market.upper()
        self.last_price_cache = {}

    # ---------------------------------------------------------------
    #  기본 틱 수집(실전용 브로커가 이 함수에 데이터를 공급)
    # ---------------------------------------------------------------
    def collect(self, symbol: str, tick: Dict[str, Any]) -> Dict[str, Any]:
        """
        run_korea_v9_plus 또는 run_us_v9_plus에서 브로커가 전달한 tick dict을 표준화함.
        tick 예시:
            {
                "price": 12345,
                "volume": 10000,
                "bid": 12340,
                "ask": 12350,
                "timestamp": datetime.datetime.now()
            }
        """

        if not tick:
            return {}

        price = tick.get("price", 0)
        volume = tick.get("volume", 0)

        # 이전 가격 대비 변화율 계산
        prev_price = self.last_price_cache.get(symbol, price)
        change_rate = (price - prev_price) / prev_price if prev_price else 0
        self.last_price_cache[symbol] = price

        normalized = {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "bid": tick.get("bid", price - 1),
            "ask": tick.get("ask", price + 1),
            "change_rate": change_rate,
            "timestamp": tick.get("timestamp", datetime.datetime.now()),
        }

        return normalized

    # ---------------------------------------------------------------
    #  샘플 데이터 발생기 (모의 테스트용)
    # ---------------------------------------------------------------
    def mock_tick(self, symbol: str) -> Dict[str, Any]:
        """모의 테스트용 더미 시세 생성 (실제 거래에서는 사용 안 함)."""

        price = random.randint(10000, 50000)
        return {
            "symbol": symbol,
            "price": price,
            "volume": random.randint(1000, 50000),
            "bid": price - random.randint(1, 5),
            "ask": price + random.randint(1, 5),
            "timestamp": datetime.datetime.now(),
        }
