# =============================================================
# data_us_plus.py (V2 — Alpaca + MOCK 실시간 데이터 엔진)
# =============================================================

import random
from datetime import datetime

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except:
    ALPACA_AVAILABLE = False


class USDataCollectorV2:
    def __init__(self, logger=None, mode="MOCK", key="", secret="", endpoint=""):
        self.logger = logger
        self.mode = mode.upper()

        if logger:
            logger.info(f"[INIT] USDataCollectorV2 (mode={self.mode})")

        self.api = None
        if self.mode == "LIVE" and ALPACA_AVAILABLE:
            try:
                self.api = tradeapi.REST(key, secret, endpoint)
                logger.info("[LIVE] Alpaca 연결 성공")
            except Exception as e:
                logger.error(f"[ERROR] Alpaca 연결 실패: {e}")
                self.mode = "MOCK"

        self.universe = ["AAPL", "TSLA", "AMZN", "NVDA", "META", "MSFT"]

    # MOCK Tick
    def _mock_tick(self, code):
        price = random.uniform(30, 600)
        vol   = random.randint(100000, 3000000)
        
        return {
            "code": code,
            "price": round(price, 2),
            "volume": vol,
            "bid_size": random.randint(50, 3000),
            "ask_size": random.randint(50, 3000),
            "vwap": round(price * random.uniform(0.995, 1.005), 2),
            "sector_strength": random.uniform(-2, 2),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }

    # LIVE Tick
    def _live_tick(self, code):
        try:
            q = self.api.get_latest_quote(code)
            b = self.api.get_latest_bar(code)

            return {
                "code": code,
                "price": float(b.c),
                "volume": int(b.v),
                "bid_size": int(q.bid_size),
                "ask_size": int(q.ask_size),
                "vwap": float(b.vw),
                "sector_strength": 0,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
        except:
            return None

    # Collect
    def collect(self):
        out = {}
        for code in self.universe:
            if self.mode == "MOCK":
                t = self._mock_tick(code)
            else:
                t = self._live_tick(code)
            if t:
                out[code] = t
        return out
