# ======================================================================
# portfolio_engine_v8.py — V8 PLUS Portfolio & Risk Engine (MASTER BUILD)
# ======================================================================
# 기능:
#   ✔ 포트폴리오(종목별 보유) 관리
#   ✔ Equal Weight 기반 포지션 사이징
#   ✔ 종목별 손익(PnL) 계산
#   ✔ 전체 포트폴리오 리스크 제어
#   ✔ 보유시간 및 레짐 기반 포지션 수 조절
# ======================================================================

from datetime import datetime, timedelta
from utils_v8 import safe_log


class PortfolioEngineV8:
    def __init__(self, config):
        self.cfg_risk = config["RISK"]
        self.cfg_port = config["PORTFOLIO"]

        # 포트폴리오 데이터
        self.positions = {}
        self.realized = 0.0

        # 자본금
        self.initial_cash = self.cfg_port["initial_cash"]
        self.equal_weight = self.cfg_port["equal_weight"]

        safe_log("[PortfolioEngine V8] 초기화 완료")

    # ==================================================================
    # 기본 유틸
    # ==================================================================
    def now(self):
        return datetime.now()

    # ==================================================================
    # 포지션 보유 여부
    # ==================================================================
    def has_position(self, symbol):
        return symbol in self.positions

    def get_position(self, symbol):
        return self.positions.get(symbol)

    # ==================================================================
    # 포지션 사이징
    # ==================================================================
    def calculate_position_size(self, price):
        """Equal Weight 포지션 사이징"""
        if not self.equal_weight:
            return 1

        capital_per_pos = self.initial_cash / max(1, self.cfg_risk["max_positions"])
        qty = max(1, int(capital_per_pos / price))
        return qty

    # ==================================================================
    # 포지션 추가
    # ==================================================================
    def add_position(self, symbol, entry_price, qty):
        self.positions[symbol] = {
            "entry": entry_price,
            "qty": qty,
            "time": self.now(),
            "pnl": 0.0
        }
        safe_log(f"[PORT] {symbol} 포지션 추가 | entry={entry_price}, qty={qty}")

    # ==================================================================
    # 포지션 종료
    # ==================================================================
    def close_position(self, symbol, exit_price):
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]
        entry = pos["entry"]
        qty = pos["qty"]

        pnl = (exit_price - entry) * qty
        self.realized += pnl

        safe_log(f"[PORT] {symbol} 포지션 종료 | exit={exit_price}, pnl={pnl:.2f}")

        del self.positions[symbol]

    # ==================================================================
    # PnL 업데이트
    # ==================================================================
    def update_pnl(self, symbol, price):
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]
        entry = pos["entry"]
        qty = pos["qty"]

        pos["pnl"] = (price - entry) * qty

    # ==================================================================
    # 전체 포트폴리오 PnL
    # ==================================================================
    def total_unrealized_pnl(self):
        total = 0
        for pos in self.positions.values():
            total += pos.get("pnl", 0)
        return total

    def total_pnl_ratio(self):
        capital = self.initial_cash
        total_pnl = (self.realized + self.total_unrealized_pnl()) / capital
        return total_pnl

    # ==================================================================
    # 리스크 체크
    # ==================================================================
    def violate_risk(self, symbol):
        """종목별 손실 및 포트폴리오 전체 손실 체크"""

        # 포트폴리오 전체 손실
        if self.total_pnl_ratio() <= self.cfg_risk["max_portfolio_loss"]:
            safe_log("[RISK] 포트폴리오 전체손실 초과 → 즉시 청산 필요")
            return True

        # 종목별 손실 체크
        pos = self.positions.get(symbol)
        if pos:
            entry = pos["entry"]
            price = entry + pos["pnl"] / pos["qty"]
            pnl_ratio = (price - entry) / entry

            if pnl_ratio <= self.cfg_risk["max_loss_per_symbol"]:
                safe_log(f"[RISK] {symbol} 종목별 손실 초과 → 손절 필요")
                return True

        return False

    # ==================================================================
    # 보유시간 초과 체크
    # ==================================================================
    def exceed_holding_time(self, symbol):
        if symbol not in self.positions:
            return False

        pos = self.positions[symbol]
        elapsed = self.now() - pos["time"]
        minutes = elapsed.total_seconds() / 60

        if minutes >= self.cfg_risk["max_holding_minutes"]:
            safe_log(f"[RISK] {symbol} 보유시간 초과 → 청산 필요")
            return True

        return False

    # ==================================================================
    # 현재 허용 가능한 포지션 수(레짐 기반)
    # ==================================================================
    def allowed_positions_by_regime(self, regime):
        regime_table = self.cfg_risk["regime"]
        return regime_table.get(regime, 1)

    # ==================================================================
    # 포지션 추가 가능 여부
    # ==================================================================
    def can_add_position(self, regime):
        max_allowed = self.allowed_positions_by_regime(regime)
        return len(self.positions) < max_allowed
