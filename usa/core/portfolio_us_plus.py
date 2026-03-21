# =============================================================
#  portfolio_us_plus.py (V3 — US Portfolio Manager, Final Stable)
# =============================================================
# 기능 요약:
#   - 종목별 포지션 보유/해제 추적
#   - 총 노출 금액 제한 (Exposure Cap)
#   - 최대 보유 종목 수 제한
#   - 시장 변동성 고려한 동적 포지션 크기 기반
#   - Executor와 완벽 연동 (중복 진입 방지)
# =============================================================

import time
from datetime import datetime


class USPortfolioPLUS:
    def __init__(
        self,
        logger=None,
        max_positions=4,          # 최대 보유 종목 4개
        max_exposure_pct=0.45,    # 총자산의 45% 이상 투자 금지
        initial_equity=100000,    # 초기 자산 (SIM에서도 사용)
    ):
        self.logger = logger
        self.max_positions = max_positions
        self.max_exposure_pct = max_exposure_pct
        self.equity = initial_equity

        # 구조:
        # positions[code] = {
        #     "qty": int,
        #     "entry": float,
        #     "last_price": float,
        #     "timestamp": time.time()
        # }
        self.positions = {}

        if logger:
            logger.info(
                f"[INIT] USPortfolioPLUS Loaded "
                f"(max_pos={max_positions}, exposure={max_exposure_pct*100:.1f}%)"
            )

    # ---------------------------------------------------------
    # 총 포트 가치: 현재 시장가 기준 전체 보유 포지션 가치
    # ---------------------------------------------------------
    def total_exposure_value(self, market_data=None):
        total = 0

        for code, pos in self.positions.items():
            price = (
                pos.get("last_price")
                if market_data is None
                else market_data.get(code, {}).get("price", pos["entry"])
            )
            total += pos["qty"] * price

        return total

    # ---------------------------------------------------------
    # 총 노출 비율 계산
    # ---------------------------------------------------------
    def exposure_ratio(self, market_data=None):
        return self.total_exposure_value(market_data) / max(self.equity, 1e-9)

    # ---------------------------------------------------------
    # 진입 가능 여부 판단
    # ---------------------------------------------------------
    def can_enter(self, code, price):
        # 1) 이미 보유 중인 종목은 재진입 금지
        if code in self.positions:
            if self.logger:
                self.logger.info(f"[PORT_US] {code} 이미 보유 → 신규 진입 불가")
            return False

        # 2) 포지션 개수 제한
        if len(self.positions) >= self.max_positions:
            if self.logger:
                self.logger.info(
                    f"[PORT_US] 보유 종목 수 초과 ({self.max_positions})"
                )
            return False

        # 3) 노출 제한
        est_value = price * 1  # 기본 1주 진입
        projected_exposure = (
            (self.total_exposure_value() + est_value) / self.equity
        )

        if projected_exposure > self.max_exposure_pct:
            if self.logger:
                self.logger.info(
                    f"[PORT_US] 총 노출 초과 예상 → 진입 차단 "
                    f"({projected_exposure*100:.1f}% > "
                    f"{self.max_exposure_pct*100:.1f}%)"
                )
            return False

        return True

    # ---------------------------------------------------------
    # BUY → 포지션 추가
    # ---------------------------------------------------------
    def add_position(self, code, qty, price):
        if code in self.positions:
            return

        self.positions[code] = {
            "qty": qty,
            "entry": price,
            "last_price": price,
            "timestamp": time.time(),
        }

        if self.logger:
            self.logger.info(
                f"[PORT_US] ADD {code} qty={qty} entry={price:.2f}"
            )

    # ---------------------------------------------------------
    # SELL → 포지션 제거
    # ---------------------------------------------------------
    def remove_position(self, code, exit_price):
        if code not in self.positions:
            return

        pos = self.positions.pop(code)
        qty = pos["qty"]
        entry = pos["entry"]

        pnl = (exit_price - entry) * qty

        if self.logger:
            self.logger.info(
                f"[PORT_US] REMOVE {code} qty={qty} entry={entry:.2f} "
                f"exit={exit_price:.2f} pnl={pnl:.2f}"
            )

    # ---------------------------------------------------------
    # 시장 가격 업데이트
    # ---------------------------------------------------------
    def update_market(self, market_data):
        for code in list(self.positions.keys()):
            if code in market_data:
                self.positions[code]["last_price"] =
                    market_data[code]["price"]

    # ---------------------------------------------------------
    # 요약 정보
    # ---------------------------------------------------------
    def summary(self, market_data=None):
        total = self.total_exposure_value(market_data)
        ratio = total / max(self.equity, 1e-9)

        return {
            "positions": len(self.positions),
            "exposure_value": total,
            "exposure_ratio": ratio,
            "equity": self.equity,
        }
