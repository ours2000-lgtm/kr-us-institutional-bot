# =============================================================
#  executor_us_plus_v4.py (미국 실행기 — PLUS V4 안정판)
# -------------------------------------------------------------
#  특징:
#    • Signal 엔진의 TP/SL 자동 반영
#    • +1.0% 도달 시 트레일링 스탑 자동 활성화
#    • Liquidity Stress / Imbalance 기반 즉시 청산
#    • SIM / PAPER / LIVE 동일 구조
# =============================================================

import time
import traceback
from datetime import datetime


class USExecutorPLUS:
    def __init__(self, logger=None, mode="SIM"):
        self.logger = logger
        self.mode = mode.upper()

        # 보유 포지션
        # positions[symbol] = {
        #   "entry": float,
        #   "tp": float,
        #   "sl": float,
        #   "trail_active": bool,
        #   "trail_stop": float
        # }
        self.positions = {}

        if logger:
            logger.info(f"[INIT] USExecutorPLUS V4 loaded (mode={self.mode})")

    # ---------------------------------------------------------
    # 주문 실행 (SIM/PAPER/LIVE 모두 동일 구조)
    # ---------------------------------------------------------
    def _execute_order(self, symbol, side, price):
        if self.logger:
            self.logger.info(f"[ORDER] {side} {symbol} @ {price:.2f} ({self.mode})")

    # ---------------------------------------------------------
    # 신규 포지션 진입
    # ---------------------------------------------------------
    def _enter_position(self, symbol, price, tp, sl):
        self.positions[symbol] = {
            "entry": price,
            "tp": tp,
            "sl": sl,
            "trail_active": False,
            "trail_stop": sl
        }

        if self.logger:
            self.logger.info(
                f"[ENTER] {symbol} entry={price:.2f} TP={tp}% SL={sl}%"
            )

    # ---------------------------------------------------------
    # 포지션 종료
    # ---------------------------------------------------------
    def _exit_position(self, symbol, price, reason=""):
        if symbol not in self.positions:
            return

        entry = self.positions[symbol]["entry"]
        pnl = (price - entry) / entry * 100

        if self.logger:
            self.logger.info(
                f"[EXIT] {symbol} price={price:.2f} PnL={pnl:.2f}% reason={reason}"
            )

        del self.positions[symbol]

    # ---------------------------------------------------------
    # 트레일링 스탑 업데이트 로직
    # ---------------------------------------------------------
    def _update_trailing(self, symbol, price):
        pos = self.positions[symbol]
        entry = pos["entry"]
        r = (price - entry) / entry * 100

        # ① +1.0% 이상 → 트레일링 ON
        if r > 1.0 and not pos["trail_active"]:
            pos["trail_active"] = True
            pos["trail_stop"] = 0.0  # 본절로 설정

            if self.logger:
                self.logger.info(f"[TRAIL ON] {symbol} Trail Started at BE")

        # ② 트레일링 활성화 → trailing 상승
        if pos["trail_active"]:
            new_trail = r - 0.7   # 항상 0.7% 아래에서 보호
            if new_trail > pos["trail_stop"]:
                pos["trail_stop"] = new_trail

                if self.logger:
                    self.logger.info(
                        f"[TRAIL UPDATE] {symbol} trail_stop={new_trail:.2f}%"
                    )

    # ---------------------------------------------------------
    # 신호 처리
    # ---------------------------------------------------------
    def process_signals(self, signals, market):
        try:
            for sig in signals:
                symbol = sig["symbol"]
                tp = sig["take_profit"]
                sl = sig["stop_loss"]
                side = sig["side"]

                price = market[symbol]["price"]

                # =====================================================
                # 신규 진입
                # =====================================================
                if symbol not in self.positions:
                    if side == "BUY":
                        self._execute_order(symbol, "BUY", price)
                        self._enter_position(symbol, price, tp, sl)
                    continue

                # =====================================================
                # 기존 포지션 관리
                # =====================================================
                pos = self.positions[symbol]
                entry = pos["entry"]
                r = (price - entry) / entry * 100

                # 1) 트레일링 업데이트
                self._update_trailing(symbol, price)

                # 2) 트레일링 스탑 도달
                if r <= pos["trail_stop"]:
                    self._exit_position(symbol, price, "TRAIL STOP HIT")
                    continue

                # 3) 기본 SL 도달
                if r <= sl:
                    self._exit_position(symbol, price, "STATIC STOP LOSS")
                    continue

                # 4) TP 도달
                if r >= tp:
                    self._exit_position(symbol, price, "TAKE PROFIT")
                    continue

                # 5) Liquidity Stress 과도
                ls = market[symbol].get("liquidity_stress", 0)
                if ls > 60:
                    self._exit_position(symbol, price, "LIQUIDITY STRESS > 60")
                    continue

                # 6) Imbalance 급락
                imb = market[symbol].get("imbalance", 0)
                if imb < -40:
                    self._exit_position(symbol, price, "IMBALANCE CRASH")
                    continue

        except Exception as e:
            if self.logger:
                self.logger.error(f"[ERROR] Executor Loop: {e}")
                self.logger.error(traceback.format_exc())

            time.sleep(1)
