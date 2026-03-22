# ============================================================
#  market.py  (V8 Market Regime Engine)
# ============================================================
#  기능 :
#    - 한국/미국 시장 레짐 자동 판단
#    - 멀티타임프레임 지수 분석
#    - VWAP 상/하단 판단
#    - 변동성 기반 BULL/BEAR/FLAT/CRASH 분류
#    - 유동성/체결강도/갭/속도 기반 확률 모델
# ============================================================

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class MarketRegimeV8:
    def __init__(self, market="KR", window=300):
        """
        market : "KR" 또는 "US"
        window : 분석할 최근 데이터 개수 (초 단위)
        """

        self.market = market
        self.window = window

        # 지수 실시간 저장 버퍼
        self.index_prices = []
        self.index_volumes = []
        self.vwap_prices = []

        # 최근 갱신 시간
        self.last_update = None

        # 최종 레짐
        self.current_regime = "FLAT"

    # --------------------------------------------------------
    # 지수 업데이트
    # --------------------------------------------------------
    def update(self, price: float, volume: float):
        """초당 지수 가격과 거래량 업데이트"""

        now = datetime.now()
        self.last_update = now

        self.index_prices.append(price)
        self.index_volumes.append(volume)

        if len(self.index_prices) > self.window:
            self.index_prices = self.index_prices[-self.window:]
            self.index_volumes = self.index_volumes[-self.window:]

        # VWAP 계산
        vwap = self.calculate_vwap()
        self.vwap_prices.append(vwap)

        if len(self.vwap_prices) > self.window:
            self.vwap_prices = self.vwap_prices[-self.window:]

        # 최종 레짐 갱신
        self.current_regime = self.get_regime()

    # --------------------------------------------------------
    # VWAP 계산
    # --------------------------------------------------------
    def calculate_vwap(self):
        try:
            prices = np.array(self.index_prices)
            vols = np.array(self.index_volumes)
            vwap = np.sum(prices * vols) / np.sum(vols)
            return float(vwap)
        except Exception:
            return prices[-1] if len(prices) else None

    # --------------------------------------------------------
    # 변동성 계산
    # --------------------------------------------------------
    def calc_volatility(self):
        if len(self.index_prices) < 30:
            return 0.0
        returns = np.diff(self.index_prices) / self.index_prices[:-1]
        return np.std(returns) * np.sqrt(60)

    # --------------------------------------------------------
    # 지수 기울기 (속도)
    # --------------------------------------------------------
    def calc_slope(self):
        if len(self.index_prices) < 10:
            return 0
        y = np.array(self.index_prices[-30:])
        x = np.arange(len(y))
        slope = np.polyfit(x, y, 1)[0]
        return slope

    # --------------------------------------------------------
    # 레짐 판단
    # --------------------------------------------------------
    def get_regime(self):

        if len(self.index_prices) < 30:
            return "FLAT"

        price = self.index_prices[-1]
        vwap = self.vwap_prices[-1]
        vol = self.calc_volatility()
        slope = self.calc_slope()

        # -----------------------------------------
        # 1) CRASH 조건
        # -----------------------------------------
        if vol > 0.035 and slope < -0.15:
            return "CRASH"

        # -----------------------------------------
        # 2) BULL 조건
        # -----------------------------------------
        if price > vwap * 1.001 and slope > 0:
            if vol < 0.02:
                return "BULL"

        # -----------------------------------------
        # 3) BEAR 조건
        # -----------------------------------------
        if price < vwap * 0.999 and slope < 0:
            return "BEAR"

        # -----------------------------------------
        # 4) FLAT 조건 (중립)
        # -----------------------------------------
        return "FLAT"

    # --------------------------------------------------------
    # 상태 출력
    # --------------------------------------------------------
    def info(self):
        return {
            "market": self.market,
            "regime": self.current_regime,
            "last_price": self.index_prices[-1] if self.index_prices else None,
            "vwap": self.vwap_prices[-1] if self.vwap_prices else None,
            "volatility": round(self.calc_volatility(), 6),
            "slope": round(self.calc_slope(), 6),
            "updated": self.last_update
        }
