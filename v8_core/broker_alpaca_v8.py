# ======================================================================
# broker_alpaca_v8.py
# 미국 시장 브로커 엔진 (V8 PLUS 안정판)
# ----------------------------------------------------------------------
# 역할 요약:
#   ✔ Alpaca(PAPER/LIVE) 매수·매도 실행
#   ✔ 잔고 / 체결 / 포트폴리오 조회
#   ✔ 네트워크/키 오류 자동 복구
#   ✔ Executor V8 PLUS에서 공통 인터페이스로 호출됨
# ======================================================================

import time
import traceback
from datetime import datetime
import requests
from utils_v8 import safe_log
from config_loader_v8 import load_config

CONFIG = load_config()


class BrokerAlpacaV8:
    """
    Alpaca Broker Wrapper (V8 PLUS)
    표준 인터페이스:
        - buy(symbol, qty)
        - sell(symbol, qty)
        - get_price(symbol)
        - get_balance()
        - recover_if_needed()
    """

    def __init__(self, mode=None):
        self.mode = (mode or CONFIG.get("mode", "SIM")).upper()

        alp = CONFIG.get("API_KEYS", {}).get("alpaca", {})
        self.key = alp.get("key")
        self.secret = alp.get("secret")

        if self.mode == "LIVE":
            self.base = "https://api.alpaca.markets"
        else:
            self.base = "https://paper-api.alpaca.markets"

        safe_log(f"[Alpaca Broker V8] Initialized (mode={self.mode})")

        self.session = requests.Session()
        self.last_error_time = None

    # --------------------------------------------------------------
    # 내부 요청 함수
    # --------------------------------------------------------------
    def _request(self, method, endpoint, data=None):
        url = self.base + endpoint
        headers = {
            "APCA-API-KEY-ID": self.key,
            "APCA-API-SECRET-KEY": self.secret
        }
        try:
            if method == "GET":
                r = self.session.get(url, headers=headers, timeout=2)
            else:
                r = self.session.post(url, json=data, headers=headers, timeout=2)

            if r.status_code in (200, 201):
                return r.json()

            safe_log(f"[Alpaca Error] {endpoint} → {r.status_code}")
            return None

        except Exception as e:
            safe_log(f"[Alpaca Request Fail] {endpoint}: {e}")
            self.mark_error()
            return None

    # --------------------------------------------------------------
    # 가격 조회
    # --------------------------------------------------------------
    def get_price(self, symbol):
        try:
            data = self._request("GET", f"/v2/stocks/{symbol}/quotes/latest")
            if not data:
                return None

            return data.get("quote", {}).get("ap", None)
        except:
            return None

    # --------------------------------------------------------------
    # 잔고 조회
    # --------------------------------------------------------------
    def get_balance(self):
        try:
            acc = self._request("GET", "/v2/account")
            if not acc:
                return {}

            cash = float(acc.get("cash", 0))
            bp = float(acc.get("buying_power", 0))

            return {"cash": cash, "buying_power": bp}
        except Exception as e:
            safe_log(f"[Alpaca Balance Error] {e}")
            self.mark_error()
            return {}

    # --------------------------------------------------------------
    # 매수
    # --------------------------------------------------------------
    def buy(self, symbol, qty):
        try:
            data = {
                "symbol": symbol,
                "qty": qty,
                "side": "buy",
                "type": "market",
                "time_in_force": "gtc"
            }

            result = self._request("POST", "/v2/orders", data)
            if result:
                safe_log(f"[BUY] {symbol} x {qty} 주문 요청됨")
                return {"status": "PENDING", "price": None}

            return {"status": "ERROR", "reason": "Failed to place BUY"}
        except Exception as e:
            safe_log(f"[BUY ERROR] {e}")
            self.mark_error()
            return {"status": "ERROR", "reason": str(e)}

    # --------------------------------------------------------------
    # 매도
    # --------------------------------------------------------------
    def sell(self, symbol, qty):
        try:
            data = {
                "symbol": symbol,
                "qty": qty,
                "side": "sell",
                "type": "market",
                "time_in_force": "gtc"
            }

            result = self._request("POST", "/v2/orders", data)
            if result:
                safe_log(f"[SELL] {symbol} x {qty} 주문 요청됨")
                return {"status": "PENDING", "price": None}

            return {"status": "ERROR", "reason": "Failed to place SELL"}
        except Exception as e:
            safe_log(f"[SELL ERROR] {e}")
            self.mark_error()
            return {"status": "ERROR", "reason": str(e)}

    # --------------------------------------------------------------
    # 오류 발생 시점 기록
    # --------------------------------------------------------------
    def mark_error(self):
        self.last_error_time = datetime.now()

    # --------------------------------------------------------------
    # 자동 복구 로직
    # Executor V8 PLUS에서 매 루프마다 호출됨
    # --------------------------------------------------------------
    def recover_if_needed(self):
        if not self.last_error_time:
            return

        try:
            if (datetime.now() - self.last_error_time).seconds >= 5:
                safe_log("[Alpaca Broker] 자동 복구 시도…")
                self.session = requests.Session()
                self.last_error_time = None
                safe_log("[Alpaca Broker] 복구 성공")
        except Exception as e:
            safe_log(f"[Alpaca Broker] 복구 실패: {e}")
            traceback.print_exc()
