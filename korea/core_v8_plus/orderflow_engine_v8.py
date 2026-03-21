# =============================================================
# orderflow_engine_v8.py — 체결·유동성 엔진 (V8 PLUS)
# -------------------------------------------------------------
# 역할:
#   • Bid/Ask Imbalance 계산
#   • 체결 속도(Tick Speed)
#   • 스프레드 분석
#   • 유동성 공백(Liquidity Gap)
#   • Orderflow Score 산출 (0~2점)
# =============================================================

import time
from collections import deque

class OrderflowEngineV8:
    def __init__(self, max_ticks=20, logger=None):
        self.logger = logger

        # 최근 체결 데이터 저장
        self.recent_ticks = {}          # {symbol: deque([price, ...])}
        self.max_ticks = max_ticks

        # 최근 체크 시간
        self.last_time = {}

        if logger:
            logger.info("[INIT] OrderflowEngineV8 Loaded")

    # ----------------------------------------------------------
    # 체결 데이터 추가
    # ----------------------------------------------------------
    def _update_ticks(self, code, price):
        if code not in self.recent_ticks:
            self.recent_ticks[code] = deque(maxlen=self.max_ticks)

        self.recent_ticks[code].append(price)

    # ----------------------------------------------------------
    # Bid/Ask Imbalance (단순 버전)
    # ----------------------------------------------------------
    def _imbalance(self, tick):
        bid = tick.get("bid", None)
        ask = tick.get("ask", None)

        if bid is None or ask is None:
            return 0.0, []

        if ask == 0:
            return 0.0, []

        imbalance = (ask - bid) / ask
        reasons = []

        if imbalance > 0.2:
            reasons.append("Strong Ask Pressure")
        elif imbalance < -0.2:
            reasons.append("Strong Bid Pressure")

        return imbalance, reasons

    # ----------------------------------------------------------
    # 스프레드 분석
    # ----------------------------------------------------------
    def _spread(self, tick):
        bid = tick.get("bid", None)
        ask = tick.get("ask", None)

        if bid is None or ask is None:
            return 0.0, []

        spread = ask - bid
        reasons = []

        if spread <= 2:
            reasons.append("Tight Spread (Good Liquidity)")
            return 0.2, reasons
        elif spread > 10:
            reasons.append("Wide Spread (Risk)")
            return -0.2, reasons

        return 0.0, []

    # ----------------------------------------------------------
    # 체결 속도 (틱 증가 횟수)
    # ----------------------------------------------------------
    def _tick_speed(self, code):
        if code not in self.recent_ticks or len(self.recent_ticks[code]) < 3:
            return 0.0, []

        changes = 0
        ticks = list(self.recent_ticks[code])

        for i in range(1, len(ticks)):
            if ticks[i] != ticks[i - 1]:
                changes += 1

        if changes >= len(ticks) * 0.6:
            return 0.3, ["Fast Tick Speed (Algo/기관 흐름)"]
        else:
            return 0.0, []

    # ----------------------------------------------------------
    # Liquidity Gap 체크
    # ----------------------------------------------------------
    def _liquidity_gap(self, tick):
        if "gap" in tick and tick["gap"]:
            return -0.3, ["Liquidity Gap Detected"]

        return 0.0, []

    # ----------------------------------------------------------
    # 종합 평가
    # ----------------------------------------------------------
    def evaluate(self, code, tick):
        price = tick["price"]
        self._update_ticks(code, price)

        score = 0.0
        reasons = []

        # 1) Imbalance
        imb, r1 = self._imbalance(tick)
        score += imb * 0.5
        reasons.extend(r1)

        # 2) Spread
        sp, r2 = self._spread(tick)
        score += sp
        reasons.extend(r2)

        # 3) Tick Speed
        ts, r3 = self._tick_speed(code)
        score += ts
        reasons.extend(r3)

        # 4) Liquidity Gap
        lg, r4 = self._liquidity_gap(tick)
        score += lg
        reasons.extend(r4)

        return {
            "score": round(score, 3),
            "reasons": reasons
        }
