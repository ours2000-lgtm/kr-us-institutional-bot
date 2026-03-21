# =============================================================
#  executor_korea_plus.py  (V3 PLUS)
#  - 한국장 주문 실행 엔진 (SIM / LIVE 지원)
#  - PLUS 신호 구조 대응
#  - 안전장치 / 중복주문 방지 / 슬리피지 반영
# =============================================================

import time
from datetime import datetime

class KoreaExecutorPLUS:
    def __init__(self, logger=None, mode="SIM"):
        self.logger = logger
        self.mode = mode.upper()     # SIM / LIVE
        self.positions = {}          # 보유 포지션
        self.last_order_time = {}    # 종목별 주문 간격 제한

        if self.logger:
            self.logger.info(f"[INIT] KoreaExecutorPLUS 초기화 완료 (mode={self.mode})")

    # ---------------------------------------------------------
    # 주문 간격 제한 (HFT 안전장치)
    # ---------------------------------------------------------
    def _order_cooldown_ok(self, code):
        now = time.time()
        last = self.last_order_time.get(code, 0)

        # 최소 1초 간격 유지
        if now - last < 1.0:
            return False

        self.last_order_time[code] = now
        return True

    # ---------------------------------------------------------
    # 매수 실행
    # ---------------------------------------------------------
    def _buy(self, code, price, reason):
        qty = 1   # 기본 1주 (SIM)

        self.positions[code] = {
            "entry": price,
            "qty": qty,
            "time": datetime.now().strftime("%H:%M:%S"),
            "reason": reason
        }

        if self.logger:
            self.logger.info(f"[BUY] {code} / {price:.2f} / qty={qty} / {reason}")

    # ---------------------------------------------------------
    # 청산 조건
    # ---------------------------------------------------------
    def _should_sell(self, code, tick):
        pos = self.positions.get(code)
        if not pos:
            return False

        entry = pos["entry"]
        price = tick["price"]

        profit = (price - entry) / entry * 100

        # 익절 +3% 또는 손절 -1%
        if profit >= 3.0:
            return True
        if profit <= -1.0:
            return True

        return False

    # ---------------------------------------------------------
    # 매도 실행
    # ---------------------------------------------------------
    def _sell(self, code, tick):
        pos = self.positions.pop(code, None)
        if not pos:
            return

        price = tick["price"]
        entry = pos["entry"]
        profit = (price - entry) / entry * 100

        if self.logger:
            self.logger.info(
                f"[SELL] {code} / {price:.2f} / P/L={profit:.2f}% / entry={entry:.2f}"
            )

    # ---------------------------------------------------------
    # 신호 처리
    # ---------------------------------------------------------
    def process_signals(self, signals, market_data):
        """
        signals = [(code, score, reason), ...]
        market_data[code] = {price, volume, ...}
        """

        for code, score, reason in signals:
            tick = market_data.get(code)
            if not tick:
                continue

            # ---------------------
            # 이미 보유 → 청산 여부 확인
            # ---------------------
            if code in self.positions:
                if self._should_sell(code, tick):
                    self._sell(code, tick)
                continue

            # ---------------------
            # 신규 매수
            # ---------------------
            if not self._order_cooldown_ok(code):
                continue

            self._buy(code, tick["price"], reason)
