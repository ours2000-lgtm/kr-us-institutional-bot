# =============================================================
# data_us_v6_plus.py — 미국 데이터 엔진 (V6 PLUS 안정판)
# -------------------------------------------------------------
# • Alpaca PAPER/LIVE 자동 인식
# • 키 누락 시 MOCK 자동 전환
# • SPY/QQQ/NQ/VIX/DXY 포함
# • 빅테크 및 일반종목 데이터 수집
# =============================================================

import random
import os
import requests
from datetime import datetime
import numpy as np

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except:
    ALPACA_AVAILABLE = False


class USDataCollectorV6Plus:
    def __init__(self, logger=None, mode="AUTO"):
        self.logger = logger
        self.mode = mode.upper()
        self.api = None

        self.key = os.getenv("ALPACA_API_KEY", "")
        self.secret = os.getenv("ALPACA_SECRET_KEY", "")
        self.base_url = "https://paper-api.alpaca.markets"

        if "LIVE" in self.mode:
            self.base_url = "https://api.alpaca.markets"

        # universe(빅테크 + ETF + 변동성)
        self.universe = [
            "AAPL","NVDA","MSFT","AMZN","META","AMD","TSLA",
            "SPY","QQQ",
            "SOXL","SOXS","TQQQ","SQQQ",
        ]

        if self.logger:
            self.logger.info(f"[INIT] USDataCollectorV6Plus (mode={self.mode})")

        self._init_alpaca()

    # ---------------------------------------------------------
    # Alpaca 초기화
    # ---------------------------------------------------------
    def _init_alpaca(self):
        if self.mode == "MOCK":
            return

        if not ALPACA_AVAILABLE or not self.key or not self.secret:
            if self.logger:
                self.logger.warning("[WARN] Alpaca 미사용 → MOCK 모드로 전환")
            self.mode = "MOCK"
            return

        try:
            self.api = tradeapi.REST(
                self.key, self.secret, self.base_url
            )
            acc = self.api.get_account()
            if self.logger:
                self.logger.info(f"[INFO] Alpaca 연결 성공 ({acc.status})")

        except Exception as e:
            if self.logger:
                self.logger.error(f"[ERROR] Alpaca 인증 실패 → MOCK: {e}")
            self.mode = "MOCK"

    # ---------------------------------------------------------
    # MOCK TICK
    # ---------------------------------------------------------
    def _mock_tick(self, symbol):
        price = random.uniform(10, 500)
        volume = random.randint(10000, 500000)

        return {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "vwap": price * random.uniform(0.995, 1.005),
            "bid": price - 0.02,
            "ask": price + 0.02,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

    # ---------------------------------------------------------
    # Alpaca tick
    # ---------------------------------------------------------
    def _alpaca_tick(self, symbol):
        try:
            bar = self.api.get_latest_bar(symbol)
            quote = self.api.get_latest_quote(symbol)

            return {
                "symbol": symbol,
                "price": float(bar.c),
                "volume": int(bar.v),
                "vwap": float(bar.vw) if bar.vw else float(bar.c),
                "bid": float(quote.bp),
                "ask": float(quote.ap),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
        except:
            return None

    # ---------------------------------------------------------
    # 외부 macro: VIX, DXY
    # ---------------------------------------------------------
    def _macro(self):
        try:
            vix = requests.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
            ).json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
        except:
            vix = random.uniform(13, 30)

        try:
            dxy = requests.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/%5EDXY"
            ).json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
        except:
            dxy = random.uniform(98, 106)

        return {"VIX": vix, "DXY": dxy}

    # ---------------------------------------------------------
    # NQ 선물
    # ---------------------------------------------------------
    def _nq_fut(self):
        try:
            data = requests.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/NQ%3DF"
            ).json()
            return data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        except:
            return random.uniform(15000, 18500)

    # ---------------------------------------------------------
    # 메인 수집
    # ---------------------------------------------------------
    def collect(self):
        data = {}

        for s in self.universe:
            if self.mode == "MOCK":
                tick = self._mock_tick(s)
            else:
                tick = self._alpaca_tick(s)
                if tick is None:
                    tick = self._mock_tick(s)

            data[s] = tick

        macro = self._macro()
        data["MACRO_VIX"] = macro["VIX"]
        data["MACRO_DXY"] = macro["DXY"]
        data["NQ"] = self._nq_fut()

        return data
