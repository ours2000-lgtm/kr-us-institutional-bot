# ================================================================
#  broker_crypto_v10_upgrade.py
#  Binance 기반 Crypto Broker (REST + WebSocket + Health Check)
#  - 체결 실시간 스트림
#  - listenKey 자동 갱신
#  - 백오프 재시도
#  - MARKET / LIMIT / STOP / OCO 지원
#  - Simulation 모드
# ================================================================

import time
import hmac
import hashlib
import requests
import threading
import traceback
import websocket
import json
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

# ---------------------------------------------------------------
# 환경 설정
# ---------------------------------------------------------------
BINANCE_BASE = "https://api.binance.com"
BINANCE_TEST = "https://testnet.binance.vision"

WS_BASE = "wss://stream.binance.com:9443/ws"
WS_TEST = "wss://testnet.binance.vision/ws"

# ---------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------
def utc_ts() -> int:
    return int(time.time() * 1000)

def safe_print(msg: str):
    print(f"[{datetime.utcnow().isoformat()}] {msg}")

# ---------------------------------------------------------------
# Crypto Broker V10 (업그레이드)
# ---------------------------------------------------------------
class BrokerCryptoV10:
    def __init__(self,
                 api_key: str,
                 api_secret: str,
                 mode: str = "REAL",
                 telegram_hook=None):

        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.mode = mode.upper()  # REAL / TEST / SIM

        self.base = BINANCE_TEST if self.mode == "TEST" else BINANCE_BASE
        self.ws_base = WS_TEST if self.mode == "TEST" else WS_BASE

        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

        # 실시간 체결/계좌 업데이트용
        self.listen_key = None
        self.ws = None
        self.ws_thread = None
        self.ws_running = False

        # SIM 모드 메모리 저장 계좌
        self.sim_balance = {"USDT": 10000.0}
        self.sim_positions = {}

        # 외부 알림 (텔레그램)
        self.alert = telegram_hook

        # 자동 시작
        if self.mode in ("REAL", "TEST"):
            self._start_user_stream()

    # -----------------------------------------------------------
    # 시그니처 생성
    # -----------------------------------------------------------
    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        sig = hmac.new(self.api_secret, query.encode(), hashlib.sha256).hexdigest()
        params["signature"] = sig
        return params

    # -----------------------------------------------------------
    # 백오프 재시도
    # -----------------------------------------------------------
    def _request(self, method: str, path: str, params=None, signed=False):
        url = self.base + path
        params = params or {}
        params["timestamp"] = utc_ts()

        if signed:
            params = self._sign(params)

        for delay in [0.1, 0.3, 0.7, 1.5]:
            try:
                resp = self.session.request(method, url, params=params, timeout=3)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    safe_print(f"REST Error {resp.status_code}: {resp.text}")
            except Exception as e:
                safe_print(f"REST Exception: {e}")
            time.sleep(delay)

        # 최종 실패
        self._send_alert(f"REST API Failure: {method} {path}")
        return None

    # -----------------------------------------------------------
    # 텔레그램 알림
    # -----------------------------------------------------------
    def _send_alert(self, msg: str):
        if self.alert:
            try:
                self.alert(msg)
            except:
                pass
        safe_print(f"[ALERT] {msg}")

    # -----------------------------------------------------------
    # WebSocket 사용자 스트림 시작
    # -----------------------------------------------------------
    def _start_user_stream(self):
        safe_print("🔌 Creating listenKey...")
        res = self._request("POST", "/api/v3/userDataStream")
        if not res or "listenKey" not in res:
            safe_print("❌ listenKey 생성 실패")
            return

        self.listen_key = res["listenKey"]
        self.ws_running = True

        ws_url = f"{self.ws_base}/{self.listen_key}"
        safe_print(f"🔌 Connecting WebSocket → {ws_url}")

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_ws_message,
            on_error=self._on_ws_error,
            on_close=self._on_ws_close
        )

        # 별도 스레드로 WS 구동
        self.ws_thread = threading.Thread(target=self._ws_run, daemon=True)
        self.ws_thread.start()

        # listenKey 갱신 스레드
        threading.Thread(target=self._keepalive_listen_key, daemon=True).start()

    def _ws_run(self):
        while self.ws_running:
            try:
                self.ws.run_forever(ping_interval=15, ping_timeout=10)
            except Exception as e:
                safe_print(f"WS run error: {e}")
            time.sleep(2)

    def _keepalive_listen_key(self):
        while self.ws_running:
            time.sleep(30 * 60)
            safe_print("🔄 listenKey KeepAlive")
            self._request("PUT", "/api/v3/userDataStream", params={"listenKey": self.listen_key})

    # -----------------------------------------------------------
    # WebSocket 콜백
    # -----------------------------------------------------------
    def _on_ws_message(self, ws, msg):
        data = json.loads(msg)
        et = data.get("e")

        if et == "executionReport":
            order_id = data.get("i")
            status = data.get("X")
            filled = float(data.get("z", 0))
            price = float(data.get("L", 0))
            safe_print(f"📥 Execution Update [{status}] id={order_id} filled={filled} price={price}")

        elif et == "outboundAccountPosition":
            safe_print(f"💰 Balance Update: {data}")

    def _on_ws_error(self, ws, error):
        safe_print(f"WS Error: {error}")
        self._send_alert(f"WebSocket error: {error}")

    def _on_ws_close(self, ws, code, msg):
        safe_print(f"❌ WebSocket Closed: {code}, {msg}")

    # -----------------------------------------------------------
    # SIM 모드 주문 처리
    # -----------------------------------------------------------
    def _sim_order(self, symbol: str, side: str, qty: float, price: float):
        cost = qty * price
        if side == "BUY":
            if self.sim_balance["USDT"] < cost:
                return {"success": False, "reason": "Insufficient USDT"}
            self.sim_balance["USDT"] -= cost
            self.sim_positions[symbol] = self.sim_positions.get(symbol, 0) + qty
        else:
            if self.sim_positions.get(symbol, 0) < qty:
                return {"success": False, "reason": "Insufficient Position"}
            self.sim_positions[symbol] -= qty
            self.sim_balance["USDT"] += cost

        return {
            "success": True,
            "filled_qty": qty,
            "avg_price": price
        }

    # -----------------------------------------------------------
    # 주문 API (MARKET / LIMIT / STOP / OCO)
    # -----------------------------------------------------------
    def place_order(self,
                    symbol: str,
                    side: str,
                    qty: float,
                    order_type: str = "MARKET",
                    price: Optional[float] = None,
                    stop_price: Optional[float] = None):

        if self.mode == "SIM":
            return self._sim_order(symbol, side, qty, price or 0)

        params = {
            "symbol": symbol.replace("/", ""),
            "side": side,
            "type": order_type,
            "quantity": qty,
        }

        if order_type == "LIMIT":
            params["timeInForce"] = "GTC"
            params["price"] = price

        if order_type in ("STOP_LOSS_LIMIT", "TAKE_PROFIT_LIMIT"):
            params["stopPrice"] = stop_price
            params["timeInForce"] = "GTC"
            params["price"] = price

        if order_type == "OCO":
            params = {
                "symbol": symbol.replace("/", ""),
                "side": side,
                "quantity": qty,
                "price": price,
                "stopPrice": stop_price,
            }

        res = self._request("POST", "/api/v3/order", params, signed=True)
        if not res:
            return {"success": False, "reason": "Order failure"}

        return {
            "success": True,
            "order_id": res.get("orderId"),
            "client_order_id": res.get("clientOrderId"),
        }

    # -----------------------------------------------------------
    # 가격 데이터
    # -----------------------------------------------------------
    def get_last_price(self, symbol: str) -> Optional[float]:
        if self.mode == "SIM":
            return 100.0

        params = {"symbol": symbol.replace("/", "")}
        res = self._request("GET", "/api/v3/ticker/price", params)
        if not res:
            return None
        return float(res["price"])

    # -----------------------------------------------------------
    # 헬스 체크
    # -----------------------------------------------------------
    def health_check(self) -> Dict[str, Any]:
        start = time.time()
        ping = self._request("GET", "/api/v3/ping")
        latency = time.time() - start

        ws_status = "UP" if self.ws_running else "DOWN"

        return {
            "rest_latency": latency,
            "rest_ok": ping is not None,
            "ws_status": ws_status
        }
