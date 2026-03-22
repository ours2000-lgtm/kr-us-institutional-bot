# ======================================================================
# orderflow_v8.py — V8 PLUS Orderflow Engine (체결 / 압력 / 유동성)
# ======================================================================
# 기능:
#   ✔ Spread (bid-ask 차이)
#   ✔ Liquidity Void (유동성 공백)
#   ✔ Speed of Tape (체결 속도)
#   ✔ Imbalance (매수/매도 체결 비율)
#   ✔ Quality Score 산출
# ======================================================================

import time
from utils_v8 import safe_log


class OrderflowV8:
    def __init__(self, config):
        self.cfg = config["ORDERFLOW"]
        self.last_price = {}
        self.last_time = {}

        safe_log("[Orderflow V8] 초기화 완료")

    # ------------------------------------------------------------------
    # Spread 계산
    # ------------------------------------------------------------------
    def compute_spread(self, tick):
        bid = tick.get("bid", 0)
        ask = tick.get("ask", 0)

        if ask <= 0:
            return 0

        return (ask - bid) / ask

    # ------------------------------------------------------------------
    # Speed of Tape (체결 속도: price/time 변화율)
    # ------------------------------------------------------------------
    def compute_speed(self, symbol, price):
        now = time.time()

        # 초기값
        if symbol not in self.last_price:
            self.last_price[symbol] = price
            self.last_time[symbol] = now
            return 0

        dt = now - self.last_time[symbol]
        if dt <= 0:
            return 0

        dp = price - self.last_price[symbol]

        speed = dp / dt

        # 업데이트
        self.last_price[symbol] = price
        self.last_time[symbol] = now

        return speed

    # ------------------------------------------------------------------
    # Imbalance (매수/매도 체결 비율)
    # ------------------------------------------------------------------
    def compute_imbalance(self, tick):
        buy = tick.get("buy_volume", 0)
        sell = tick.get("sell_volume", 0)

        total = buy + sell
        if total == 0:
            return 0.5

        return buy / total

    # ------------------------------------------------------------------
    # 메인 오더플로우 분석 함수
    # ------------------------------------------------------------------
    def analyze(self, symbol, tick):
        price = tick.get("price", 0)
        volume = tick.get("volume", 0)

        spread = self.compute_spread(tick)
        speed = self.compute_speed(symbol, price)
        imbalance = self.compute_imbalance(tick)

        liquidity_void = (volume < 20000)

        # Quality Score 구성 (기관급 간단 모델)
        quality = 0

        # 스프레드 적정
        if spread <= self.cfg["spread_limit"]:
            quality += 1

        # 속도 증가
        if abs(speed) >= self.cfg["speed_threshold"]:
            quality += 1

        # imbalance (매수 우위)
        if imbalance >= self.cfg["imbalance_threshold"]:
            quality += 1

        # Liquidity Void는 감점
        if liquidity_void and self.cfg["forbid_liquidity_void"]:
            quality -= 1

        flow = {
            "spread": spread,
            "speed": speed,
            "imbalance": imbalance,
            "liquidity_void": liquidity_void,
            "orderflow_score": quality,
            "quality": quality,   # SignalEngine과 호환성 위해
        }

        return flow
