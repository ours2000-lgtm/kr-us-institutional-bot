# ================================================================
# portfolio_engine_v9.py
# - V9 PLUS 포트폴리오 관리 엔진
# - 한국/미국 공통 구조
# ================================================================

import logging
from datetime import datetime

class PortfolioEngineV9:
    """
    V9 PLUS 포트폴리오 엔진
    - 현재 보유 종목 상태 점검
    - 목표 비중 계산
    - 리스크 관리 기반 포트폴리오 조절
    """

    def __init__(self, max_positions=3, max_risk=0.25):
        """
        :param max_positions: 최대 동시 보유 종목 수
        :param max_risk: 전체 자산 대비 1회 진입 허용 위험도
        """
        self.max_positions = max_positions
        self.max_risk = max_risk
        self.positions = {}  # {symbol: {"qty": int, "avg_price": float}}
        self.logger = logging.getLogger("PORTFOLIO_V9")

    # ------------------------------------------------------------
    # 포지션 업데이트
    # ------------------------------------------------------------
    def update_position(self, symbol, qty, avg_price):
        self.positions[symbol] = {"qty": qty, "avg_price": avg_price}
        self.logger.info(f"[PORT] 포지션 업데이트: {symbol} qty={qty} avg={avg_price}")

    # ------------------------------------------------------------
    # 포지션 제거
    # ------------------------------------------------------------
    def remove_position(self, symbol):
        if symbol in self.positions:
            del self.positions[symbol]
            self.logger.info(f"[PORT] 포지션 제거: {symbol}")

    # ------------------------------------------------------------
    # 진입 가능한지 체크
    # ------------------------------------------------------------
    def can_enter(self):
        return len(self.positions) < self.max_positions

    # ------------------------------------------------------------
    # 포트폴리오 내의 전체 평가액 계산
    # ------------------------------------------------------------
    def total_value(self, price_feed):
        total = 0.0
        for symbol, pos in self.positions.items():
            if symbol in price_feed:
                total += pos["qty"] * price_feed[symbol]
        return total

    # ------------------------------------------------------------
    # 단일 종목 진입 허용 금액 계산
    # ------------------------------------------------------------
    def position_size(self, account_balance):
        return account_balance * self.max_risk

    # ------------------------------------------------------------
    # 현재 보유 종목 수
    # ------------------------------------------------------------
    def count(self):
        return len(self.positions)

    # ------------------------------------------------------------
    # 전체 포지션 정보 반환
    # ------------------------------------------------------------
    def snapshot(self):
        return self.positions.copy()
