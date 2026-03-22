"""
broker_alpaca_v9.py
V9 PLUS — Alpaca Broker Engine
기관급 미국주식 거래 전용 브로커 모듈
"""

import time
import traceback
from datetime import datetime

from utils_v9 import safe_log


class AlpacaBrokerV9:
    """
    Alpaca REST API 기반 주문 엔진
    - SIM / LIVE 자동 지원
    - 시장가 + 지정가 하이브리드 주문
    - 재시도 및 네트워크 장애 복구
    """

    def __init__(self, api):
        """
        api: Alpaca API 객체 (REST)
        """
        self.api = api

        # 페이퍼 계정인지 실전인지 자동 감지
        account = self.api.get_account()
        self.is_live = not account.account_number.startswith("PA")
        safe_log(f"[BROKER] Alpaca 연결됨 | LIVE={self.is_live}")

        # 주문 실패 재시도 횟수
        self.max_retries = 5

    # ----------------------------------------------------------------------
    # 내부 유틸
    # ----------------------------------------------------------------------
    def _retry_wrapper(self, func, *args, **kwargs):
        """네트워크 오류 보호 + 재시도 처리"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                safe_log(f"[BROKER-RETRY] 재시도({attempt+1}) 오류: {e}")
                time.sleep(0.3)
        return None

    # ----------------------------------------------------------------------
    # 매수 주문
    # ----------------------------------------------------------------------
    def buy(self, symbol, qty, limit_price=None):
        """
        시장가 / 지정가 하이브리드 매수
        """
        safe_log(f"[BUY] 주문 요청: {symbol}, qty={qty}, limit={limit_price}")

        try:
            if limit_price:
                order = self._retry_wrapper(
                    self.api.submit_order,
                    symbol=symbol,
                    qty=qty,
                    side='buy',
                    type='limit',
                    limit_price=round(limit_price, 2),
                    time_in_force='gtc'
                )
            else:
                order = self._retry_wrapper(
                    self.api.submit_order,
                    symbol=symbol,
                    qty=qty,
                    side='buy',
                    type='market',
                    time_in_force='day'
                )

            if order:
                safe_log(f"[BUY] 성공 → id={order.id}")
                return order.id
            else:
                safe_log(f"[BUY] 실패 → {symbol}")
                return None

        except Exception as e:
            safe_log(f"[BUY-ERR] {symbol}: {e}")
            return None

    # ----------------------------------------------------------------------
    # 매도 주문
    # ----------------------------------------------------------------------
    def sell(self, symbol, qty, limit_price=None):
        """
        시장가 / 지정가 하이브리드 매도
        """
        safe_log(f"[SELL] 주문 요청: {symbol}, qty={qty}, limit={limit_price}")

        try:
            if limit_price:
                order = self._retry_wrapper(
                    self.api.submit_order,
                    symbol=symbol,
                    qty=qty,
                    side='sell',
                    type='limit',
                    limit_price=round(limit_price, 2),
                    time_in_force='gtc'
                )
            else:
                order = self._retry_wrapper(
                    self.api.submit_order,
                    symbol=symbol,
                    qty=qty,
                    side='sell',
                    type='market',
                    time_in_force='day'
                )

            if order:
                safe_log(f"[SELL] 성공 → id={order.id}")
                return order.id
            else:
                safe_log(f"[SELL] 실패 → {symbol}")
                return None

        except Exception as e:
            safe_log(f"[SELL-ERR] {symbol}: {e}")
            return None

    # ----------------------------------------------------------------------
    # 포지션 리스트
    # ----------------------------------------------------------------------
    def list_positions(self):
        """전체 포지션 반환"""
        try:
            positions = self._retry_wrapper(self.api.list_positions)
            return positions if positions else []
        except:
            return []

    # ----------------------------------------------------------------------
    # 특정 종목 포지션 조회
    # ----------------------------------------------------------------------
    def get_position(self, symbol):
        """
        포지션 객체 또는 None 반환
        """
        try:
            return self._retry_wrapper(self.api.get_position, symbol)
        except Exception:
            return None

    # ----------------------------------------------------------------------
    # 매수 가능 금액 조회
    # ----------------------------------------------------------------------
    def get_buying_power(self):
        try:
            account = self._retry_wrapper(self.api.get_account)
            if account:
                return float(account.buying_power)
            return 0.0
        except:
            return 0.0

    # ----------------------------------------------------------------------
    # 잔고 조회
    # ----------------------------------------------------------------------
    def get_cash(self):
        try:
            account = self._retry_wrapper(self.api.get_account)
            if account:
                return float(account.cash)
        except:
            pass
        return 0.0

    # ----------------------------------------------------------------------
    # 주문 취소
    # ----------------------------------------------------------------------
    def cancel(self, order_id):
        try:
            self._retry_wrapper(self.api.cancel_order, order_id)
            safe_log(f"[CANCEL] 주문 취소됨 → {order_id}")
            return True
        except Exception as e:
            safe_log(f"[CANCEL-ERR] {order_id}: {e}")
            return False
