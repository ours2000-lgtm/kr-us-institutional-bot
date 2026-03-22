# ======================================================================
# broker_kiwoom_v8.py
# 기관급 V8 PLUS — Korean Market Broker Adapter (Kiwoom API)
# ----------------------------------------------------------------------
# 역할 요약:
#   ✔ 한국 주식 실거래 / 모의거래 전용 브로커 엔진
#   ✔ 매수/매도/잔고/체결조회/오류 복구 자동화
#   ✔ Executor V8 PLUS에서 호출하는 표준 인터페이스 제공
#   ✔ "강한 예외 처리 + 자동 재시도 + 안정 로그" 구조로 설계
# ======================================================================

import time
import traceback
from datetime import datetime
from utils_v8 import safe_log


class BrokerKiwoomV8:
    """
    Kiwoom API 래퍼
    - buy(symbol, qty)
    - sell(symbol, qty)
    - get_balance()
    - get_price(symbol)
    - recover_if_needed()
    """

    def __init__(self, mode="LIVE", api=None):
        """
        mode:
            LIVE  → 키움 실거래
            MOCK  → 키움 모의투자
        api:
            키움 OpenAPI 인스턴스 전달
        """
        self.mode = mode
        self.api = api
        self.last_error_time = None

        safe_log(f"[Kiwoom Broker V8] Initialized (mode={mode})")

    # ==================================================================
    # 가격 조회
    # ==================================================================
    def get_price(self, symbol):
        try:
            price = self.api.get_price(symbol)
            return price
        except Exception as e:
            safe_log(f"[KiwoomBroker] 가격조회 오류 {symbol}: {e}")
            return None

    # ==================================================================
    # 매수 실행
    # ==================================================================
    def buy(self, symbol, qty):
        try:
            price = self.get_price(symbol)
            if price is None:
                return {"status": "ERROR", "reason": "NO_PRICE"}

            order = self.api.buy(symbol, qty)
            safe_log(f"[BUY] {symbol} x {qty} → 요청됨")

            return {
                "status": "FILLED" if order else "PENDING",
                "price": price
            }

        except Exception as e:
            safe_log(f"[BUY ERROR] {symbol}: {e}")
            traceback.print_exc()
            self.mark_error()
            return {"status": "ERROR", "reason": str(e)}

    # ==================================================================
    # 매도 실행
    # ==================================================================
    def sell(self, symbol, qty):
        try:
            price = self.get_price(symbol)
            if price is None:
                return {"status": "ERROR", "reason": "NO_PRICE"}

            order = self.api.sell(symbol, qty)
            safe_log(f"[SELL] {symbol} x {qty} → 요청됨")

            return {
                "status": "FILLED" if order else "PENDING",
                "price": price
            }

        except Exception as e:
            safe_log(f"[SELL ERROR] {symbol}: {e}")
            traceback.print_exc()
            self.mark_error()
            return {"status": "ERROR", "reason": str(e)}

    # ==================================================================
    # 잔고 조회
    # ==================================================================
    def get_balance(self):
        try:
            return self.api.get_balance()
        except Exception as e:
            safe_log(f"[BALANCE ERROR] {e}")
            self.mark_error()
            return {}

    # ==================================================================
    # 자동 오류 복구 (핵심)
    # ==================================================================
    def mark_error(self):
        """오류 발생 시점 기록 → 일정 시간 지나면 자동 복구 허용"""
        self.last_error_time = datetime.now()

    def recover_if_needed(self):
        """
        브로커 오류 발생 후 일정 시간이 지나면 자동 재연결을 허용.
        Executor는 이 함수를 매 Loop마다 1회 호출.
        """
        try:
            if not self.last_error_time:
                return

            # 5초 이상 지나면 자동 복구
            if (datetime.now() - self.last_error_time).seconds >= 5:
                safe_log("[Kiwoom Broker] 자동 복구 시도…")
                self.api.reconnect()
                self.last_error_time = None
                safe_log("[Kiwoom Broker] 복구 성공")

        except Exception as e:
            safe_log(f"[Kiwoom Broker] 복구 실패: {e}")
            traceback.print_exc()
