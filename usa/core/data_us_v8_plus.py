# =====================================================================
# data_us_v8_plus.py — 미국 실시간 데이터 엔진 (V8 PLUS)
# =====================================================================

import os
import time
import random
import requests
from datetime import datetime

class USDataV8Plus:
    """
    미국 시장 데이터 엔진 (V8)
    - SIM  : 내부 시뮬레이션
    - PAPER: Alpaca 모의계좌
    - LIVE : Alpaca 실계좌
    - 모든 전략에서 필요한 필드를 정규화된 구조로 반환
    """

    def __init__(self, logger=None, mode="PAPER"):
        self.logger = logger
        self.mode = mode.upper()

        # Alpaca API 키
        self.api_key = os.getenv("ALPACA_API_KEY", "")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY", "")

        # Alpaca endpoint
        self.base_url = (
            "https://api.alpaca.markets"
            if self.mode == "LIVE"
            else "https://paper-api.alpaca.markets"
        )

        # SIM을 위한 기초 가격
        self.sim_prices = {
            "AAPL": 170,
            "MSFT": 330,
            "NVDA": 490,
            "AMZN": 145,
            "META": 350,
            "QQQ": 380,
            "NQ": 17800,
            "MACRO_VIX": 13.0,
            "MACRO_DXY": 103.0,
        }

        if self.logger:
            self.logger.info(f"[INIT] USDataV8Plus (mode={self.mode}) 준비완료")

    # ===============================================================
    # Alpaca REST API 통신
    # ===============================================================
    def _alpaca_get(self, endpoint):
        url = f"{self.base_url}{endpoint}"
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
        }
        try:
            r = requests.get(url, headers=headers, timeout=1.5)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None

    # ===============================================================
    # PAPER / LIVE 데이터 수집
    # ===============================================================
    def _collect_alpaca(self):
        symbols = "AAPL,MSFT,NVDA,AMZN,META,QQQ"
        result = self._alpaca_get(f"/v2/stocks/quotes/latest?symbols={symbols}")
        if not result:
            return None

        data = {}

        for code in ["AAPL", "MSFT", "NVDA", "AMZN", "META", "QQQ"]:
            q = result.get(code)
            if not q:
                continue

            price = q.get("bp", 0)
            volume = q.get("bv", 0)
            data[code] = {
                "price": float(price),
                "volume": int(volume),
                "vwap": float(price),
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }

        # NQ, VIX, DXY는 외부 데이터 모듈에서 확장 가능 (임시값)
        data["NQ"] = data["QQQ"]["price"] * 47.0
        data["MACRO_VIX"] = random.uniform(12.5, 15.0)
        data["MACRO_DXY"] = random.uniform(102.5, 103.5)

        return data

    # ===============================================================
    # SIM 모드 (내부 랜덤 시뮬레이션)
    # ===============================================================
    def _collect_sim(self):
        data = {}

        for code in self.sim_prices.keys():
            # 가격 랜덤 변동 (0.2~0.5% 범위)
            base = self.sim_prices[code]
            base *= random.uniform(0.997, 1.003)
            self.sim_prices[code] = base

            data[code] = {
                "price": round(base, 2),
                "volume": random.randint(2000, 8000),
                "vwap": round(base * random.uniform(0.998, 1.002), 2),
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }

        return data

    # ===============================================================
    # 메인 collect()
    # ===============================================================
    def collect(self):
        if self.mode in ["LIVE", "PAPER"]:
            return self._collect_alpaca()

        if self.mode == "SIM":
            return self._collect_sim()

        return None
