# ======================================================================
# executor_engine_v9.py
# ----------------------------------------------------------------------
#  V9 Executor Engine (강세/약세/횡보 + 레짐 기반 자동매매 실행 엔진)
# ======================================================================

import traceback
from datetime import datetime

from utils_v8 import safe_log


class ExecutorEngineV9:

    def __init__(self, broker, config, portfolio, meta_engine):
        self.broker = broker
        self.config = config
        self.portfolio = portfolio
        self.meta = meta_engine

        self.market = config.get("ENGINE", {}).get("market", "KR")

        # 가격 기반 Exit 조건
        self.take_profit = 0.025   # +2.5%
        self.stop_loss = -0.007    # -0.7%

        safe_log("[Executor V9] 자동매매 실행엔진 초기화 완료")

    # ==================================================================
    # 강제 청산 시간
    # ==================================================================
    def force_exit_time(self):
        now = datetime.now().strftime("%H:%M:%S")

        if self.market == "KR":
            return now >= "15:10:00"

        if self.market == "US":
            return now >= "05:50:00"

        return False

    # ==================================================================
    # 가격 기반 Exit
    # ==================================================================
    def price_exit(self, symbol, price):
        pos = self.portfolio.get_position(symbol)
        if not pos:
            return False

        pnl = (price - pos["entry"]) / pos["entry"]

        if pnl >= self.take_profit:
            safe_log(f"[TP] {symbol} +{pnl*100:.2f}% → 익절")
            return True

        if pnl <= self.stop_loss:
            safe_log(f"[SL] {symbol} {pnl*100:.2f}% → 손절")
            return True

        return False

    # ==================================================================
    # 고급 Exit (구조 + 오더플로우 + 엔진별 조건)
    # ==================================================================
    def advanced_exit(self, symbol, price, structure, flow, regime):
        st = structure or {}
        fl = flow or {}

        # 공통: 유동성 위험
        if fl.get("liquidity_void"):
            safe_log(f"[EXIT] {symbol} 유동성 VOID")
            return True

        # 공통: 스프레드 이상
        if fl.get("spread", 0) > 0.012:
            safe_log(f"[EXIT] {symbol} 스프레드 비정상")
            return True

        # --------------------------------------------------------------
        # BULL 전용 Exit
        # --------------------------------------------------------------
        if regime == "BULL":
            # 추세 반전
            if st.get("mtf_trend", 0) < 0:
                safe_log(f"[EXIT] {symbol} BULL → 추세 반전")
                return True

            # VWAP 하락 이탈
            if st.get("price", 0) < st.get("vwap", 0):
                safe_log(f"[EXIT] {symbol} BULL → VWAP 이탈")
                return True

        # --------------------------------------------------------------
        # BEAR 전용 Exit
        # --------------------------------------------------------------
        if regime == "BEAR":
            # ORB 하방 이탈
            if st.get("orb_break_down"):
                safe_log(f"[EXIT] {symbol} BEAR → ORB 붕괴")
                return True

            # Orderflow 급악화
            if fl.get("quality", 0) < 0.20:
                safe_log(f"[EXIT] {symbol} BEAR → orderflow 악화")
                return True

        # --------------------------------------------------------------
        # SIDEWAYS 전용 Exit
        # --------------------------------------------------------------
        if regime == "SIDE":
            # Range 상단/하단 돌파 → 범위 이탈
            box_low = st.get("range_low")
            box_high = st.get("range_high")

            if box_low and box_high:
                if price > box_high * 1.01:
                    safe_log(f"[EXIT] {symbol} SIDE → 박스 상단 돌파")
                    return True
                if price < box_low * 0.99:
                    safe_log(f"[EXIT] {symbol} SIDE → 박스 하단 붕괴")
                    return True

        return False

    # ==================================================================
    # 매수
    # ==================================================================
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

    # ==================================================================
    # 매도
    # ==================================================================
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

    # ==================================================================
    # 최종 실행 루프 호출
    # ==================================================================
    def process(self, symbol, tick, structure, flow, regime):

        price = tick.get("price")

        # 1) 보유 중인 종목 EXIT 체크
        if self.portfolio.has_position(symbol):

            # 시간 기반 청산
            if self.force_exit_time():
                self.execute_sell(symbol, price)
                return

            # 가격 기반 청산
            if self.price_exit(symbol, price):
                self.execute_sell(symbol, price)
                return

            # 고급 Exit (구조/오더플로우/레짐)
            if self.advanced_exit(symbol, price, structure, flow, regime):
                self.execute_sell(symbol, price)
                return

            return  # 보유 상태에서는 BUY 금지

        # 2) 신규 진입 로직
        # (메타 엔진 + 레짐 기반 전략 결과)
        signal = self.meta.generate(symbol, tick, structure, flow, regime)

        if signal != "BUY":
            return

        # 포트폴리오 제한 체크
        if not self.portfolio.can_add_position():
            return

        # 매수 실행
        self.execute_buy(symbol, price)
