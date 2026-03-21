# =====================================================================
# executor_us_v7_plus.py — 미국 매매 실행 엔진 (V7 PLUS / 최종 안정본)
# =====================================================================

import time
import traceback
from datetime import datetime


class USExecutorV7Plus:
    def __init__(self, logger=None, mode="SIM"):
        self.logger = logger
        self.mode = mode.upper()
        self.positions = {}  # symbol → position info

        if logger:
            logger.info(f"[INIT] USExecutorV7Plus Loaded (mode={self.mode})")

    # ---------------------------------------------------------
    # 내부 주문 처리 (BUY/SELL 공용)
    # ---------------------------------------------------------
    def _execute_order(self, symbol, side, price):
        slippage = price * 0.0005
        exec_price = round(
            price + slippage if side == "BUY" else price - slippage, 2
        )

        if self.logger:
            self.logger.info(f"[ORDER] {side} {symbol} @ {exec_price:.2f} ({self.mode})")

        return exec_price

    # ---------------------------------------------------------
    # 신규 진입
    # ---------------------------------------------------------
    def _enter(self, symbol, price, tp, sl, reason):
        exec_price = self._execute_order(symbol, "BUY", price)

        self.positions[symbol] = {
            "entry": exec_price,
            "qty": 1,
            "tp": tp,
            "sl": sl,
            "trail_active": False,
            "trail_stop": sl,
            "reason": reason,
        }

        if self.logger:
            self.logger.info(
                f"[ENTER] {symbol} entry={exec_price:.2f} TP={tp}% SL={sl}% reason={reason}"
            )

    # ---------------------------------------------------------
    # 포지션 종료
    # ---------------------------------------------------------
    def _exit(self, symbol, price, reason):
        if symbol not in self.positions:
            return

        exec_price = self._execute_order(symbol, "SELL", price)
        entry = self.positions[symbol]["entry"]
        pnl = (exec_price - entry) / entry * 100

        if self.logger:
            self.logger.info(
                f"[EXIT] {symbol} price={exec_price:.2f} pnl={pnl:.2f}% "
                f"(entry={entry:.2f}) reason={reason}"
            )

        del self.positions[symbol]

    # ---------------------------------------------------------
    # 트레일링 스탑 업데이트
    # ---------------------------------------------------------
    def _update_trailing(self, symbol, price):
        pos = self.positions[symbol]
        entry = pos["entry"]
        r = (price - entry) / entry * 100

        # 1) +1% 이상 → 트레일링 활성화
        if r >= 1.0 and not pos["trail_active"]:
            pos["trail_active"] = True
            pos["trail_stop"] = 0.0

            if self.logger:
                self.logger.info(f"[TRAIL ON] {symbol} → BE activated")

        # 2) 트레일링 스탑 추적
        if pos["trail_active"]:
            new_trail = r - 0.7
            if new_trail > pos["trail_stop"]:
                pos["trail_stop"] = new_trail

                if self.logger:
                    self.logger.info(
                        f"[TRAIL] {symbol} trail_stop={pos['trail_stop']:.2f}%"
                    )

    # ---------------------------------------------------------
    # 청산 조건 판단
    # ---------------------------------------------------------
    def _check_exit(self, symbol, tick, regime):
        pos = self.positions[symbol]
        price = tick["price"]
        entry = pos["entry"]
        r = (price - entry) / entry * 100

        # 1) 트레일링 스탑
        self._update_trailing(symbol, price)
        if r <= pos["trail_stop"]:
            self._exit(symbol, price, "TRAIL STOP HIT")
            return True

        # 2) SL
        if r <= pos["sl"]:
            self._exit(symbol, price, "STATIC SL HIT")
            return True

        # 3) TP
        if r >= pos["tp"]:
            self._exit(symbol, price, "TP HIT")
            return True

        # 4) Liquidity Stress
        if tick.get("liquidity_stress", 0) > 60:
            self._exit(symbol, price, "LIQUIDITY STRESS")
            return True

        # 5) Imbalance
        if tick.get("imbalance", 0) < -40:
            self._exit(symbol, price, "IMBALANCE CRASH")
            return True

        # 6) CRASH 레짐 → 즉시 전량 정리
        if regime == "CRASH":
            self._exit(symbol, price, "CRASH REGIME")
            return True

        return False

    # ---------------------------------------------------------
    # 신호 처리 (메인)
    # ---------------------------------------------------------
    def process(self, signals, market, portfolio, regime):
        try:
            for sig in signals:
                symbol = sig["symbol"]
                price = market[symbol]["price"]

                # ★ tp/sl 키 mismatch 해결
                tp = sig["tp"]
                sl = sig["sl"]

                reason = sig.get("reason", "AUTO")

                # -----------------------------------------------------
                # 1) 기존 포지션 → 청산 체크
                # -----------------------------------------------------
                if symbol in self.positions:
                    self._check_exit(symbol, market[symbol], regime)
                    continue

                # -----------------------------------------------------
                # 2) 신규 진입 가능 여부
                # -----------------------------------------------------
                if not portfolio.can_enter(symbol, price, regime):
                    continue

                # -----------------------------------------------------
                # 3) 신규 진입
                # -----------------------------------------------------
                self._enter(symbol, price, tp, sl, reason)
                portfolio.add_position(symbol, price)

        except Exception as e:
            if self.logger:
                self.logger.error(f"[ERROR] Executor Loop: {e}")
                self.logger.error(traceback.format_exc())
            time.sleep(1)
