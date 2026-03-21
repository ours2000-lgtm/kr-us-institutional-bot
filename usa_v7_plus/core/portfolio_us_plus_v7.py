# =============================================================
# portfolio_us_plus_v7.py — 미국 포트폴리오 엔진 (V7 PLUS)
# -------------------------------------------------------------
# 특징:
#   • 최대 보유종목 제한
#   • 총 노출(exposure) 제한
#   • 시장 레짐 기반 자동 제한
#   • 평가손익(PnL) 실시간 계산
#   • 한국 포트폴리오 엔진과 동일한 직관적 구조
# =============================================================

import time
from datetime import datetime


class USPortfolioPLUS_V7:
    def __init__(
        self,
        logger=None,
        max_positions=3,          # 최대 보유 종목
        max_exposure_pct=0.40,    # 총자산 대비 최대 투자비율
        initial_equity=100000,    # 초기 자산 기준
    ):
        self.logger = logger

        self.max_positions = max_positions
        self.max_exposure_pct = max_exposure_pct
        self.equity = initial_equity

        # positions[symbol] = {qty, entry, last_price, timestamp}
        self.positions = {}

        if logger:
            logger.info(
                f"[INIT] USPortfolioPLUS_V7 loaded "
                f"(max_pos={max_positions}, exposure={max_exposure_pct*100:.1f}%)"
            )

    # ---------------------------------------------------------
    # 총 평가금액
    # ---------------------------------------------------------
    def total_exposure_value(self):
        total = 0
        for sym, pos in self.positions.items():
            price = pos.get("last_price", pos["entry"])
            total += price * pos["qty"]
        return total

    # ---------------------------------------------------------
    # 총 노출 비율
    # ---------------------------------------------------------
    def exposure_ratio(self):
        exp = self.total_exposure_value()
        return exp / self.equity

    # ---------------------------------------------------------
    # 신규 진입 가능 여부
    # ---------------------------------------------------------
    def can_enter(self, symbol, price, regime):

        # BEAR/CRASH에서는 신규 진입 억제
        if regime in ["BEAR", "CRASH"]:
            if self.logger:
                self.logger.info(f"[PORT] {regime} → 신규 진입 제한")
            return False

        # 이미 보유 중이면 X
        if symbol in self.positions:
            return False

        # 최대 종목수 초과
        if len(self.positions) >= self.max_positions:
            if self.logger:
                self.logger.info("[PORT] 진입 불가: 최대 포지션 초과")
            return False

        # 총 노출 한도 초과
        future_value = self.total_exposure_value() + (price * 1)
        if (future_value / self.equity) > self.max_exposure_pct:
            if self.logger:
                self.logger.info("[PORT] 노출 한도 초과로 진입 제한")
            return False

        return True

    # ---------------------------------------------------------
    # 포지션 추가
    # ---------------------------------------------------------
    def add_position(self, symbol, price, qty=1):
        if symbol in self.positions:
            return

        self.positions[symbol] = {
            "qty": qty,
            "entry": price,
            "last_price": price,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

        if self.logger:
            self.logger.info(
                f"[PORT] ADD {symbol} qty={qty} entry={price:.2f}"
            )

    # ---------------------------------------------------------
    # 포지션 제거
    # ---------------------------------------------------------
    def remove_position(self, symbol, price):
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]
        entry = pos["entry"]
        qty = pos["qty"]

        pnl = (price - entry) / entry * 100

        if self.logger:
            self.logger.info(
                f"[PORT] REMOVE {symbol} qty={qty} entry={entry:.2f} "
                f"exit={price:.2f} pnl={pnl:.2f}%"
            )

        del self.positions[symbol]

    # ---------------------------------------------------------
    # 시장가 update (평가금액 반영)
    # ---------------------------------------------------------
    def update_market(self, market_data):
        for sym in list(self.positions.keys()):
            if sym in market_data:
                self.positions[sym]["last_price"] = market_data[sym]["price"]

    # ---------------------------------------------------------
    # 포트 요약
    # ---------------------------------------------------------
    def summary(self):
        exp = self.total_exposure_value()
        ratio = exp / self.equity

        return {
            "positions": len(self.positions),
            "exposure": exp,
            "exposure_ratio": ratio,
            "equity": self.equity
        }
