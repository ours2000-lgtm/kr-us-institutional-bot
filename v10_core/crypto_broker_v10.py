# =====================================================================
#  Crypto Broker V10 (Primary: Binance SDK, Backup: REST)
# =====================================================================

from __future__ import annotations
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from binance.spot import Spot
from typing import Dict, Any, Optional


# =====================================================================
# Utils
# =====================================================================

def safe_log(msg: str):
    print(f"[CRYPTO_BROKER] {msg}")


# =====================================================================
#  Primary Broker — Binance SDK
# =====================================================================
class BinanceSDKBroker:
    def __init__(self, api_key: str, api_secret: str):
        self.client = Spot(api_key=api_key, api_secret=api_secret)
        safe_log("Primary BinanceSDKBroker loaded")

    @staticmethod
    def format_symbol(symbol: str) -> str:
        # BTC/USDT → BTCUSDT
        return symbol.replace("/", "")

    # ----------------------------
    # Price Feed
    # ----------------------------
    def get_last_price(self, symbol: str) -> float:
        s = self.format_symbol(symbol)
        res = self.client.ticker_price(symbol=s)
        return float(res["price"])

    # ----------------------------
    # Order: BUY
    # ----------------------------
    def buy(self, symbol: str, qty: float, price: float) -> str:
        s = self.format_symbol(symbol)
        res = self.client.new_order(
            symbol=s,
            side="BUY",
            type="LIMIT",
            timeInForce="GTC",
            price=str(price),
            quantity=str(qty)
        )
        safe_log(f"BUY submitted id={res.get('orderId')}")
        return str(res.get("orderId"))

    # ----------------------------
    # Order: SELL
    # ----------------------------
    def sell(self, symbol: str, qty: float, price: float) -> str:
        s = self.format_symbol(symbol)
        res = self.client.new_order(
            symbol=s,
            side="SELL",
            type="LIMIT",
            timeInForce="GTC",
            price=str(price),
            quantity=str(qty)
        )
        safe_log(f"SELL submitted id={res.get('orderId')}")
        return str(res.get("orderId"))

    # ----------------------------
    # Order Status
    # ----------------------------
    def get_order_status(self, order_id: str, symbol: str):
        s = self.format_symbol(symbol)
        res = self.client.get_order(symbol=s, orderId=order_id)

        filled = float(res.get("executedQty", 0))
        remaining = float(res.get("origQty", 0)) - filled
        avg_price = float(res.get("price", 0)) if filled > 0 else 0.0

        return {
            "filled_qty": filled,
            "remaining_qty": remaining,
            "avg_fill_price": avg_price
        }

    # ----------------------------
    # Cancel Order
    # ----------------------------
    def cancel_order(self, order_id: str, symbol: str):
        s = self.format_symbol(symbol)
        self.client.cancel_order(symbol=s, orderId=order_id)
        safe_log(f"Order cancelled: {order_id}")


# =====================================================================
#  Backup Broker — REST (fallback)
# =====================================================================
class BinanceRestBroker:
    BASE_URL = "https://api.binance.com"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        safe_log("Backup BinanceRestBroker loaded")

    @staticmethod
    def format_symbol(symbol: str) -> str:
        return symbol.replace("/", "")

    # Signature
    def _sign(self, params: dict) -> dict:
        query = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        params["signature"] = signature
        return params

    # GET request
    def _get(self, path: str, params: dict = None):
        headers = {"X-MBX-APIKEY": self.api_key}
        r = requests.get(self.BASE_URL + path, params=params, headers=headers)
        return r.json()

    # POST request
    def _post(self, path: str, params: dict):
        headers = {"X-MBX-APIKEY": self.api_key}
        r = requests.post(self.BASE_URL + path, params=params, headers=headers)
        return r.json()

    # ----------------------------
    # Price Feed
    # ----------------------------
    def get_last_price(self, symbol: str) -> float:
        s = self.format_symbol(symbol)
        res = self._get("/api/v3/ticker/price", {"symbol": s})
        return float(res["price"])

    # ----------------------------
    # Order Submit
    # ----------------------------
    def _send_order(self, symbol: str, side: str, qty: float, price: float):
        ts = int(time.time() * 1000)
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": qty,
            "price": price,
            "timestamp": ts
        }
        params = self._sign(params)
        res = self._post("/api/v3/order", params=params)
        return res.get("orderId")

    def buy(self, symbol: str, qty: float, price: float) -> str:
        s = self.format_symbol(symbol)
        order_id = self._send_order(s, "BUY", qty, price)
        safe_log(f"(REST) BUY submitted id={order_id}")
        return str(order_id)

    def sell(self, symbol: str, qty: float, price: float) -> str:
        s = self.format_symbol(symbol)
        order_id = self._send_order(s, "SELL", qty, price)
        safe_log(f"(REST) SELL submitted id={order_id}")
        return str(order_id)

    # ----------------------------
    # Order Status
    # ----------------------------
    def get_order_status(self, order_id: str, symbol: str):
        s = self.format_symbol(symbol)
        ts = int(time.time() * 1000)
        params = {"symbol": s, "orderId": order_id, "timestamp": ts}
        params = self._sign(params)

        res = self._get("/api/v3/order", params=params)
        filled = float(res.get("executedQty", 0))
        remaining = float(res.get("origQty", 0)) - filled
        avg_price = float(res.get("price", 0))

        return {
            "filled_qty": filled,
            "remaining_qty": remaining,
            "avg_fill_price": avg_price
        }

    # ----------------------------
    # Cancel
    # ----------------------------
    def cancel_order(self, order_id: str, symbol: str):
        s = self.format_symbol(symbol)
        ts = int(time.time() * 1000)
        params = {"symbol": s, "orderId": order_id, "timestamp": ts}
        params = self._sign(params)
        self._post("/api/v3/order", params=params)
        safe_log(f"(REST) Order cancelled: {order_id}")


# =====================================================================
#  Broker Manager — 자동 전환 (Primary → Backup)
# =====================================================================

class CryptoBrokerV10:
    """
    Primary: Binance SDK
    Fallback: REST
    """

    def __init__(self, api_key: str, api_secret: str):
        self.primary = BinanceSDKBroker(api_key, api_secret)
        self.backup = BinanceRestBroker(api_key, api_secret)

    # Wrapper with failover
    def _try(self, func_primary, func_backup, *args):
        try:
            return func_primary(*args)
        except Exception as e:
            safe_log(f"[FAILOVER] Primary failed → switching to backup. Reason: {e}")
            return func_backup(*args)

    # ----------------------------
    # Unified API
    # ----------------------------
    def get_last_price(self, symbol: str):
        return self._try(
            self.primary.get_last_price,
            self.backup.get_last_price,
            symbol
        )

    def buy(self, symbol: str, qty: float, price: float):
        return self._try(
            self.primary.buy,
            self.backup.buy,
            symbol, qty, price
        )

    def sell(self, symbol: str, qty: float, price: float):
        return self._try(
            self.primary.sell,
            self.backup.sell,
            symbol, qty, price
        )

    def get_order_status(self, order_id: str, symbol: str):
        return self._try(
            self.primary.get_order_status,
            self.backup.get_order_status,
            order_id, symbol
        )

    def cancel_order(self, order_id: str, symbol: str):
        return self._try(
            self.primary.cancel_order,
            self.backup.cancel_order,
            order_id, symbol
        )
