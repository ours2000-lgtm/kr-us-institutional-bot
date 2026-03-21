# =============================================================
# portfolio_us_v7_plus.py — 미국 포트폴리오 엔진 (V7 PLUS)
# -------------------------------------------------------------
# 기능:
#   • 최대 보유 종목 수 제한 (Max Positions)
#   • 총 투자 노출도 제한 (Exposure Cap)
#   • 변동성 기반 동적 포지션 크기 (Volatility-based sizing)
#   • 중복 진입 완전 차단 (Executor와 연동)
#   • 실시간 PnL 업데이트 / 포트 가치 계산
#   • 위험 레짐(BEAR/CRASH)에서 자동 축소
# =============================================================

import time
from datetime import datetime


class USPortfolio_V7Plus:
    def __init__(
        self,
        logger=None,
        max_positions=4,            # 최대 4종목 보유
        max_exposure_pct=0.45,      # 총 자산의 45% 이상 투자 금지
        initial_equity=100000,      # 기준 자산
    ):
        self.logger = logger
        self.max_positions = max_positions
        self.max_exposure_pct = max_exposure_pct
        self.equity = initial_equity

        # 포지션 구조
        self.positions = {}  
        # {
        #   "AAPL": {
        #       "qty": 1,
        #       "entry": 158.2,
        #       "last": 160.0,
        #       "time": timestamp
        #   }
        # }

        if self.logger:
            self.logger.info(
                f"[INIT] USPortfolio_V7Plus (max={max_positions}, exposure={max_exposure_pct*100:.1f}%)"
            )

    # ---------------------------------------------------------
    # 실시간 가격 업데이트
    # ---------------------------------------------------------
    def update_market(self, market_data):
        for code in list(self.positions.keys()):
            if code in market_data:
                self.positions[code]["last"] = market_data[code]["price"]

    # ---------------------------------------------------------
    # 전체 포트 가치 계산
    # ---------------------------------------------------------
    def total_exposure_value(self):
        total = 0
        for code, pos in self.positions.items():
            price = pos.get("last", pos["entry"])
            total += price * pos["qty"]
        return total

    # ---------------------------------------------------------
    # 총 노출 비율 (Exposure Ratio)
    # ---------------------------------------------------------
    def exposure_ratio(self):
        return self.total_exposure_value() / max(self.equity, 1e-9)

    # ---------------------------------------------------------
    # 변동성 기반 주문 크기 계산 (미국 시장용)
    # ---------------------------------------------------------
    def sizing(self, vol_level):
        """
        vol_level: NQ/QQQ 기반 변동성 (0~5 이상)
        변동성이 크면 qty ↓ / 변동성 낮으면 qty ↑
        """
        if vol_level < 1.0:
            return 2    # 안정 → 2주
        if vol_level < 2.0:
            return 1    # 보통 → 1주
        return 1        # 고변동성 → 1주 고정

    # ---------------------------------------------------------
    # 신규 진입 가능 여부 판단
    # ---------------------------------------------------------
    def can_enter(self, code, price, vol_level=1.0, regime="NORMAL"):
        # 중복 진입 차단
        if code in self.positions:
            return False

        # 포지션 개수 제한
        if len(self.positions) >= self.max_positions:
            if self.logger:
                self.logger.info("[PORT] 진입 제한: 보유종목 초과")
            return False

        # 리스크 높은 레짐 → 진입 더 보수적
        if regime in ["BEAR", "CRASH"]:
            if self.logger:
                self.logger.info(f"[PORT] BEAR/CRASH → 신규 진입 금지 ({code})")
            return False

        # 총 노출 제한
        qty = self.sizing(vol_level)
        est_value = price * qty

        future_exposure = (self.total_exposure_value() + est_value) / self.equity
        if future_exposure > self.max_exposure_pct:
            if self.logger:
                self.logger.info(
                    f"[PORT] 노출도 초과 → {future_exposure*100:.1f}% > {self.max_exposure_pct*100:.1f}%"
                )
            return False

        return True

    # ---------------------------------------------------------
    # 신규 포지션 추가
    # ---------------------------------------------------------
    def add(self, code, price, vol_level=1.0):
        qty = self.sizing(vol_level)

        self.positions[code] = {
            "qty": qty,
            "entry": price,
            "last": price,
            "time": time.time(),
        }

        if self.logger:
            self.logger.info(
                f"[PORT] ADD {code} qty={qty} entry={price:.2f}"
            )

    # ---------------------------------------------------------
    # 포지션 제거
    # ---------------------------------------------------------
    def remove(self, code, exit_price):
        if code not in self.positions:
            return

        pos = self.positions[code]
        qty = pos["qty"]
        entry = pos["entry"]

        pnl = (exit_price - entry) / entry * 100

        if self.logger:
            self.logger.info(
                f"[PORT] REMOVE {code} qty={qty} exit={exit_price:.2f} PnL={pnl:.2f}%"
            )

        del self.positions[code]

    # ---------------------------------------------------------
    # 전체 요약
    # ---------------------------------------------------------
    def summary(self):
        return {
            "positions": len(self.positions),
            "exposure_value": self.total_exposure_value(),
            "exposure_ratio": self.exposure_ratio(),
            "equity": self.equity,
            "details": self.positions
        }
