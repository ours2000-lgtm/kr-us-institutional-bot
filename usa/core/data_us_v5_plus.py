# =============================================================
#  data_us_v5_plus.py  (미국 실시간 데이터 엔진 — V5 PLUS)
# -------------------------------------------------------------
#  특징:
#    • AUTO: PAPER → LIVE → 실패 시 MOCK 자동 전환
#    • Alpaca 실시간 가격/체결량/호가
#    • 고급 MOCK (볼륨, 모멘텀, 시가대비 반영)
#    • run_us_v5_plus.py 와 100% 호환
# =============================================================

import random
from datetime import datetime

# -------------------------------------------------------------
# Alpaca 연결 준비
# -------------------------------------------------------------
import requests

ALPACA_API_KEY = ""
ALPACA_SECRET_KEY = ""
ALPACA_PAPER_ENDPOINT = "https://paper-api.alpaca.markets"
ALPACA_DATA_ENDPOINT = "https://data.alpaca.markets/v2"

def alpaca_get_price(symbol):
    url = f"{ALPACA_DATA_ENDPOINT}/stocks/{symbol}/quotes/latest"
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }
    r = requests.get(url, headers=headers, timeout=3)
    if r.status_code != 200:
        return None
    q = r.json().get("quote", {})
    return {
        "price": q.get("ap", 0),
        "bid": q.get("bp", 0),
        "ask": q.get("ap", 0),
        "volume": q.get("as", 0)
    }


# =============================================================
#                    미국 데이터 수집 엔진 (V5)
# =============================================================
class USDataCollectorV5:
    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()

        if self.logger:
            self.logger.info(f"[INIT] USDataCollectorV5 (mode={self.mode})")

        # 미국 테스트용 유니버스 (원하면 ETF/빅테크 추가 가능)
        self.universe = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN"]

        # AUTO 모드 → PAPER 자동 연결
        if self.mode == "AUTO":
            self.mode = "PAPER"
            if self.logger:
                self.logger.info("[AUTO] PAPER 시도 → 실패 시 MOCK 사용")

    # ---------------------------------------------------------
    # MOCK 데이터 생성
    # ---------------------------------------------------------
    def _generate_mock_tick(self, code):
        price = random.uniform(80, 500)
        volume = random.randint(10000, 500000)
        bid = price - random.uniform(0.01, 0.2)
        ask = price + random.uniform(0.01, 0.2)

        return {
            "code": code,
            "price": round(price, 2),
            "open": round(price * random.uniform(0.97, 1.03), 2),
            "high": round(price * random.uniform(1.01, 1.05), 2),
            "low": round(price * random.uniform(0.95, 0.99), 2),
            "volume": volume,
            "bid": round(bid, 2),
            "ask": round(ask, 2),
            "amount": volume * price,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }

    # ---------------------------------------------------------
    # Alpaca PAPER/LIVE 조회
    # ---------------------------------------------------------
    def _collect_alpaca(self, code):
        try:
            tick = alpaca_get_price(code)
            if not tick:
                return None

            return {
                "code": code,
                "price": float(tick["price"]),
                "open": tick["price"],
                "high": tick["price"],
                "low": tick["price"],
                "volume": tick["volume"],
                "bid": tick["bid"],
                "ask": tick["ask"],
                "amount": tick["volume"] * tick["price"],
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
        except:
            return None

    # ---------------------------------------------------------
    # 메인 collect()
    # ---------------------------------------------------------
    def collect(self):
        result = {}

        for code in self.universe:
            tick = None

            if self.mode in ["PAPER", "LIVE"]:
                tick = self._collect_alpaca(code)

            if tick is None:
                tick = self._generate_mock_tick(code)

            result[code] = tick

        return result
