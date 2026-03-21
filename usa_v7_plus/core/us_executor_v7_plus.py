# =====================================================================
# us_executor_v7_plus.py
# 미국 매매 실행 엔진 — V7 PLUS (기관급)
# ---------------------------------------------------------------------
# 특징:
#   • BUY/SELL 실행 (SIM/PAPER/LIVE 대응 가능)
#   • TP/SL + 트레일링 스탑 + 레짐 기반 리스크
#   • Liquidity Stress / Imbalance 즉시 청산
#   • 슬리피지 자동 반영
# =====================================================================

import time
import traceback
from datetime import datetime


class USExecutorV7Plus:
    def __init__(self, logger=None, mode="SIM"):
        self.logger = logger
        self.mode = mode.upper()

        # 보유 포지션 구조
        # pos[sym] = {
        #     "entry": float,
        #     "qty": int,
        #     "tp": float,
        #     "sl": float,
        #     "trail_active": bool,
        #     "trail_stop": float,
        #     "reason": str
        # }
        self.positions = {}

        if logger:
            logger.info(f"[INIT] USExecutorV7Plus Loaded (mode={self.mode})")

    # ------------------------------------------------------------------
    # 내부 주문 실행 (실론/SIM 공용)
    # ------------------------------------------------------------------
    def _execute_order(self, symbol, side, price):
        slippage = price * 0.0005
        exec_price = round(price + slippage if side == "BUY" else price - slippage, 2)

        if self.logger:
            self.logger.info(f"[ORDER] {side} {symbol} @ {exec_price:.2f} ({self.mode})")

        return exec_price

    # ------------------------------------------------------------------
    # 신규 진입
    # ------------------------------------------------------------------
    def enter_position(self, symbol, price, qty, tp, sl, reason):
        exec_price = self._execute_order(symbol, "BUY", price)

        self.positions[symbol] = {
            "entry": exec_price,
            "qty": qty,
            "tp": tp,
            "sl": sl,
            "trail_active": False,
            "trail_stop": sl,
            "reason": reason,
        }

        if self.logger:
            self.logger.info(
                f"[ENTER] {symbol} qty={qty} entry={exec_price:.2f} TP={tp}% SL={sl}% reason={reason}"
            )

    # ------------------------------------------------------------------
    # 포지션 종료
    # ------------------------------------------------------------------
    def exit_position(self, symbol, price, reason=""):
        if symbol not in self.positions:
            return

        exec_price = self._execute_order(symbol, "SELL", price)
        entry = self.positions[symbol]["entry"]
        pnl = (exec_price - entry) / entry * 100

        if self.logger:
            self.logger.info(
                f"[EXIT] {symbol} price={exec_price:.2f} pnl={pnl:.2f}% (entry={entry:.2f}) reason={reason}"
            )

        del self.positions[symbol]

    # ------------------------------------------------------------------
    # 트레일링 스탑 업데이트
    # ------------------------------------------------------------------
    def _update_trailing(self, symbol, price):
        pos = self.positions[symbol]
        entry = pos["entry"]

        r = (price - entry) / entry * 100

        # 1) +1% 이상 = trailing ON
        if r > 1.0 and not pos["trail_active"]:
            pos["trail_active"] = True
            pos["trail_stop"] = 0.0  # 본절
            if self.logger:
                self.logger.info(f"[TRAIL ON] {symbol} → BE")

        # 2) trailing active면 계속 갱신
        if pos["trail_active"]:
            new_trail = r - 0.7
            if new_trail > pos["trail_stop"]:
                pos["trail_stop"] = new_trail
                if self.logger:
                    self.logger.info(
                        f"[TRAIL UPDATE] {symbol} trail_stop={pos['trail_stop']:.2f}%"
                    )

    # ------------------------------------------------------------------
    # 매도 체크 로직
    # ------------------------------------------------------------------
    def _check_exit(self, symbol, tick, regime):
        pos = self.positions[symbol]
        price = tick["price"]
        entry = pos["entry"]
        r = (price - entry) / entry * 100

        # 1) 트레일링 체크
        self._update_trailing(symbol, price)
        if r <= pos["trail_stop"]:
            self.exit_position(symbol, price, "TRAIL STOP HIT")
            return True

        # 2) 기본 SL
        if r <= pos["sl"]:
            self.exit_position(symbol, price, "STATIC SL HIT")
            return True

        # 3) 기본 TP
        if r >= pos["tp"]:
            self.exit_position(symbol, price, "TP HIT")
            return True

        # 4) Liquidity Stress
        ls = tick.get("liquidity_stress", 0)
        if ls > 60:
            self.exit_position(symbol, price, "LIQUIDITY STRESS > 60")
            return True

        # 5) Imbalance 급락
        imb = tick.get("imbalance", 0)
        if imb < -40:
            self.exit_position(symbol, price, "IMBALANCE CRASH")
            return True

        # 6) CRASH 레짐 → 즉시 전량 정리
        if regime == "CRASH":
            self.exit_position(symbol, price, "CRASH REGIME")
            return True

        return False

    # ------------------------------------------------------------------
    # 신호 처리
    # ------------------------------------------------------------------
    def process_signals(self, signals, market, portfolio, regime):
        try:
            for sig in signals:
                symbol = sig["symbol"]
                tp = sig["take_profit"]
                sl = sig["stop_loss"]
                price = market[symbol]["price"]
                volatility = market[symbol].get("volatility", 1.0)
                reason = sig.get("mode", "AUTO")

                # ============================================================
                # 1) 기존 포지션 → 청산 여부 체크
                # ============================================================
                if symbol in self.positions:
                    self._check_exit(symbol, market[symbol], regime)
                    continue

                # ============================================================
                # 2) 신규 진입 가능 여부
                # ============================================================
                if not portfolio.can_enter(symbol, price, volatility, regime):
                    continue

                qty = portfolio.calc_position_size(symbol, volatility)

                # ============================================================
                # 3) 진입
                # ============================================================
                self.enter_position(symbol, price, qty, tp, sl, reason)
                portfolio.enter(symbol, price, qty)

        except Exception as e:
            if self.logger:
                self.logger.error(f"[ERROR] Executor Loop: {e}")
                self.logger.error(traceback.format_exc())
            time.sleep(1)
