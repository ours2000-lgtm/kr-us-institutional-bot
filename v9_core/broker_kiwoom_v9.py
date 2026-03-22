"""
broker_kiwoom_v9.py
V9 PLUS — Kiwoom Broker Engine
한국 주식 자동매매 전용 브로커 모듈
"""

import time
import traceback
from datetime import datetime

from PyQt5.QtCore import QObject, QEventLoop

from utils_v9 import safe_log


class KiwoomBrokerV9(QObject):
    """
    키움증권 OpenAPI+ 기반 주문 엔진
    - 매수/매도
    - 잔고 조회
    - 주문/미체결 조회
    - 재시도 안정성
    """

    def __init__(self, api):
        super().__init__()
        self.api = api
        self._loop = QEventLoop()

        # 재시도 횟수
        self.max_retries = 5

        safe_log("[BROKER-KR] 키움 브로커 초기화 완료")

    # ----------------------------------------------------------------------
    # 내부 유틸
    # ----------------------------------------------------------------------
    def _retry_wrapper(self, func, *args, **kwargs):
        """OpenAPI 명령 호출 재시도 래퍼"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                safe_log(f"[KR-RETRY] 재시도({attempt+1}): {e}")
                time.sleep(0.2)
        return None

    # ----------------------------------------------------------------------
    # 매수
    # ----------------------------------------------------------------------
    def buy(self, code, qty, price=0):
        """
        시장가: price=0
        지정가: price > 0
        """
        try:
            if price == 0:
                ord_type = "03"  # 시장가
            else:
                ord_type = "00"  # 지정가

            safe_log(f"[BUY-KR] {code} qty={qty} price={price}")

            ret = self.api.send_order(
                rqname="buy_order",
                screen_no="0101",
                acc_no=self.api.account,
                order_type=1,  # 신규매수
                code=code,
                qty=qty,
                price=price,
                hoga=ord_type,
                original_no=""
            )

            if ret == 0:
                safe_log(f"[BUY-KR] 성공 → {code}")
                return True
            else:
                safe_log(f"[BUY-KR] 실패 (code={ret}) → {code}")
                return False

        except Exception as e:
            safe_log(f"[BUY-KR-ERR] {code}: {e}")
            return False

    # ----------------------------------------------------------------------
    # 매도
    # ----------------------------------------------------------------------
    def sell(self, code, qty, price=0):
        """
        시장가 or 지정가 매도
        """
        try:
            if price == 0:
                ord_type = "03"
            else:
                ord_type = "00"

            safe_log(f"[SELL-KR] {code} qty={qty} price={price}")

            ret = self.api.send_order(
                rqname="sell_order",
                screen_no="0102",
                acc_no=self.api.account,
                order_type=2,  # 신규매도
                code=code,
                qty=qty,
                price=price,
                hoga=ord_type,
                original_no=""
            )

            if ret == 0:
                safe_log(f"[SELL-KR] 성공 → {code}")
                return True
            else:
                safe_log(f"[SELL-KR] 실패 (code={ret}) → {code}")
                return False

        except Exception as e:
            safe_log(f"[SELL-KR-ERR] {code}: {e}")
            return False

    # ----------------------------------------------------------------------
    # 잔고 조회
    # ----------------------------------------------------------------------
    def get_balance(self):
        """보유 종목 잔고 전체 조회"""
        try:
            self.api.request_balance()

            # 이벤트 응답 대기
            self._loop.exec_()

            return self.api.balance_data

        except Exception as e:
            safe_log(f"[KR-BALANCE-ERR] {e}")
            return {}

    # ----------------------------------------------------------------------
    # 매수 가능 금액
    # ----------------------------------------------------------------------
    def get_cash(self):
        try:
            self.api.request_account_info()
            self._loop.exec_()

            return float(self.api.cash_available)
        except:
            return 0.0

    # ----------------------------------------------------------------------
    # 미체결 조회
    # ----------------------------------------------------------------------
    def get_unfilled_orders(self):
        try:
            self.api.request_unfilled()
            self._loop.exec_()

            return self.api.unfilled_data
        except:
            return []

    # ----------------------------------------------------------------------
    # 주문 취소
    # ----------------------------------------------------------------------
    def cancel_order(self, order_no, code, qty):
        """
        부분 체결된 경우 남은 수량만 취소
        """
        try:
            safe_log(f"[KR-CANCEL] 주문취소 {order_no}")

            ret = self.api.send_order(
                rqname="cancel_order",
                screen_no="0103",
                acc_no=self.api.account,
                order_type=3,  # 매수취소
                code=code,
                qty=qty,
                price=0,
                hoga="00",
                original_no=order_no
            )

            if ret == 0:
                safe_log(f"[KR-CANCEL] 성공 {order_no}")
                return True
            else:
                safe_log(f"[KR-CANCEL] 실패 (code={ret})")
                return False

        except Exception as e:
            safe_log(f"[KR-CANCEL-ERR] {e}")
            return False
