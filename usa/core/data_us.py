# =============================================================
# data_us.py (V2 — Alpaca + MOCK 실시간 데이터 수집 엔진)
# -------------------------------------------------------------
# · Alpaca 실계좌 / 모의계좌 자동 전환
# · 미국장 특성(유동성 변동, 프리/애프터 영향) 반영
# · run_us.py 에서 USDataCollectorV2 로 호출
# =============================================================

import random
import datetime
from datetime import datetime

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except Exception:
    ALPACA_AVAILABLE = False


class USDataCollectorV2:
    def __init__(self, logger=None, mode="MOCK", key="", secret="", endpoint=""):
        self.logger = logger
        self.mode = mode.upper()   # MOCK / LIVE

        if self.logger:
            self.logger.info(f"[INIT] USDataCollectorV2 (mode={self.mode})")

        self.api = None
        if self.mode == "LIVE" and ALPACA_AVAILABLE:
            try:
                self.api = tradeapi.REST(key, secret, endpoint)
                if self.logger:
                    self.logger.info("[INFO] Alpaca LIVE 연결 성공")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[ERROR] Alpaca 연결 실패: {e}")
                self.mode = "MOCK"

        # 기본 유니버스
        self.universe = ["AAPL", "TSLA", "NVDA", "AMZN", "META", "MSFT"]

    # ---------------------------------------------------------
    # MOCK Tick
    # ---------------------------------------------------------
    def _mock_tick(self, code):
        price = random.uniform(20, 450)
        volume = random.randint(50000, 2000000)

        return {
            "code": code,
            "price": round(price, 2),
            "volume": volume,
            "bid_size": random.randint(100, 5000),
            "ask_size": random.randint(100, 5000),
            "vwap": round(price * random.uniform(0.995, 1.005), 2),
            "sector_strength": random.uniform(-2, 2),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }

    # ---------------------------------------------------------
    # LIVE Tick
    # ---------------------------------------------------------
    def _live_tick(self, code):
        try:
            quote = self.api.get_latest_quote(code)
            bar = self.api.get_latest_bar(code)

            return {
                "code": code,
                "price": float(bar.c),
                "volume": int(bar.v),
                "bid_size": int(quote.bid_size),
                "ask_size": int(quote.ask_size),
                "vwap": float(bar.vw),
                "sector_strength": 0,  # 추후 확장
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
        except:
            return None

    # ---------------------------------------------------------
    # Main Collect
    # ---------------------------------------------------------
    def collect(self):
        market = {}

        for code in self.universe:
            if self.mode == "MOCK":
                t = self._mock_tick(code)
            else:
                t = self._live_tick(code)

            if t:
                market[code] = t

        return market


class USDataCollector(USDataCollectorV2):
    pass
