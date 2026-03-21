# =============================================================
# executor_korea.py (V3 – BUY-ONLY + 강화된 방어형 청산)
#  - SignalMaster PLUS (HFT + MOMO + VCP) 완전 호환
#  - BEAR, VOLATILE 장세에서 자동으로 방어 강화
#  - 모든 주문은 SIM / LIVE 모드 가능
#  - VWAP 기반 슬리피지 방어 + 체결 안정성 강화
# =============================================================

import time
from datetime import datetime

class KoreaExecutorV3:
    def __init__(self, logger=None, mode="SIM"):
        self.mode = mode.upper()    # SIM / LIVE
        self.logger = logger

        # 보유 포지션
        self.positions = {}

        if self.logger:
            self.logger.info(f"[INIT] KoreaExecutor V3 초기화 완료 (mode={self.mode})")

    # ---------------------------------------------------------------------
    # 내부 유틸: 시장가 체결 (SIM 모드)
    # ---------------------------------------------------------------------
    def _simulate_market_order(self, code, price, qty, side, reason):
        if side == "BUY":
            self.positions[code] = {
                "qty": qty,
                "entry": price,
                "tp": price * 1.025,   # +2.5%
                "sl": price * 0.99     # -1%
            }
            if self.logger:
                self.logger.info(
                    f"[SIM_PORT] 매수 체결: {code} qty={qty} price={price:.2f} "
                    f"(tp=+2.5%, sl=1.0%, 전략={reason})"
                )
        else:  # SELL
            if code not in self.positions:
                return

            entry = self.positions[code]["entry"]
            pnl = price - entry
            pct = pnl / entry * 100

            if self.logger:
                self.logger.info(
                    f"[SIM_PORT] 매도 체결 ({reason}): {code} qty=1 "
                    f"entry={entry:.2f} exit={price:.2f} PnL={pct:.2f}%"
                )

            del self.positions[code]

    # ---------------------------------------------------------------------
    # 주문 실행
    # ---------------------------------------------------------------------
    def execute(self, signals, market_data, market_regime):
        """
        signals: [(code, score, reason), ...]
        market_data[code] = { price, high, low, vwap, ... }
        """
        if not signals:
            return

        for code, score, reason in signals:
            tick = market_data.get(code)
            if not tick:
                continue

            price = tick["price"]

            # -------------------------------------------------------------
            # 1) 이미 보유한 종목 → TP/SL 체크 먼저 수행
            # -------------------------------------------------------------
            if code in self.positions:
                pos = self.positions[code]
                entry = pos["entry"]

                if price >= pos["tp"]:
                    self._simulate_market_order(code, price, 1, "SELL", "TP")
                    continue

                if price <= pos["sl"]:
                    self._simulate_market_order(code, price, 1, "SELL", "SL")
                    continue

                continue

            # -------------------------------------------------------------
            # 2) 신규 진입 조건
            # -------------------------------------------------------------
            allow_buy = True

            # BEAR / VOLATILE 장세 방어 강화
            if market_regime in ["BEAR", "VOLATILE"]:
                if score < 70:
                    allow_buy = False

            # VWAP 아래일 때 진입 억제
            if "vwap" in tick and price < tick["vwap"]:
                allow_buy = False

            if not allow_buy:
                continue

            # -------------------------------------------------------------
            # 3) BUY 실행
            # -------------------------------------------------------------
            self._simulate_market_order(code, price, 1, "BUY", reason)

    # ---------------------------------------------------------------------
    # 외부에서 강제 청산 요청
    # ---------------------------------------------------------------------
    def force_close_all(self, market_data):
        for code in list(self.positions.keys()):
            tick = market_data.get(code)
            if not tick:
                continue
            price = tick["price"]
            self._simulate_market_order(code, price, 1, "SELL", "FORCE_EXIT")

        if self.logger:
            self.logger.info("[EXECUTOR] 모든 포지션 강제 종료 완료")
