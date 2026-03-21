# =============================================================
# executor_us_v7_plus.py — 미국 매매 실행 엔진 (V7 PLUS)
# =============================================================

import time
import traceback
from datetime import datetime


class USExecutorV7Plus:
    """
    미국 매매 실행기 (V7 PLUS)
    - TP / SL / 트레일링 스탑
    - 유동성 스트레스 기반 즉시 청산
    - 체결강도(imbalance) 기반 위험 차단
    - 시장 레짐 기반 리스크 조정
    """

    def __init__(self, logger=None, mode="SIM"):
        self.logger = logger
        self.mode = mode.upper()
        self.positions = {}  # symbol → position info

        if logger:
            logger.info(f"[INIT] USExecutorV7Plus (mode={self.mode}) loaded")

    # ---------------------------------------------------------
    # 내부 주문 처리 (SIM/PAPER/LIVE 공용)
    # ---------------------------------------------------------
    def _execute_order(self, symbol, side, price):
        if self.logger:
            self.logger.info(
                f"[ORDER] {side} {symbol} @ {price:.2f} ({self.mode})"
            )

    # ---------------------------------------------------------
    # 신규 진입
    # ---------------------------------------------------------
    def _enter(self, symbol, price, tp, sl):
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
    # 포지션 청산
    # ---------------------------------------------------------
    def _exit(self, symbol, price, reason):
        if symbol not in self.positions:
            return

        entry = self.positions[symbol]["entry"]
        pnl = (price - entry) / entry * 100

        if self.logger:
            self.logger.info(
                f"[EXIT] {symbol} price={price:.2f}, PnL={pnl:.2f}% reason={reason}"
            )

        del self.positions[symbol]

    # ---------------------------------------------------------
    # 트레일링 스탑 업데이트
    # ---------------------------------------------------------
    def _update_trailing(self, symbol, price):
        pos = self.positions[symbol]
        entry = pos["entry"]
        r = (price - entry) / entry * 100

        # 1) +1% 이상 → 트레일링 활성화 (본절)
        if r >= 1.0 and not pos["trail_active"]:
            pos["trail_active"] = True
            pos["trail_stop"] = 0.0

            if self.logger:
                self.logger.info(f"[TRAIL ON] {symbol} → BE activated")

        # 2) 트레일링 스탑 추적 : 최고가 - 0.65%
        if pos["trail_active"]:
            new_trail = r - 0.65
            if new_trail > pos["trail_stop"]:
                pos["trail_stop"] = new_trail

                if self.logger:
                    self.logger.info(
                        f"[TRAIL] {symbol} trail_stop={pos['trail_stop']:.2f}%"
                    )

    # ---------------------------------------------------------
    # 시그널 처리 (메인)
    # ---------------------------------------------------------
    def process(self, signals, market, portfolio, regime):
        """
        signals: 신호 리스트 [{symbol, score, tp, sl, ...}]
        market:  실시간 market_data
        portfolio: 포트폴리오 엔진
        regime: 시장 레짐
        """

        try:
            for sig in signals:
                symbol = sig["symbol"]
                tp = sig["take_profit"]
                sl = sig["stop_loss"]
                price = market[symbol]["price"]

                # -----------------------------------------------------
                # 1) 시장 레짐 기반 신규 진입 차단
                # -----------------------------------------------------
                if regime == "CRASH":
                    if self.logger:
                        self.logger.info(
                            f"[BLOCK] CRASH regime → 신규 진입 차단"
                        )
                    return

                # -----------------------------------------------------
                # 2) 신규 진입 처리
                # -----------------------------------------------------
                if symbol not in self.positions:
                    if portfolio.can_enter(symbol, price, regime):
                        self._execute_order(symbol, "BUY", price)
                        self._enter(symbol, price, tp, sl)
                        portfolio.add_position(symbol, price)
                    continue

                # -----------------------------------------------------
                # 3) 기존 포지션 관리
                # -----------------------------------------------------
                pos = self.positions[symbol]
                entry = pos["entry"]
                r = (price - entry) / entry * 100

                # --- 트레일링 업데이트 ---
                self._update_trailing(symbol, price)

                # --- ① 트레일링 스탑 HIT ---
                if r <= pos["trail_stop"]:
                    self._exit(symbol, price, "TRAIL STOP HIT")
                    portfolio.remove_position(symbol, price)
                    continue

                # --- ② 기본 SL ---
                if r <= sl:
                    self._exit(symbol, price, "STATIC SL HIT")
                    portfolio.remove_position(symbol, price)
                    continue

                # --- ③ TP 도달 ---
                if r >= tp:
                    self._exit(symbol, price, "TP HIT")
                    portfolio.remove_position(symbol, price)
                    continue

                # --- ④ Liquidity Stress 위험 ---
                ls = market[symbol].get("liquidity_stress", 0)
                if ls > 60:
                    self._exit(symbol, price, "LIQUIDITY STRESS")
                    portfolio.remove_position(symbol, price)
                    continue

                # --- ⑤ Imbalance 급락 ---
                imb = market[symbol].get("imbalance", 0)
                if imb < -40:
                    self._exit(symbol, price, "IMBALANCE CRASH")
                    portfolio.remove_position(symbol, price)
                    continue

        except Exception as e:
            if self.logger:
                self.logger.error(f"[ERROR] Executor Loop: {e}")
                self.logger.error(traceback.format_exc())
            time.sleep(1)
