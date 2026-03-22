# ======================================================================
# executor_engine_v9_plus.py
# V9 PLUS 주문 엔진 (KR/US 통합, Alpaca & Kiwoom 자동 지원)
# ======================================================================

import time
import traceback
from datetime import datetime

from utils_v8 import safe_log


class ExecutorEngineV9Plus:
    """
    통합 주문 엔진
    - 익절 +2.5% / 손절 -0.7%
    - ORB 실패 / AVWAP 붕괴 / MTF 반전 / Orderflow 악화 자동 청산
    - 시장(한국/미국)별 강제청산 시간 자동 적용
    - Regime 및 Portfolio 기반 포지션 수 조절
    - Broker(Kiwoom, Alpaca V9) 자동 호환
    """

    def __init__(self, broker, config, portfolio):
        self.broker = broker
        self.config = config

        # 시장 (KR/US)
        self.market = config["ENGINE"]["market"]

        # 가격 익절/손절 기준
        self.take_profit = 0.025   # +2.5%
        self.stop_loss = -0.007    # -0.7%

        # 포트폴리오 엔진
        self.portfolio = portfolio

        safe_log("[Executor V9 PLUS] 주문 엔진 초기화 완료")

    # ------------------------------------------------------------------
    # 강제 청산 시간 체크
    # ------------------------------------------------------------------
    def force_exit_time(self):
        now = datetime.now().strftime("%H:%M:%S")

        force_exit = self.config["SCHEDULE"][self.market]["force_exit"]

        return now >= force_exit

    # ------------------------------------------------------------------
    # 가격 기반 익절/손절
    # ------------------------------------------------------------------
    def price_exit(self, symbol, price):
        pos = self.portfolio.get_position(symbol)
        if not pos:
            return False

        pnl = (price - pos["entry"]) / pos["entry"]

        # 익절
        if pnl >= self.take_profit:
            safe_log(f"[TP HIT] {symbol} +{pnl*100:.2f}% → 익절")
            return True

        # 손절
        if pnl <= self.stop_loss:
            safe_log(f"[SL HIT] {symbol} {pnl*100:.2f}% → 손절")
            return True

        return False

    # ------------------------------------------------------------------
    # 고급 Exit: ORB, AVWAP, MTF, Orderflow
    # ------------------------------------------------------------------
    def advanced_exit(self, symbol, structure, flow):
        st = structure.get(symbol, {})
        fl = flow.get(symbol, {})

        # ORB 하락이탈
        if st.get("orb_fail", False):
            safe_log(f"[EXIT] {symbol} ORB 실패")
            return True

        # AVWAP 아래 이탈
        if st.get("avwap") and st["avwap"] > st.get("price", 0):
            safe_log(f"[EXIT] {symbol} AVWAP 붕괴")
            return True

        # MTF 반전
        if st.get("mtf_score", 0) < 0:
            safe_log(f"[EXIT] {symbol} MTF 약세 전환")
            return True

        # Orderflow 악화
        if fl.get("quality", 1) < 0.25:
            safe_log(f"[EXIT] {symbol} Orderflow 약화")
            return True

        return False

    # ------------------------------------------------------------------
    # 매수 실행
    # ------------------------------------------------------------------
    def execute_buy(self, symbol, price):
        try:
            qty = self.portfolio.calculate_position_size(symbol, price)

            order = self.broker.buy(symbol, qty)

            if order.get("status") == "FILLED":
                self.portfolio.add_position(symbol, order["price"], qty)
                safe_log(f"[BUY FILLED] {symbol} @ {order['price']}")
            else:
                safe_log(f"[BUY PENDING] {symbol}")

        except Exception as e:
            safe_log(f"[BUY ERROR] {e}")
            traceback.print_exc()

    # ------------------------------------------------------------------
    # 매도 실행
    # ------------------------------------------------------------------
    def execute_sell(self, symbol, price):
        try:
            pos = self.portfolio.get_position(symbol)
            qty = pos["qty"]

            order = self.broker.sell(symbol, qty)

            if order.get("status") == "FILLED":
                self.portfolio.close_position(symbol, order["price"])
                safe_log(f"[SELL FILLED] {symbol} @ {order['price']}")
            else:
                safe_log(f"[SELL PENDING] {symbol}")

        except Exception as e:
            safe_log(f"[SELL ERROR] {e}")
            traceback.print_exc()

    # ------------------------------------------------------------------
    # 메인 주문 처리
    # ------------------------------------------------------------------
    def process(self, symbol, signal, tick, structure, flow, regime):

        price = tick.get("price")
        if price is None:
            return

        # ==============================================================
        # 1) 보유 중인 종목: EXIT 먼저 체크
        # ==============================================================
        if self.portfolio.has_position(symbol):

            # 강제 청산 시간
            if self.force_exit_time():
                safe_log(f"[FORCE EXIT] 시장 종료 → {symbol}")
                self.execute_sell(symbol, price)
                return

            # 익절/손절
            if self.price_exit(symbol, price):
                self.execute_sell(symbol, price)
                return

            # ORB/MTF/AVWAP/Orderflow 고급 청산
            if self.advanced_exit(symbol, structure, flow):
                self.execute_sell(symbol, price)
                return

            return  # 보유 중이면 BUY 금지

        # ==============================================================
        # 2) 신규 진입 조건
        # ==============================================================

        # BUY 신호가 아니면 무시
        if signal != "BUY":
            return

        # Regime 기반 포지션 제한
        if not self.portfolio.can_add_position(regime):
            return

        # 매수 실행
        self.execute_buy(symbol, price)
