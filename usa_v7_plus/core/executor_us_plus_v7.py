# =============================================================
# executor_us_plus_v7.py — 미국 실행기 (V7 PLUS)
# -------------------------------------------------------------
# 특징:
#   • Signal V7 PLUS와 연동
#   • TP/SL 실시간 반영
#   • 트레일링 스탑 V3
#   • Liquidity Stress / Imbalance 기반 즉시 정리
#   • 시장 레짐 기반 리스크 자동 조절
#   • SIM / PAPER / LIVE 3모드 지원
# =============================================================

import time
import traceback
from datetime import datetime


class USExecutorPLUS_V7:
    def __init__(self, logger=None, mode="SIM"):
        self.logger = logger
        self.mode = mode.upper()

        # 보유 포지션
        # pos[symbol] = {
        #   entry, qty, tp, sl,
        #   trail_active, trail_stop,
        #   timestamp
        # }
        self.pos = {}

        # 주문 쿨다운 (1.2초)
        self.last_order = {}

        if logger:
            logger.info(f"[INIT] USExecutorPLUS_V7 Loaded (mode={self.mode})")

    # ---------------------------------------------------------
    # 공용 주문 실행
    # ---------------------------------------------------------
    def _execute_order(self, side, symbol, price):
        if self.logger:
            self.logger.info(f"[ORDER] {side} {symbol} @ {price:.2f} ({self.mode})")
        # 실전 모드(PAPER/LIVE)는 여기에 API 주문 코드 넣기

    # ---------------------------------------------------------
    # 쿨다운 체크
    # ---------------------------------------------------------
    def _cooldown_ok(self, symbol):
        now = time.time()
        last = self.last_order.get(symbol, 0)

        if now - last < 1.2:
            return False

        self.last_order[symbol] = now
        return True

    # ---------------------------------------------------------
    # 신규 진입
    # ---------------------------------------------------------
    def _enter(self, symbol, price, tp, sl):
        if symbol in self.pos:
            return

        qty = 1  # 기본 1주

        # 슬리피지 (0.03% 가정)
        exec_price = round(price * 1.0003, 2)

        self.pos[symbol] = {
            "entry": exec_price,
            "qty": qty,
            "tp": tp,
            "sl": sl,
            "trail_active": False,
            "trail_stop": sl,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

        self._execute_order("BUY", symbol, exec_price)

        if self.logger:
            self.logger.info(
                f"[ENTER] {symbol} entry={exec_price:.2f}, TP={tp}%, SL={sl}%"
            )

    # ---------------------------------------------------------
    # 청산 처리
    # ---------------------------------------------------------
    def _exit(self, symbol, price, reason=""):
        if symbol not in self.pos:
            return

        pos = self.pos[symbol]
        entry = pos["entry"]

        # 슬리피지
        exec_price = round(price * 0.9997, 2)

        pnl = (exec_price - entry) / entry * 100

        self._execute_order("SELL", symbol, exec_price)

        if self.logger:
            self.logger.info(
                f"[EXIT] {symbol} @ {exec_price:.2f} / PnL={pnl:.2f}% / reason={reason}"
            )

        del self.pos[symbol]

    # ---------------------------------------------------------
    # 트레일링 스탑 업데이트
    # ---------------------------------------------------------
    def _update_trailing(self, symbol, price):
        pos = self.pos[symbol]
        entry = pos["entry"]

        r = (price - entry) / entry * 100

        # 트레일링 ON (1% 이상 수익)
        if r >= 1.0 and not pos["trail_active"]:
            pos["trail_active"] = True
            pos["trail_stop"] = 0.0

            if self.logger:
                self.logger.info(f"[TRAIL] {symbol} → ON (BE activated)")

        # 트레일링 활성 시: trail_stop 상승
        if pos["trail_active"]:
            new_stop = r - 0.7  # 고점 대비 -0.7% 마진
            if new_stop > pos["trail_stop"]:
                pos["trail_stop"] = new_stop

                if self.logger:
                    self.logger.info(
                        f"[TRAIL UPDATE] {symbol} trail_stop={new_stop:.2f}%"
                    )

    # ---------------------------------------------------------
    # 전체 시그널 처리
    # ---------------------------------------------------------
    def process_signals(self, signals, market, regime):
        """
        signals = [{
            symbol, score, side, tp, sl, strategy
        }]
        """
        try:
            # -----------------------------------------
            # 1) 신규 진입 처리
            # -----------------------------------------
            for sig in signals:
                sym = sig["symbol"]
                price = market[sym]["price"]
                tp = sig["tp"]
                sl = sig["sl"]

                if sym not in self.pos:
                    if not self._cooldown_ok(sym):
                        continue

                    if sig["side"] == "BUY":
                        self._enter(sym, price, tp, sl)

            # -----------------------------------------
            # 2) 기존 포지션 관리
            # -----------------------------------------
            for sym in list(self.pos.keys()):
                price = market[sym]["price"]
                pos = self.pos[sym]
                entry = pos["entry"]

                r = (price - entry) / entry * 100

                # ① 트레일링 업데이트
                self._update_trailing(sym, price)

                # ② 트레일링 스탑 hit
                if r <= pos["trail_stop"]:
                    self._exit(sym, price, "TRAIL STOP")
                    continue

                # ③ 기본 SL hit
                if r <= pos["sl"]:
                    self._exit(sym, price, "STATIC SL")
                    continue

                # ④ TP hit
                if r >= pos["tp"]:
                    self._exit(sym, price, "TAKE PROFIT")
                    continue

                # ⑤ Liquidity Stress
                ls = market[sym].get("liquidity_stress", 0)
                if ls > 55:
                    self._exit(sym, price, "LIQUIDITY STRESS")
                    continue

                # ⑥ Imbalance 기반 급락
                imb = market[sym].get("imbalance", 0)
                if imb < -40:
                    self._exit(sym, price, "IMBALANCE CRASH")
                    continue

                # ⑦ BEAR & CRASH 레짐 -> 추가 리스크컷
                if regime in ["BEAR", "CRASH"]:
                    if r < -0.7:
                        self._exit(sym, price, f"{regime} RISK CUT")
                        continue

        except Exception as e:
            if self.logger:
                self.logger.error(f"[ERROR] Executor_V7: {e}")
                self.logger.error(traceback.format_exc())
            time.sleep(1)
