# =============================================================
#  executor_us_plus_v3.py (미국 매매 실행 엔진 — V3 PLUS)
# -------------------------------------------------------------
#  특징:
#    • SIM / PAPER / LIVE 지원 (AUTO 엔진과 호환)
#    • 과도한 중복 매수 방지 (쿨다운)
#    • 익절(+3%) / 손절(-1%) 기본 규칙
#    • 슬리피지(호가 미끄러짐) 반영
#    • 미국 시장의 소수점 가격 처리 자동 지원
# =============================================================

import time
from datetime import datetime


class USExecutorPLUS:
    def __init__(self, logger=None, mode="SIM"):
        self.logger = logger
        self.mode = mode.upper()  # SIM / PAPER / LIVE
        self.positions = {}        # 보유 포지션
        self.last_order_time = {}  # 종목별 주문 간격 제한

        if self.logger:
            self.logger.info(f"[INIT] USExecutorPLUS 초기화 완료 (mode={self.mode})")

    # ---------------------------------------------------------
    # 주문 간격 제한 (초단타 오버트레이딩 방지)
    # ---------------------------------------------------------
    def _order_cooldown_ok(self, code):
        now = time.time()
        last = self.last_order_time.get(code, 0)

        # 최소 1.2초 간격 유지 (미국 시장 호가 변동이 심함)
        if now - last < 1.2:
            return False

        self.last_order_time[code] = now
        return True

    # ---------------------------------------------------------
    # 매수 실행 (SIM/PAPER/LIVE 공용)
    # ---------------------------------------------------------
    def _buy(self, code, price, reason):
        # 슬리피지 적용 (미국은 평균 0.01~0.05 달러 미끄러짐 반영)
        slippage = price * 0.0005  
        exec_price = round(price + slippage, 2)

        qty = 1  # 기본 1주 (SIM)

        self.positions[code] = {
            "entry": exec_price,
            "qty": qty,
            "time": datetime.now().strftime("%H:%M:%S"),
            "reason": reason
        }

        if self.logger:
            self.logger.info(
                f"[BUY] {code} / {exec_price:.2f} / qty={qty} / reason={reason}"
            )

    # ---------------------------------------------------------
    # 청산 조건 체크
    # ---------------------------------------------------------
    def _should_sell(self, code, tick):
        pos = self.positions.get(code)
        if not pos:
            return False

        entry = pos["entry"]
        price = tick["price"]

        profit = (price - entry) / entry * 100

        # 기본 수익·손실 기준
        if profit >= 3.0:   # 익절
            return True
        if profit <= -1.0:  # 손절
            return True

        return False

    # ---------------------------------------------------------
    # 매도 실행
    # ---------------------------------------------------------
    def _sell(self, code, tick):
        pos = self.positions.pop(code, None)
        if not pos:
            return

        # 슬리피지 적용
        slippage = tick["price"] * 0.0005
        exec_price = round(tick["price"] - slippage, 2)

        entry = pos["entry"]
        profit = (exec_price - entry) / entry * 100

        if self.logger:
            self.logger.info(
                f"[SELL] {code} / {exec_price:.2f} / PnL={profit:.2f}% "
                f"(entry={entry:.2f}, qty={pos['qty']})"
            )

    # ---------------------------------------------------------
    # 전체 신호 처리
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

            # -------------------------------------------------
            # 이미 보유 중 → 청산 여부 판단
            # -------------------------------------------------
            if code in self.positions:
                if self._should_sell(code, tick):
                    self._sell(code, tick)
                continue

            # -------------------------------------------------
            # 신규 매수 조건 체크
            # -------------------------------------------------
            if not self._order_cooldown_ok(code):
                continue  # 쿨다운 미적용

            # 신규 매수
            self._buy(code, tick["price"], reason)
