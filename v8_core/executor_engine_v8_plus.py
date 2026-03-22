# ======================================================================
# executor_engine_v8_plus.py — V8 PLUS 주문 엔진 (MASTER BUILD)
# ======================================================================
# 기능:
#   ✔ TP/SL 기반 기본 Exit
#   ✔ ORB Fail / AVWAP Reverse / MTF Reverse / Orderflow 악화 시 Exit
#   ✔ 레짐 기반 포트폴리오 제한
#   ✔ 포트폴리오, ML Gate, 구조엔진, Orderflow 엔진 통합
#   ✔ 강제청산 시간 자동 처리
# ======================================================================

import traceback
from datetime import datetime
from utils_v8 import safe_log


class ExecutorEngineV8Plus:

    def __init__(self, config, broker, portfolio, signal_engine,
                 structure_engine, orderflow_engine, ml_gate, regime_engine):

        self.cfg_exec = config["EXECUTOR"]
        self.cfg_risk = config["RISK"]
        self.schedule = config["MARKET_SCHEDULE"]

        self.broker = broker
        self.portfolio = portfolio
        self.signal = signal_engine
        self.structure = structure_engine
        self.orderflow = orderflow_engine
        self.ml = ml_gate
        self.regime = regime_engine

        self.market = config["ENGINE"]["market"]

        # TP / SL 기준
        self.tp = self.cfg_exec["take_profit"]
        self.sl = self.cfg_exec["stop_loss"]

        safe_log("[Executor V8 PLUS] 초기화 완료")

    # ==================================================================
    # 강제 청산 시간
    # ==================================================================
    def is_force_exit_time(self):
        now = datetime.now().strftime("%H:%M:%S")
        return now >= self.schedule["force_exit"]

    # ==================================================================
    # 가격 기반 TP/SL
    # ==================================================================
    def price_exit(self, symbol, price):
        pos = self.portfolio.get_position(symbol)
        if not pos:
            return False

        entry = pos["entry"]
        pct = (price - entry) / entry

        if pct >= self.tp:
            safe_log(f"[TP] {symbol} +{pct*100:.2f}%")
            return True

        if pct <= self.sl:
            safe_log(f"[SL] {symbol} {pct*100:.2f}%")
            return True

        return False

    # ==================================================================
    # 고급 EXIT 규칙
    # ==================================================================
    def advanced_exit(self, symbol, structure, flow, price):

        # ORB 실패
        if structure.get("orb_up", False) is False and self.structure.orb_complete:
            safe_log(f"[EXIT] {symbol} ORB Fail")
            return True

        # AVWAP 아래로 리버스
        if price < structure.get("avwap", 0):
            safe_log(f"[EXIT] {symbol} AVWAP Breakdown")
            return True

        # MTF 역전
        if structure.get("mtf_trend", 0) < 0:
            safe_log(f"[EXIT] {symbol} MTF Reverse")
            return True

        # 오더플로우 악화
        if flow.get("quality", 0) < 0:
            safe_log(f"[EXIT] {symbol} Orderflow Negative")
            return True

        return False

    # ==================================================================
    # 매수 실행
    # ==================================================================
    def execute_buy(self, symbol, price, regime):

        # ML Gate 확인
        if not self.ml.allow(symbol, "BUY", {"price": price}, {}):
            return

        # 포트폴리오 제한 (레짐 기반)
        if not self.portfolio.can_add_position(regime):
            safe_log(f"[BLOCK] {symbol} → 포트폴리오 한도 초과")
            return

        qty = self.portfolio.calculate_position_size(price)
        order = self.broker.buy(symbol, qty)

        if order.get("status") == "FILLED":
            self.portfolio.add_position(symbol, order["price"], qty)
            safe_log(f"[BUY] {symbol} @ {order['price']}")
        else:
            safe_log(f"[BUY-PENDING] {symbol}")

    # ==================================================================
    # 매도 실행
    # ==================================================================
    def execute_sell(self, symbol, price):
        pos = self.portfolio.get_position(symbol)
        if not pos:
            return

        qty = pos["qty"]
        order = self.broker.sell(symbol, qty)

        if order.get("status") == "FILLED":
            self.portfolio.close_position(symbol, order["price"])
            safe_log(f"[SELL] {symbol} @ {order['price']}")
        else:
            safe_log(f"[SELL-PENDING] {symbol}")

    # ==================================================================
    # 메인 실행 루프 (run 파일에서 symbol마다 호출)
    # ==================================================================
    def process(self, symbol, tick, structure, flow):

        price = tick.get("price", 0)
        regime = self.regime.get_regime()

        # --------------------------------------------------------------
        # 1) 보유 중인 종목 EXIT 먼저 체크
        # --------------------------------------------------------------
        if self.portfolio.has_position(symbol):

            # 강제청산
            if self.is_force_exit_time():
                self.execute_sell(symbol, price)
                return

            # 손익 기반 Exit
            if self.price_exit(symbol, price):
                self.execute_sell(symbol, price)
                return

            # 고급 Exit
            if self.advanced_exit(symbol, structure, flow, price):
                self.execute_sell(symbol, price)
                return

            # 보유시간 초과
            if self.portfolio.exceed_holding_time(symbol):
                self.execute_sell(symbol, price)
                return

            return

        # --------------------------------------------------------------
        # 2) 신규 진입 (BUY)
        # --------------------------------------------------------------
        signal = self.signal.generate(symbol, tick, structure, flow)
        if signal != "BUY":
            return

        # ML Gate / 포트 제한 / 레짐 제한 모두 체크
        self.execute_buy(symbol, price, regime)
