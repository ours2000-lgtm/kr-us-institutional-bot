# ======================================================================
# broker_alpaca_v8.py — Alpaca Broker for V8 PLUS (FINAL)
# ======================================================================
# 기능:
#   ✔ 미국주식 Alpaca 매수/매도
#   ✔ PAPER / LIVE 자동 인식
#   ✔ 실패 시 최대 3회 재시도
#   ✔ 잔고 / 포지션 / 시세 조회
#   ✔ ExecutorEngineV8와 완전 호환
#   ✔ 안전로그(safe_log)로 모든 기록 보존
# ======================================================================

import time
import traceback
from datetime import datetime

import requests
from utils_v8 import safe_log


class AlpacaBrokerV8:
    def __init__(self, config):
        self.config = config
        self.mode = config.get("mode", "SIM").upper()

        alpaca = config.get("alpaca", {})
        self.key = alpaca.get("key")
        self.secret = alpaca.get("secret")

        # PAPER / LIVE URL 자동 설정
        if self.mode == "LIVE":
            self.base = "https://api.alpaca.markets"
        else:
            self.base = "https://paper-api.alpaca.markets"

        self.retry = 3

        safe_log(f"[AlpacaBroker V8] 초기화 (mode={self.mode}, base={self.base})")

        self.session = requests.Session()
        self.session.headers.update({
            "APCA-API-KEY-ID": self.key,
            "APCA-API-SECRET-KEY": self.secret
        })

    # ----------------------------------------------------------------------
    # 내부 요청 함수 (자동 재시도)
    # ----------------------------------------------------------------------
    def _req(self, method, endpoint, payload=None):
        url = self.base + endpoint

        for attempt in range(self.retry):
            try:
                if method == "GET":
                    res = self.session.get(url, timeout=2)
                else:
                    res = self.session.post(url, json=payload, timeout=2)

                if res.status_code in (200, 201):
                    return res.json()

                safe_log(f"[Alpaca ERROR] Status={res.status_code}, Body={res.text}")
            except Exception as e:
                safe_log(f"[Alpaca REQ FAIL] attempt {attempt+1}/3 → {e}")

            time.sleep(0.4)

        return None

    # ----------------------------------------------------------------------
    # 시세 조회 (현재가)
    # ----------------------------------------------------------------------
    def get_price(self, symbol):
        data = self._req("GET", f"/v2/stocks/{symbol}/quotes/latest")
        try:
            return float(data["quote"]["ap"])
        except:
            return None

    # ----------------------------------------------------------------------
    # 매수
    # ----------------------------------------------------------------------
    def buy(self, symbol, qty, price=None):
        """
        price=None → 시장가
        """
        order = {
            "symbol": symbol,
            "qty": qty,
            "side": "buy",
            "type": "market" if price is None else "limit",
            "time_in_force": "day"
        }

        if price is not None:
            order["limit_price"] = price

        res = self._req("POST", "/v2/orders", order)

        safe_log(f"[BUY] {symbol} qty={qty} price={price} res={res}")

        if not res:
            return {"status": "ERROR"}

        return {"status": "PENDING", "id": res.get("id")}

    # ----------------------------------------------------------------------
    # 매도
    # ----------------------------------------------------------------------
    def sell(self, symbol, qty, price=None):
        order = {
            "symbol": symbol,
            "qty": qty,
            "side": "sell",
            "type": "market" if price is None else "limit",
            "time_in_force": "day"
        }

        if price is not None:
            order["limit_price"] = price

        res = self._req("POST", "/v2/orders", order)

        safe_log(f"[SELL] {symbol} qty={qty} price={price} res={res}")

        if not res:
            return {"status": "ERROR"}

        return {"status": "PENDING", "id": res.get("id")}

    # ----------------------------------------------------------------------
    # 포지션 리스트
    # ----------------------------------------------------------------------
    def get_positions(self):
        data = self._req("GET", "/v2/positions")
        if not data:
            return {}

        out = {}
        for p in data:
            out[p["symbol"]] = {
                "qty": float(p["qty"]),
                "avg_price": float(p["avg_entry_price"])
            }
        return out

    # ----------------------------------------------------------------------
    # 계좌 정보 (잔고)
    # ----------------------------------------------------------------------
    def get_account_info(self):
        data = self._req("GET", "/v2/account")

        if not data:
            return {"balance": 0}

        balance = float(data.get("portfolio_value", 0))
        cash = float(data.get("cash", 0))

        return {"balance": balance, "cash": cash}
