"""
executor_engine_v9_plus.py
V9 PLUS — 통합 주문 실행 엔진
한국/미국 공통 구조 (Kiwoom / Alpaca 자동 감지)
"""

import time
import traceback
from datetime import datetime

from utils_v9 import safe_log
from portfolio_engine_v9 import PortfolioEngineV9
from orderflow_v9 import OrderFlowV9   # 정식 클래스명
# 호환용
OrderflowV9 = OrderFlowV9


class ExecutorEngineV9Plus:
    """
    기관급 주문 실행 엔진
    - 시장가/지정가 자동 판단
    - 익절/손절 자동 처리
    - 포트폴리오 기반 포지션 사이징
    - 실패 시 재시도 보호
    """

    def __init__(self, broker, config):
        self.broker = broker
        self.config = config

        self.portfolio = PortfolioEngineV9(broker, config)
        self.orderflow = OrderFlowV9()

        self.max_retries = 5

    # -----------------------------------------------------------
    # BUY (매수)
    # -----------------------------------------------------------
    def execute_buy(self, symbol, signal_strength, price_hint=None):
        try:
            safe_log(f"[BUY] 매수 시작 → {symbol} | strength={signal_strength}")

            qty = self.portfolio.calc_position_size(symbol)
            if qty <= 0:
                safe_log(f"[BUY] 수량 계산 실패 → {symbol}")
                return False

            # 오더플로우 기반 가격 보정
            limit_price = self.orderflow.adjust_buy_price(price_hint)

            # 재시도 루프
            for attempt in range(self.max_retries):
                try:
                    order_id = self.broker.buy(symbol, qty, limit_price)
                    safe_log(f"[BUY] 주문 성공 → {symbol}, qty={qty}, id={order_id}")
                    return True
                except Exception as e:
                    safe_log(f"[BUY-ERR] {symbol} 재시도({attempt+1}) : {e}")
                    time.sleep(0.3)

            safe_log(f"[BUY] 실패: {symbol}")
            return False

        except Exception as e:
            safe_log(f"[BUY-CRIT] {symbol} 치명적 오류: {e}")
            traceback.print_exc()
            return False

    # -----------------------------------------------------------
    # SELL (매도)
    # -----------------------------------------------------------
    def execute_sell(self, symbol, reason=""):
        try:
            pos = self.broker.get_position(symbol)
            if pos is None or pos.qty <= 0:
                safe_log(f"[SELL] 포지션 없음 → {symbol}")
                return False

            qty = pos.qty
            safe_log(f"[SELL] 매도 시작 → {symbol}, qty={qty}, reason={reason}")

            # 매도 가격 보정
            limit_price = self.orderflow.adjust_sell_price(pos.avg_price)

            for attempt in range(self.max_retries):
                try:
                    order_id = self.broker.sell(symbol, qty, limit_price)
                    safe_log(f"[SELL] 완료 → {symbol}, qty={qty}, id={order_id}")
                    return True
                except Exception as e:
                    safe_log(f"[SELL-ERR] {symbol} 재시도({attempt+1}) : {e}")
                    time.sleep(0.3)

            safe_log(f"[SELL] 실패: {symbol}")
            return False

        except Exception as e:
            safe_log(f"[SELL-CRIT] {symbol} 오류: {e}")
            traceback.print_exc()
            return False

    # -----------------------------------------------------------
    # Signal Processing
    # -----------------------------------------------------------
    def process_signal(self, signal):
        """
        signal.type : BUY / SELL / EXIT / HOLD
        signal.symbol
        signal.strength
        """
        try:
            stype = signal.type.upper()
            symbol = signal.symbol

            if stype == "BUY":
                return self.execute_buy(symbol, signal.strength)

            elif stype == "SELL":
                return self.execute_sell(symbol, reason="SELL signal")

            elif stype == "EXIT":
                return self.execute_sell(symbol, reason="EXIT command")

            elif stype == "HOLD":
                return True

            else:
                safe_log(f"[SIGNAL] 알 수 없는 신호: {stype}")
                return False

        except Exception as e:
            safe_log(f"[SIGNAL-ERR] 신호 처리 오류: {e}")
            traceback.print_exc()
            return False

    # -----------------------------------------------------------
    # Market Close — 전체 포지션 정리
    # -----------------------------------------------------------
    def close_all_positions(self):
        safe_log("[CLOSE] 전 종목 포지션 정리 시작…")

        positions = self.broker.list_positions()
        if not positions:
            safe_log("[CLOSE] 포지션 없음")
            return

        for pos in positions:
            try:
                self.execute_sell(pos.symbol, reason="Market Close")
            except:
                pass

        safe_log("[CLOSE] 전체 정리 완료")
