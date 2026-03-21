# =============================================================
#  data_us_v7_plus.py — 미국 시장 실시간 데이터 수집 엔진 (V7 PLUS)
# =============================================================

import os
import time
import random
from datetime import datetime
import requests

class USDataCollectorV7Plus:
    """
    미국 시장 실시간 데이터 수집 엔진
    - mode="LIVE"  : Alpaca LIVE 계좌
    - mode="PAPER" : Alpaca PAPER 계좌
    - mode="SIM"   : 내부 시뮬레이션 데이터
    - mode="REPLAY": 과거 로그 기반 재생
    """

    def __init__(self, logger=None, mode="PAPER", replay_file=None):
        self.logger = logger
        self.mode = mode.upper()

        # Alpaca API 키 읽기
        self.api_key = os.getenv("ALPACA_API_KEY", "")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY", "")

        # 엔드포인트
        self.base_url = (
            "https://api.alpaca.markets" if self.mode == "LIVE"
            else "https://paper-api.alpaca.markets"
        )

        # 시뮬레이션 상태
        self.sim_price = {}
        self.sim_symbols = ["AAPL", "MSFT", "NVDA", "TSLA", "AMD"]

        # REPLAY 파일
        self.replay_file = replay_file
        self.replay_fp = None
        if replay_file and os.path.exists(replay_file):
            self.replay_fp = open(replay_file, "r", encoding="utf-8")

        if logger:
            logger.info(f"[INIT] USDataCollectorV7Plus (mode={self.mode}) 준비완료")

    # ---------------------------------------------------------
    # Alpaca REST API 요청
    # ---------------------------------------------------------
    def _alpaca_get(self, endpoint):
        url = f"{self.base_url}{endpoint}"
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        }
        try:
            r = requests.get(url, headers=headers, timeout=1.5)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None

    # ---------------------------------------------------------
    # LIVE / PAPER 데이터 수집
    # ---------------------------------------------------------
    def _collect_from_alpaca(self):
        market_data = {}

        quotes = self._alpaca_get("/v2/stocks/quotes/latest?symbols=AAPL,MSFT,NVDA,TSLA,AMD")

        if not quotes:
            return None

        for symbol in ["AAPL", "MSFT", "NVDA", "TSLA", "AMD"]:
            q = quotes.get(symbol)
            if not q:
                continue

            price = q.get("bp", 0)
            volume = q.get("bv", 0)

            market_data[symbol] = {
                "price": float(price),
                "volume": int(volume),
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }

        return market_data

    # ---------------------------------------------------------
    # SIM 모드 — 랜덤 가격 생성
    # ---------------------------------------------------------
    def _collect_sim(self):
        market_data = {}

        for code in self.sim_symbols:
            if code not in self.sim_price:
                self.sim_price[code] = random.uniform(100, 400)

            # 가격 랜덤 변동
            self.sim_price[code] *= random.uniform(0.995, 1.005)

            market_data[code] = {
                "price": round(self.sim_price[code], 2),
                "volume": random.randint(1000, 5000),
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }

        return market_data

    # ---------------------------------------------------------
    # REPLAY 모드 — 파일에서 한 라인씩 읽기
    # ---------------------------------------------------------
    def _collect_replay(self):
        if not self.replay_fp:
            return None

        line = self.replay_fp.readline()
        if not line:
            return None

        try:
            symbol, price, volume = line.strip().split(",")
            market_data = {
                symbol: {
                    "price": float(price),
                    "volume": int(volume),
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                }
            }
            return market_data
        except:
            return None

    # ---------------------------------------------------------
    # 메인 수집 함수
    # ---------------------------------------------------------
    def collect(self):
        if self.mode in ["LIVE", "PAPER"]:
            return self._collect_from_alpaca()

        if self.mode == "SIM":
            return self._collect_sim()

        if self.mode == "REPLAY":
            return self._collect_replay()

        return None
