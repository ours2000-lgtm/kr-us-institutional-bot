# ======================================================================
# orderflow_v9.py — V9 PLUS Orderflow Engine
# ======================================================================
# 기능:
#   ✔ 체결강도(틱 속도)
#   ✔ 매수·매도 불균형(imbalance)
#   ✔ 스프레드 이상 감지
#   ✔ 유동성 공백(Liquidity Void) 감지
#   ✔ 대량 체결 Spike
#   ✔ 종합 Orderflow Score 산출
# ======================================================================

import numpy as np
from datetime import datetime
from utils_v8 import safe_log


class OrderflowV9:

    def __init__(self):
        self.last_tick_time = {}
        self.speed_history = {}
        self.max_history = 100

        safe_log("[Orderflow V9] 엔진 초기화 완료")

    # ------------------------------------------------------------------
    # 유동성 공백(Liquidity Void) 판단
    # ------------------------------------------------------------------
    def detect_liquidity_void(self, bid_size, ask_size):
        # 호가 잔량이 거의 없으면 위험
        if bid_size < 300 or ask_size < 300:
            return True
        return False

    # ------------------------------------------------------------------
    # 스프레드 감지
    # ------------------------------------------------------------------
    def calc_spread(self, bid, ask):
        if bid <= 0 or ask <= 0:
            return 1.0
        return (ask - bid) / bid

    # ------------------------------------------------------------------
    # 체결 속도(Tick Speed)
    # ------------------------------------------------------------------
    def calc_speed(self, symbol):
        now = datetime.now().timestamp()

        if symbol not in self.last_tick_time:
            self.last_tick_time[symbol] = now
            return 0.0

        diff = now - self.last_tick_time[symbol]
        self.last_tick_time[symbol] = now

        if diff <= 0:
            return 0.0

        speed = 1.0 / diff  # ticks per second

        # 기록
        if symbol not in self.speed_history:
            self.speed_history[symbol] = []

        self.speed_history[symbol].append(speed)

        if len(self.speed_history[symbol]) > self.max_history:
            self.speed_history[symbol].pop(0)

        return speed

    # ------------------------------------------------------------------
    # 체결 불균형: 매수 체결량 vs 매도 체결량
    # ------------------------------------------------------------------
    def calc_imbalance(self, buy_volume, sell_volume):
        total = buy_volume + sell_volume + 1
        imbalance = (buy_volume - sell_volume) / total
        return imbalance  # -1 ~ +1

    # ------------------------------------------------------------------
    # 메인 분석 (symbol, tick)
    # ------------------------------------------------------------------
    def analyze(self, symbol, tick):
        """
        tick 예시:
        {
            'price': 78100,
            'bid': 78000,
            'ask': 78100,
            'bid_size': 1500,
            'ask_size': 1900,
            'buy_volume': 12000,
            'sell_volume': 9500,
            'volume': 21000
        }
        """

        bid = tick.get("bid", 0)
        ask = tick.get("ask", 0)
        bid_size = tick.get("bid_size", 0)
        ask_size = tick.get("ask_size", 0)
        buy_volume = tick.get("buy_volume", 0)
        sell_volume = tick.get("sell_volume", 0)

        # --------------------------------------------------------------
        # 1) 스프레드
        # --------------------------------------------------------------
        spread = self.calc_spread(bid, ask)

        # --------------------------------------------------------------
        # 2) 유동성 공백
        # --------------------------------------------------------------
        liquidity_void = self.detect_liquidity_void(bid_size, ask_size)

        # --------------------------------------------------------------
        # 3) 체결 속도
        # --------------------------------------------------------------
        speed = self.calc_speed(symbol)

        # --------------------------------------------------------------
        # 4) 체결 불균형 (imbalance)
        # --------------------------------------------------------------
        imbalance = self.calc_imbalance(buy_volume, sell_volume)

        # --------------------------------------------------------------
        # 5) 대량체결 Spike 감지
        # --------------------------------------------------------------
        spike = 1 if tick.get("volume", 0) > 50000 else 0

        # --------------------------------------------------------------
        # 6) 종합 Orderflow Score
        # --------------------------------------------------------------
        score = 0

        # buy imbalance → 강세
        score += np.clip(imbalance * 2.0, -2, 2)

        # speed → 체결 강도
        score += np.clip(speed * 0.05, -1, 1)

        # 대량 체결 spike
        score += spike * 0.3

        # 유동성 공백 감점
        if liquidity_void:
            score -= 1.0

        # 스프레드 크면 감점
        if spread > 0.015:
            score -= 1.0

        # 제한
        score = float(np.clip(score, -2.5, 2.5))

        return {
            "spread": spread,
            "speed": speed,
            "imbalance": imbalance,
            "spike": spike,
            "liquidity_void": liquidity_void,
            "orderflow_score": score,
            "quality": (score + 2.5) / 5.0  # 0.0 ~ 1.0
        }
