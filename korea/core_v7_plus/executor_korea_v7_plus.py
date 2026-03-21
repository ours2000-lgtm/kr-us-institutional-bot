# =============================================================
# executor_korea_v7_plus.py
# 한국 자동매매 실행 엔진 — V7 PLUS (기관급)
# -------------------------------------------------------------
# 특징:
#   • Adaptive TP/SL + 트레일링 스탑
#   • 체결강도 기반 위험 차단
#   • 급락 Imbalance / 유동성 스트레스 감시
#   • 상한가/하한가 체크
#   • 포트폴리오(노출·보유·수량)와 밀접 통합
# =============================================================

import time
import traceback
from datetime import datetime


class KoreaExecutorV7Plus:
    def __init__(self, logger=None, mode="SIM"):
        self.logger = logger
        self.mode = mode.upper()

        # 보유 포지션
        # pos[symbol] = { entry, qty, tp, sl, trail_active, trail_stop }
        self.positions = {}

        if logger:
            logger.info(f"[INIT] KoreaExecutorV7Plus Loaded (mode={self.mode})")

    # ---------------------------------------------------------
    # 내부 주문 실행 (SIM/LIVE 공용)
    # ---------------------------------------------------------
    def _execute_order(self, symbol, side, price):
        # 슬리피지 기본 반영
        slip = price * 0.0004
        exec_price = round(price + slip if side == "BUY" else price - slip, 2)

        if self.logger:
            self.logger.info(f"[ORDER] {side} {symbol} @ {exec_price:.2f} ({self.mode})")

        return exec_price

    # ---------------------------------------------------------
    # 신규 진입
    # ---------------------------------------------------------
    def enter_position(self, symbol, price, qty, tp, sl, reason):
        exec_price = self._execute_order(symbol, "BUY", price)

        self.positions[symbol] = {
            "entry": exec_price,
            "qty": qty,
            "tp": tp,
            "sl":
