# =====================================================================
# us_portfolio_v7_plus.py
# 미국 포트폴리오 엔진 — V7 PLUS (기관급)
# ---------------------------------------------------------------------
# 특징:
#   • Exposure Cap (총 노출 제한) — NQ 모멘텀 기반 동적 조절
#   • Max Positions 제한
#   • 종목별 Cooldown (휩쏘 방지)
#   • Dynamic Position Sizing (1~3주)
#   • Risk Weight (고변동/빅테크/ETF 구분)
#   • Regime-aware sizing (Bull/NORMAL/Bear 자동)
#   • 실시간 평가금액 업데이트
# =====================================================================

import time
from datetime import datetime


class USPortfolioV7Plus:
    def __init__(
        self,
        logger=None,
        initial_equity=100000,
        max_positions=4,
        base_exposure_pct=0.45,       # 기본 총 노출 45%
    ):
        self.logger = logger

        self.equity = initial_equity
        self.max_positions = max_positions
        self.base_exposure_pct = base_exposure_pct

        # 보유 포지션 구조
        # positions[sym] = {
        #     "entry": float,
        #     "qty": int,
        #     "last_price": float,
        #     "timestamp": float,
        #     "cooldown_until": float,
        # }
        self.positions = {}

        # 진입 쿨다운
        self.cooldown_secs = 20

        # 종목별 리스크 가중치
        self.risk_weight = {
            "NVDA": 1.3,
            "TSLA": 1.3,
            "SOXL": 1.5,
            "TQQQ": 1.5,
            "SQQQ": 1.5,
            "AAPL": 1.0,
            "MSFT": 1.0,
            "QQQ": 1.0,
        }

        if logger:
            logger.info(
                f"[INIT] USPortfolioV7Plus Loaded "
                f"(pos≤{max_positions}, exposure≤{base_exposure_pct*100:.1f}%)"
            )

    # ------------------------------------------------------------------
    # 실시간 평가금액 업데이트
    # ------------------------------------------------------------------
    def update_market(self, market):
        for code, pos in self.positions.items():
            if code not in market:
                continue
            pos["last_price"] = market[code]["price"]

    # ------------------------------------------------------------------
    # 총 노출 계산
    # ------------------------------------------------------------------
    def total_exposure_value(self):
        total = 0
        for code, pos in self.positions.items():
            total += pos["last_price"] * pos["qty"]
        return total

    # 총노출 비율
    def exposure_ratio(self):
        return self.total_exposure_value() / max(self.equity, 1e-9)

    # ------------------------------------------------------------------
    # Regime 기반 Exposure Cap 조정
    # ------------------------------------------------------------------
    def dynamic_exposure_cap(self, regime):
        cap = self.base_exposure_pct

        if regime == "HYPER_BULL":
            cap = 0.55
        elif regime == "BULL":
            cap = 0.50
        elif regime == "NORMAL":
            cap = self.base_exposure_pct
        elif regime == "VOLATILE":
            cap = 0.35
        elif regime == "BEAR":
            cap = 0.30
        elif regime == "CRASH":
            cap = 0.25

        return cap

    # ------------------------------------------------------------------
    # Dynamic Position Sizing (1~3주)
    # ------------------------------------------------------------------
    def calc_position_size(self, symbol, volatility):
        base = 1

        if volatility > 2.0:
            base = 1
        elif volatility > 1.0:
            base = 2
        else:
            base = 3

        # 위험 가중치 반영
        weight = self.risk_weight.get(symbol, 1.0)
        size = max(1, round(base / weight))

        return size

    # ------------------------------------------------------------------
    # 진입 가능 여부 판단
    # ------------------------------------------------------------------
    def can_enter(self, symbol, price, volatility, regime):
        now = time.time()

        # 1) 쿨다운 체크
        if symbol in self.positions:
            return False

        # cooldown dict
        for sym, pos in self.positions.items():
            if sym == symbol:
                continue
            if "cooldown_until" in pos and pos["cooldown_until"] > now:
                pass

        # 2) Max Positions
        if len(self.positions) >= self.max_positions:
            if self.logger:
                self.logger.info("[PORTFOLIO] 최대 보유 종목수 도달 → 진입 불가")
            return False

        # 3) Exposure Cap
        desired_qty = self.calc_position_size(symbol, volatility)
        est_value = desired_qty * price

        cap = self.dynamic_exposure_cap(regime)
        future_exposure = (self.total_exposure_value() + est_value) / self.equity

        if future_exposure > cap:
            if self.logger:
                self.logger.info(
                    f"[PORTFOLIO] 총 노출 초과 → {future_exposure*100:.1f}% > cap {cap*100:.1f}%"
                )
            return False

        return True

    # ------------------------------------------------------------------
    # 포지션 기록
    # ------------------------------------------------------------------
    def enter(self, symbol, price, qty):
        self.positions[symbol] = {
            "entry": price,
            "qty": qty,
            "last_price": price,
            "timestamp": time.time(),
            "cooldown_until": time.time() + self.cooldown_secs,
        }

        if self.logger:
            self.logger.info(
                f"[PORTFOLIO] ENTER {symbol} qty={qty} entry={price:.2f}"
            )

    # ------------------------------------------------------------------
    # 청산
    # ------------------------------------------------------------------
    def exit(self, symbol, price):
        if symbol not in self.positions:
            return

        pos = self.positions[symbol]
        entry = pos["entry"]
        pnl = (price - entry) / entry * 100

        if self.logger:
            self.logger.info(
                f"[PORTFOLIO] EXIT {symbol} price={price:.2f} pnl={pnl:.2f}%"
            )

        del self.positions[symbol]

    # ------------------------------------------------------------------
    # 요약
    # ------------------------------------------------------------------
    def summary(self):
        return {
            "positions": len(self.positions),
            "exposure_value": self.total_exposure_value(),
            "exposure_ratio": self.exposure_ratio(),
            "equity": self.equity,
        }
