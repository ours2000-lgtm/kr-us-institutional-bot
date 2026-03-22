# ======================================================================
# executor_engine_v8.py — V8 PLUS Execution Engine (Final Version)
# ======================================================================
# 기능 요약:
#   ✔ TP +2.5% / SL -0.7% 자동 반영
#   ✔ 강제청산 (KR 15:10 / US 05:50)
#   ✔ 포트폴리오 리스크 체크
#   ✔ 레짐 기반 출구 (약세 전환 시 보호)
#   ✔ 브로커(KR/US) 통합
#   ✔ MetaStrategy에서 호출되어 최종 매수/매도 트리거 처리
# ======================================================================

from datetime import datetime
from utils_v8 import safe_log
from config_loader_v8 import load_config

CONFIG = load_config()


class ExecutorEngineV8:
    """
    최종 매수/매도 실행 엔진 (한국/미국 공통)
    """

    def __init__(self, market, portfolio, broker):
        self.market = market.upper()
        self.portfolio = portfolio
        self.broker = broker

        # TP/SL 기준
        self.tp = CONFIG.get("take_profit_percent", 2.5)   # +2.5%
        self.sl = CONFIG.get("stop_loss_percent", -0.7)    # -0.7%

        # 강제 청산 시각
        self.force_exit_kr = CONFIG.get("force_exit_kr", "15:10:00")
        self.force_exit_us = CONFIG.get("force_exit_us", "05:50:00")

        safe_log(f"[Executor V8] 초기화 완료 (TP={self.tp}%, SL={self.sl}%)")

    # ==================================================================
    # 시간 기반 강제 청산
    # ==================================================================
    def _force_exit_time(self):
        now = datetime.now().strftime("%H:%M:%S")

        if self.market == "KR" and now >= self.force_exit_kr:
            return True

        if self.market == "US" and now >= self.force_exit_us:
            return True

        return False

    # ==================================================================
    # 매수 실행
    # ==================================================================
    def execute_buy(self, symbol, price):
        qty = self.portfolio.calculate_position_size(symbol)

        result = self.broker.buy(symbol, qty)

        if result["status"] != "ERROR":
            self.portfolio.add_position(symbol, price, qty)
            safe_log(f"[BUY EXECUTED] {symbol} @ {price} (qty={qty})")
            return True

        safe_log(f"[BUY FAILED] {symbol}")
        return False

    # ==================================================================
    # 매도 실행
    # ==================================================================
    def execute_sell(self, symbol, price):
        pos = self.portfolio.positions.get(symbol)
        if not pos:
            return False

        qty = pos["qty"]

        result = self.broker.sell(symbol, qty)

        if result["status"] != "ERROR":
            self.portfolio.close_position(symbol, price)
            safe_log(f"[SELL EXECUTED] {symbol} @ {price}")
            return True

        safe_log(f"[SELL FAILED] {symbol}")
        return False

    # ==================================================================
    # 가격 업데이트 및 TP/SL 체크
    # ==================================================================
    def update(self, symbol, price, regime="NEUTRAL"):
        if not self.portfolio.has_position(symbol):
            return

        pos = self.portfolio.positions[symbol]
        entry = pos["entry"]

        pnl_rate = (price - entry) / entry * 100

        # PnL 기록 업데이트
        self.portfolio.update_pnl(symbol, price)

        # --------------------------------------------------------------
        # 1) STOP LOSS — -0.7%
        # --------------------------------------------------------------
        if pnl_rate <= self.sl:
            safe_log(f"[STOP LOSS] {symbol} ({pnl_rate:.2f}%)")
            self.execute_sell(symbol, price)
            return

        # --------------------------------------------------------------
        # 2) TAKE PROFIT — +2.5%
        # --------------------------------------------------------------
        if pnl_rate >= self.tp:
            safe_log(f"[TAKE PROFIT] {symbol} ({pnl_rate:.2f}%)")
            self.execute_sell(symbol, price)
            return

        # --------------------------------------------------------------
        # 3) 약세장(BEAR) — 강제 보호 청산
        # --------------------------------------------------------------
        if regime == "BEAR":
            safe_log(f"[REGIME EXIT] {symbol} — 약세장 전환 보호 청산")
            self.execute_sell(symbol, price)
            return

        # --------------------------------------------------------------
        # 4) 포트폴리오 강제 리스크 보호
        # --------------------------------------------------------------
        if self.portfolio.violate_risk(symbol):
            safe_log(f"[PORTFOLIO RISK EXIT] {symbol}")
            self.execute_sell(symbol, price)
            return

        # --------------------------------------------------------------
        # 5) 최대 보유시간 초과
        # --------------------------------------------------------------
        if self.portfolio.exceed_holding_time(symbol):
            safe_log(f"[TIME EXIT] {symbol} — 최대 보유시간 초과")
            self.execute_sell(symbol, price)
            return

