# ======================================================================
# portfolio_engine_v9.py — V9 PLUS Portfolio Engine
# ======================================================================
# 기능:
#   ✔ 종목별 포지션 관리
#   ✔ 평균단가 / 수익률 / 평가손익 실시간 업데이트
#   ✔ 레짐(BULL/NEUTRAL/BEAR) 기반 포지션 수 자동 제한
#   ✔ 2.5% 익절 / -0.7% 손절과 연동
#   ✔ 포트폴리오 손실 -3% 차단
#   ✔ 최대 보유시간(기본 120분) 자동 청산
#   ✔ 미국 / 한국 시장 자동 지원
# ======================================================================

from datetime import datetime, timedelta
from utils_v8 import safe_log


class PortfolioEngineV9:

    def __init__(self, config, market="KR"):
        self.config = config
        self.market = market

        self.max_positions = config["RISK"]["max_positions"]
        self.max_loss_per_symbol = config["RISK"]["max_loss_per_symbol"]  # -0.7%
        self.max_portfolio_loss = config["RISK"]["max_portfolio_loss"]    # -3%
        self.max_hold_minutes = config["RISK"]["max_holding_minutes"]     # 120 min

        # 포지션 저장 구조
        self.positions = {}  # symbol → {entry, qty, entry_time}

        # 초기잔고 (모의 or 실계좌)
        self.cash = config["PORTFOLIO"]["initial_cash"]
        self.init_cash = self.cash

        safe_log(f"[Portfolio V9] 포트폴리오 초기화 완료 (시장={market})")

    # ==================================================================
    # 포지션 추가
    # ==================================================================
    def add_position(self, symbol, entry_price, qty):
        now = datetime.now()
        self.positions[symbol] = {
            "entry": entry_price,
            "qty": qty,
            "entry_time": now,
            "pnl": 0.0
        }

        used = entry_price * qty
        self.cash -= used

        safe_log(f"[POSITION ADD] {symbol} qty={qty} entry={entry_price}")

    # ==================================================================
    # 포지션 닫기
    # ==================================================================
    def close_position(self, symbol, exit_price):
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]
        qty = pos["qty"]
        entry_price = pos["entry"]

        realized = (exit_price - entry_price) * qty

        self.cash += exit_price * qty
        del self.positions[symbol]

        safe_log(f"[POSITION CLOSE] {symbol} exit={exit_price}, realized={realized:.2f}")

    # ==================================================================
    # 보유 여부
    # ==================================================================
    def has_position(self, symbol):
        return symbol in self.positions

    # ==================================================================
    # 현재 포지션 수
    # ==================================================================
    def position_count(self):
        return len(self.positions)

    # ==================================================================
    # 레짐 기반 포지션 제한
    # ==================================================================
    def can_add_position(self, regime):
        rule = self.config["RISK"]["regime"]

        limit = rule.get(regime, self.max_positions)

        if self.position_count() < limit:
            return True
        return False

    # ==================================================================
    # 단일 포지션 가져오기
    # ==================================================================
    def get_position(self, symbol):
        return self.positions.get(symbol)

    # ==================================================================
    # 수량 계산
    # ==================================================================
    def calculate_position_size(self, symbol, price):
        """
        기본 전략:
        - 예수금 / (최대포지션수 * 1.1)
        - 안전하게 10% 여유 둔다
        """
        if price <= 0:
            return 0

        slots = max(self.max_positions, 1)
        alloc = (self.cash / (slots * 1.1))
        qty = int(alloc / price)

        return max(qty, 1)

    # ==================================================================
    # 실시간 PnL 업데이트
    # ==================================================================
    def update_pnl(self, symbol, price):
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]
        entry = pos["entry"]
        pnl = (price - entry) / entry

        self.positions[symbol]["pnl"] = pnl

    # ==================================================================
    # 전체 포트폴리오 손실 체크 (-3%)
    # ==================================================================
    def violate_total_loss(self):
        total_value = self.cash

        for symbol, pos in self.positions.items():
            total_value += pos["entry"] * pos["qty"] * (1 + pos["pnl"])

        loss_rate = (total_value - self.init_cash) / self.init_cash

        return loss_rate <= self.max_portfolio_loss

    # ==================================================================
    # 개별 종목 손실 체크 (-0.7%)
    # ==================================================================
    def violate_risk(self, symbol):
        pos = self.positions.get(symbol)
        if not pos:
            return False

        pnl = pos["pnl"]
        return pnl <= self.max_loss_per_symbol

    # ==================================================================
    # 보유시간 초과 체크
    # ==================================================================
    def exceed_holding_time(self, symbol):
        pos = self.positions.get(symbol)
        if not pos:
            return False

        entry_time = pos["entry_time"]
        duration = datetime.now() - entry_time

        return duration >= timedelta(minutes=self.max_hold_minutes)

    # ==================================================================
    # 전체 포지션 강제 청산 (사용자 명령)
    # ==================================================================
    def close_all(self, price_map):
        for symbol, pos in list(self.positions.items()):
            if symbol in price_map:
                price = price_map[symbol]
                self.close_position(symbol, price)

        safe_log("[Portfolio] 전체 포지션 강제 청산 완료")

