# =============================================================
#  data_us_v7_plus.py — 미국 데이터 엔진 (V7 PLUS 완성본)
# -------------------------------------------------------------
#  특징:
#    • Alpaca LIVE/PAPER 지원 (REST 기반)
#    • 인증 실패 시 자동 MOCK 전환
#    • BigTech / ETF / Leveraged ETF / MidCap 모듈화
#    • VIX / DXY / NQ Futures / SPY / QQQ 수집
#    • 시세·호가·VWAP·거래량·유동성 구성
# =============================================================

import os
import random
import requests
from datetime import datetime

try:
    import alpaca_trade_api as tradeapi
    ALPACA_LOADED = True
except:
    ALPACA_LOADED = False


class USDataCollectorV7Plus:
    def __init__(self, logger=None, mode="PAPER", universe=None):
        self.logger = logger
        self.mode = mode.upper()

        # Universe (Config에서 받아옴)
        self.universe = universe or [
            "AAPL", "MSFT", "NVDA", "AMZN", "META",
            "TSLA", "AMD", "QQQ", "TQQQ", "SQQQ",
            "SOXL", "SOXS", "RIVN", "UPST"
        ]

        # Macro + Index
        self.idx_list = ["SPY", "QQQ"]
        self.bigtech = ["AAPL", "MSFT", "NVDA"]

        # Alpaca API 준비
        self.key = os.getenv("ALPACA_API_KEY", "")
        self.secret = os.getenv("ALPACA_SECRET_KEY", "")

        self.base_url = (
            "https://api.alpaca.markets" if self.mode == "LIVE"
            else "https://paper-api.alpaca.markets"
        )

        self.api = None

        if self.logger:
            logger.info(f"[INIT] USDataCollectorV7Plus (mode={self.mode})")

        self._init_alpaca()

    # ==========================================================
    # Alpaca 초기화
    # ==========================================================
    def _init_alpaca(self):
        if self.mode == "MOCK":
            if self.logger:
                self.logger.warning("[INFO] MOCK 모드로 실행")
            return

        if not ALPACA_LOADED:
            if self.logger:
                self.logger.error("[ERROR] alpaca_trade_api 미설치 → MOCK 강제")
            self.mode = "MOCK"
            return

        if not self.key or not self.secret:
            if self.logger:
                self.logger.error("[ERROR] Alpaca APIKEY 누락 → MOCK 모드 전환")
            self.mode = "MOCK"
            return

        try:
            self.api = tradeapi.REST(self.key, self.secret, self.base_url)
            acc = self.api.get_account()

            if self.logger:
                self.logger.info(f"[API] Alpaca 인증 성공: {acc.status}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"[API] Alpaca 인증 실패: {e}")
            self.mode = "MOCK"

    # ==========================================================
    # MOCK 데이터 생성
    # ==========================================================
    def _mock_tick(self, s):
        price = random.uniform(5, 700)
        volume = random.randint(8000, 400000)
        p = round(price, 2)

        return {
            "symbol": s,
            "price": p,
            "volume": volume,
            "bid": p - random.uniform(0.01, 0.12),
            "ask": p + random.uniform(0.01, 0.12),
            "bid_size": random.randint(20, 500),
            "ask_size": random.randint(20, 500),
            "vwap": p * random.uniform(0.995, 1.005),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }

    # ==========================================================
    # Alpaca 실시간 데이터 (REST)
    # ==========================================================
    def _alpaca_tick(self, s):
        try:
            bar = self.api.get_latest_bar(s)
            quote = self.api.get_latest_quote(s)

            return {
                "symbol": s,
                "price": float(bar.c),
                "volume": int(bar.v),
                "bid": float(quote.bp),
                "ask": float(quote.ap),
                "bid_size": int(quote.bs),
                "ask_size": int(quote.as_),
                "vwap": float(bar.vw) if bar.vw else float(bar.c),
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }

        except Exception:
            return None

    # ==========================================================
    # Macro 데이터: VIX, DXY
    # ==========================================================
    def _get_macro(self):
        try:
            vix = requests.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
            ).json()["chart"]["result"][0]["meta"]["regularMarketPrice"]

            dxy = requests.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/%5EDXY"
            ).json()["chart"]["result"][0]["meta"]["regularMarketPrice"]

        except:
            vix = random.uniform(12, 28)
            dxy = random.uniform(98, 106)

        return vix, dxy

    # ==========================================================
    # NASDAQ 선물 (NQ)
    # ==========================================================
    def _get_nq(self):
        try:
            r = requests.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/NQ%3DF"
            ).json()
            return r["chart"]["result"][0]["meta"]["regularMarketPrice"]
        except:
            return random.uniform(15000, 18500)

    # ==========================================================
    # SPY / QQQ
    # ==========================================================
    def _get_index(self, s):
        if self.mode == "MOCK":
            return self._mock_tick(s)

        t = self._alpaca_tick(s)
        if t is None:
            return self._mock_tick(s)
        return t

    # ==========================================================
    # 메인 데이터 수집
    # ==========================================================
    def collect(self):
        data = {}

        # 1) 일반 종목
        for s in self.universe:
            if self.mode == "MOCK":
                tick = self._mock_tick(s)
            else:
                tick = self._alpaca_tick(s)
                if tick is None:
                    tick = self._mock_tick(s)
            data[s] = tick

        # 2) BigTech / Index
        for idx in self.idx_list:
            data[idx] = self._get_index(idx)

        # 3) Macro
        vix, dxy = self._get_macro()
        data["MACRO_VIX"] = vix
        data["MACRO_DXY"] = dxy

        # 4) NASDAQ Futures
        data["NQ"] = self._get_nq()

        return data
