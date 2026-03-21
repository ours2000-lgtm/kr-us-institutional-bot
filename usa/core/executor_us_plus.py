# =============================================================
# executor_us_plus.py (미국 실행기 — V4 안정판)
# =============================================================
# 특징:
#   • TP/SL 자동 적용 (시그널 엔진 제공값 사용)
#   • 트레일링 스탑 전체 개선
#   • Imbalance / Liquidity Stress 기반 긴급청산
#   • 미국 호가(소수점 2자리) 자동 처리
#   • 중복 매수 방지 (포트폴리오 연동)
#   • SIM / PAPER / LIVE 통합
# =============================================================

import time
import traceback
from datetime import datetime


class USExecutorPLUS:
    def __init__(self, logger=None, mode="SIM", portfolio=None):
        self.logger = logger
        self.mode = mode.upper()      # SIM / PAPER / LIVE
        self.portfolio = portfolio    # 외부 Portfolio 객체

        # 보유 포지션 구조
        # positions[symbol] = {
        #     "entry": float,
        #     "tp": float,
        #     "sl": float,
        #     "trail_active": False,
        #     "trail_stop_pct": float
        # }
        self.positions = {}

        if self.logger:
            self.logger.info(f"[INIT] USExecutorPLUS V4 Loaded (mode={self.mode})")

    # ---------------------------------------------------------
    # 주문 실행 (SIM/PAPER/LIVE 공용)
    # ---------------------------------------------------------
    def _execute_order(self, symbol, side, price):
        if self.logger:
            self.logger.info(
                f"[ORDER] {side} {symbol} @ {price:.2f} ({self.mode})"
            )

    # ---------------------------------------------------------
    # 신규 포지션 진입
    # ---------------------------------------------------------
    def _enter_position(self, symbol, price, tp, sl):
        self.positions[symbol] = {
            "entry": price,
            "tp": tp,
            "sl": sl,
            "trail_active": False,
            "trail_stop_pct": sl        # 실제 초기값은 SL 기준
        }

        if self.portfolio:
            self.portfolio.add_position(symbol, qty=1, price=price)

        if self.logger:
            self.logger.info(
                f"[ENTER] {symbol} entry={price:.2f} TP={tp}% SL={sl}%"
            )

    # ---------------------------------------------------------
    # 포지션 종료 처리
    # ---------------------------------------------------------
    def _exit_position(self, symbol, price, reason):
        if symbol not in self.positions:
            return

        entry = self.positions[symbol]["entry"]
        pnl = (price - entry) / entry * 100

        if self.logger:
            self.logger.info(
                f"[EXIT] {symbol} @ {price:.2f} PnL={pnl:.2f}% reason={reason}"
            )

        if self.portfolio:
            self.portfolio.remove_position(symbol, exit_price=price)

        del self.positions[symbol]

    # ---------------------------------------------------------
    # 트레일링 스탑 업데이트
    # ---------------------------------------------------------
    def _update_trailing(self, symbol, price):
        pos = self.positions[symbol]
        entry = pos["entry"]

        r = (price - entry) / entry * 100  # 현재 수익률 %

        # 1) +1.0% 돌파 → 트레일링 활성화
        if r > 1.0 and not pos["trail_active"]:
            pos["trail_active"] = True
            pos["trail_stop_pct"] = 0.0  # 본절(BE)
            if self.logger:
                self.logger.info(f"[TRAIL ON] {symbol} → BE (0%)")

        # 2) 트레일링 활성 상태 → 스탑 상향조정
        if pos["trail_active"]:
            new_trail = r - 0.7  # 항상 현재보다 0.7% 아래
            if new_trail > pos["trail_stop_pct"]:
                pos["trail_stop_pct"] = new_trail
                if self.logger:
                    self.logger.info(
                        f"[TRAIL UPDATE] {symbol} → {pos['trail_stop_pct']:.2f}%"
                    )

    # ---------------------------------------------------------
    # 시그널 처리
    # ---------------------------------------------------------
    def process_signals(self, signals, market_data):
        try:
            for sig in signals:
                symbol = sig["symbol"]
                tp = sig["take_profit"]
                sl = sig["stop_loss"]
                side = sig["side"]

                price = market_data[symbol]["price"]

                # ---------------------------------------------
                # 신규 진입
                # ---------------------------------------------
                if symbol not in self.positions:

                    # 포트폴리오 진입 가능 여부 체크
                    if self.portfolio and not self.portfolio.can_enter(symbol, price):
                        continue

                    if side == "BUY":
                        self._execute_order(symbol, "BUY", price)
                        self._enter_position(symbol, price, tp, sl)
                    continue

                # ---------------------------------------------
                # 기존 포지션 관리
                # ---------------------------------------------
                pos = self.positions[symbol]
                entry = pos["entry"]

                r = (price - entry) / entry * 100  # 현재 수익률 %

                # 트레일링 업데이트
                self._update_trailing(symbol, price)

                # 1) 트레일링 스탑 결시
                if r <= pos["trail_stop_pct"]:
                    self._exit_position(symbol, price, "TRAIL STOP")
                    continue

                # 2) 기본 SL
                if r <= sl:
                    self._exit_position(symbol, price, "STATIC SL")
                    continue

                # 3) 기본 TP
                if r >= tp:
                    self._exit_position(symbol, price, "TP HIT")
                    continue

                # 4) Liquidity Stress 기반 긴급청산
                ls = market_data[symbol].get("liquidity_stress", 0)
                if ls > 60:
                    self._exit_position(symbol, price, "LIQUIDITY STRESS")
                    continue

                # 5) Imbalance 이상치(급락 전조)
                imb = market_data[symbol].get("imbalance", 0)
                if imb < -40:
                    self._exit_position(symbol, price, "IMBALANCE CRASH")
                    continue

        except Exception as e:
            if self.logger:
                self.logger.error(f"[ERROR] Executor Loop: {e}")
                self.logger.error(traceback.format_exc())
            time.sleep(1)
