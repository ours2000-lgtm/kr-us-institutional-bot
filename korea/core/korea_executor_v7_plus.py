# =============================================================
#  korea_executor_v7_plus.py
#  한국 자동매매 실행 엔진 — V7 PLUS (기관급)
# -------------------------------------------------------------
#  기능:
#    • +3% 익절 / -1% 손절 + 트레일링스탑
#    • 시장 레짐 기반 리스크 조정
#    • 중복 진입 방지 / 슬리피지 자동 적용
# =============================================================

import time
from datetime import datetime


class KoreaExecutorV7PLUS:
    def __init__(self, logger=None, mode="SIM"):
        self.logger = logger
        self.mode = mode.upper()

        # positions[symbol] = {
        #     entry, qty, tp, sl, trail_active, trail_stop
        # }
        self.positions = {}

        if logger:
            logger.info(f"[INIT] KoreaExecutorV7PLUS Loaded (mode={self.mode})")

    # ---------------------------------------------------------
    # 주문 실행 (SIM 버전)
    # ---------------------------------------------------------
    def _execute(self, symbol, side, price):
        if self.logger:
            self.logger.info(f"[ORDER] {side} {symbol} @ {price:.2f} ({self.mode})")

    # ---------------------------------------------------------
    # 트레일링 업데이트
    # ---------------------------------------------------------
    def _update_trailing(self, symbol, price):
        pos = self.positions[symbol]
        entry = pos["entry"]

        r = (price - entry) / entry * 100

        # ① 수익 +0.8% 이상 → 트레일링 ON
        if r > 0.8 and not pos["trail_active"]:
            pos["trail_active"] = True
            pos["trail_stop"] = 0.0  # 본절(BE)
            if self.logger:
                self.logger.info(f"[TRAIL ON] {symbol} trailing at BE")

        # ② 트레일링 활성화 후 → stop 계속 상승
        if pos["trail_active"]:
            new_stop = r - 0.6
            if new_stop > pos["trail_stop"]:
                pos["trail_stop"] = new_stop
                if self.logger:
                    self.logger.info(
                        f"[TRAIL UPDATE] {symbol} trail_stop={pos['trail_stop']:.2f}%"
                    )

    # ---------------------------------------------------------
    # 포지션 진입
    # ---------------------------------------------------------
    def enter(self, symbol, price, market_regime):
        if symbol in self.positions:
            return  # 중복 방지

        # 기본 TP/SL
        tp = 3.0
        sl = -1.0

        # 레짐 기반 조정
        if market_regime == "BULL":
            tp += 0.3
        if market_regime == "BEAR":
            sl -= 0.2

        # 슬리피지
        exec_price = round(price * 1.0003, 2)

        self._execute(symbol, "BUY", exec_price)

        self.positions[symbol] = {
            "entry": exec_price,
            "qty": 1,
            "tp": tp,
            "sl": sl,
            "trail_active": False,
            "trail_stop": sl
        }

        if self.logger:
            self.logger.info(
                f"[ENTER] {symbol} entry={exec_price} TP={tp}% SL={sl}%"
            )

    # ---------------------------------------------------------
    # 포지션 청산
    # ---------------------------------------------------------
    def exit(self, symbol, price, reason):
        pos = self.positions.pop(symbol, None)
        if not pos:
            return

        exec_price = round(price * 0.9997, 2)  # 슬리피지 반영
        entry = pos["entry"]
        r = (exec_price - entry) / entry * 100

        if self.logger:
            self.logger.info(
                f"[EXIT] {symbol} price={exec_price:.2f} PnL={r:.2f}% reason={reason}"
            )

    # ---------------------------------------------------------
    # 전체 포지션 관리 (TP/SL/Trail)
    # ---------------------------------------------------------
    def update_positions(self, market_data):
        for symbol, pos in list(self.positions.items()):
            if symbol not in market_data:
                continue

            price = market_data[symbol]["price"]
            entry = pos["entry"]

            r = (price - entry) / entry * 100

            # 트레일링 갱신
            self._update_trailing(symbol, price)

            # 1) 트레일링 스탑 hit
            if pos["trail_active"] and r <= pos["trail_stop"]:
                self.exit(symbol, price, "TRAIL STOP")
                continue

            # 2) 기본 SL hit
            if r <= pos["sl"]:
                self.exit(symbol, price, "STOP LOSS")
                continue

            # 3) TP hit
            if r >= pos["tp"]:
                self.exit(symbol, price, "TAKE PROFIT")
                continue

    # ---------------------------------------------------------
    # signal → position 진입
    # ---------------------------------------------------------
    def process_signals(self, signals, market_data, market_regime):
        """
        signals: [(symbol, score, reason), ...]
        """
        for symbol, score, reason in signals:
            if symbol not in market_data:
                continue

            price = market_data[symbol]["price"]

            # 신규 진입 only
            if symbol not in self.positions:
                self.enter(symbol, price, market_regime)
