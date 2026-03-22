"""
market_structure_v9.py
V9 PLUS + V10 구조 기반 Market Structure Engine

역할:
- ORB 구조 분석
- AVWAP (Anchor VWAP) 계산
- 변동성 구조(Vol Clustering)
- 추세 구조(MTF Trend Approx)
- 매수/매도 압력 탐지(Orderflow-independent structural pressure)
- 구조적 지지/저항 레벨 계산

출력 형태:
{
    "symbol": ...,
    "price": ...,
    "trend": {"short":..., "mid":..., "long":...},
    "orb": {"high":..., "low":..., "broken_up":..., "broken_down":...},
    "avwap": float,
    "vol_cluster": float,
    "pressure": {"buy":..., "sell":..., "bias":...},
    "timestamp": ...
}
"""

from datetime import datetime
import numpy as np

from utils_v9 import safe_log


class MarketStructureV9:
    """
    Market Structure Engine V9 (with V10 structural upgrades)
    """

    def __init__(self, market="KR"):
        self.market = market

        # ORB 저장소
        self.orb_high = {}
        self.orb_low = {}
        self.orb_ready = {}

        # AVWAP 저장소
        self.avwap_sum = {}
        self.avwap_volume = {}

        # 최근 n틱 저장 (변동성 군집)
        self.price_window = {}

        # 기본 설정
        self.window_size = 60        # 변동성 구조 계산용 (최근 60틱)
        self.orb_minutes = 30        # ORB 기간 (09:00~09:30 등)

    # --------------------------------------------------------------
    # ORB(Opening Range Breakout)
    # --------------------------------------------------------------
    def update_orb(self, symbol, tick):
        ts = datetime.now().time()
        price = tick["price"]

        # ORB 초기 설정
        if symbol not in self.orb_high:
            self.orb_high[symbol] = price
            self.orb_low[symbol] = price
            self.orb_ready[symbol] = False

        # ORB 기간 체크
        if ts.hour == 9 and ts.minute < self.orb_minutes:
            # 오프닝 레인지 업데이트
            self.orb_high[symbol] = max(self.orb_high[symbol], price)
            self.orb_low[symbol] = min(self.orb_low[symbol], price)
        else:
            self.orb_ready[symbol] = True

        # 브레이크 여부
        broken_up = False
        broken_down = False

        if self.orb_ready[symbol]:
            if price > self.orb_high[symbol]:
                broken_up = True
            elif price < self.orb_low[symbol]:
                broken_down = True

        return {
            "high": self.orb_high[symbol],
            "low": self.orb_low[symbol],
            "broken_up": broken_up,
            "broken_down": broken_down
        }

    # --------------------------------------------------------------
    # AVWAP 계산
    # --------------------------------------------------------------
    def update_avwap(self, symbol, tick):
        price = tick["price"]
        volume = tick.get("volume", 1)

        if symbol not in self.avwap_sum:
            self.avwap_sum[symbol] = 0.0
            self.avwap_volume[symbol] = 0.0

        self.avwap_sum[symbol] += price * volume
        self.avwap_volume[symbol] += volume

        if self.avwap_volume[symbol] == 0:
            return price

        return self.avwap_sum[symbol] / self.avwap_volume[symbol]

    # --------------------------------------------------------------
    # 변동성 구조 분석 (V10의 핵심 개념 중 하나)
    # --------------------------------------------------------------
    def update_vol_cluster(self, symbol, price):
        if symbol not in self.price_window:
            self.price_window[symbol] = []

        window = self.price_window[symbol]
        window.append(price)

        # window 유지
        if len(window) > self.window_size:
            window.pop(0)

        if len(window) < 5:
            return 0.0

        # 변동성(표준편차)
        vol = np.std(window)

        # normalized volatility cluster index
        return float(vol)

    # --------------------------------------------------------------
    # 구조적 매수/매도 압력 (orderflow에 독립적)
    # --------------------------------------------------------------
    def structural_pressure(self, symbol, tick, avwap):
        price = tick["price"]

        # AVWAP 대비 가격 위치
        bias = price - avwap

        # 가격이 AVWAP 위에서 오래 유지될수록 매수 우위
        buy_p = 1.0 if price > avwap else 0.0
        sell_p = 1.0 if price < avwap else 0.0

        return {
            "buy": buy_p,
            "sell": sell_p,
            "bias": bias
        }

    # --------------------------------------------------------------
    # 추세 구조 MTF approximation (단순화된 형태)
    # --------------------------------------------------------------
    def mtf_trend(self, symbol, price):
        window = self.price_window.get(symbol, [])

        if len(window) < 10:
            return {"short": 0, "mid": 0, "long": 0}

        short = price - np.mean(window[-10:])
        mid = price - np.mean(window[-30:]) if len(window) >= 30 else 0
        long = price - np.mean(window[-60:]) if len(window) >= 60 else 0

        return {
            "short": float(short),
            "mid": float(mid),
            "long": float(long)
        }

    # --------------------------------------------------------------
    # 메인 분석 (Signal Engine, MetaEngine 등에서 직접 호출)
    # --------------------------------------------------------------
    def analyze(self, symbol, tick):
        price = tick["price"]

        # 업데이트
        orb_info = self.update_orb(symbol, tick)
        avwap = self.update_avwap(symbol, tick)
        vol_cluster = self.update_vol_cluster(symbol, price)
        pressure = self.structural_pressure(symbol, tick, avwap)
        trend = self.mtf_trend(symbol, price)

        result = {
            "symbol": symbol,
            "price": price,
            "trend": trend,
            "orb": orb_info,
            "avwap": avwap,
            "vol_cluster": vol_cluster,
            "pressure": pressure,
            "timestamp": datetime.now()
        }

        return result
