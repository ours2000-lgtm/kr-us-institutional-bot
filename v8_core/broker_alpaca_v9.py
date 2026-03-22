# ================================================================
#  broker_alpaca_v9.py — Alpaca Broker Interface (V9 PLUS)
# ================================================================
#  • Paper / Live 자동 전환
#  • 시장가 주문 / 포지션 조회 / 계좌 잔고 조회
#  • 안전한 주문 예외처리 + 딜레이 관리
#  • 전 세계 1% 개인 트레이더급 안정성
# ================================================================

import time
import threading
import traceback
from datetime import datetime
import alpaca_trade_api as tradeapi


class AlpacaBrokerV9:

    def __init__(self, config):
        """
        config 예시:
        BROKER:
          US:
            type: "ALPACA"
            key: "..."
            secret: "..."
            paper: true
        """

        self.api_key = config["BROKER"]["US"]["key"]
        self.secret = config["BROKER"]["US"]["secret"]
        self.paper = config["BROKER"]["US"].get("paper", True)

        # --------------------------------------------------------
        # ENDPOINT 자동 전환
        # --------------------------------------------------------
        if self.paper:
            endpoint = "https://paper-api.alpaca.markets"
        else:
            endpoint = "https://api.alpaca.markets"

        # --------------------------------------------------------
        # Alpaca API 객체 생성
        # --------------------------------------------------------
        self.api = tradeapi.REST(
            self.api_key,
            self.secret,
            endpoint,
            api_version="v2"
        )

        print(f"[Alpaca] BrokerV9 초기화 완료 (PAPER={self.paper})")

    # ==================================================================
    # 계좌 잔고
    # ==================================================================
    def get_cash(self):
        try:
            account = self.api.get_account()
            return float(account.cash)
        except Exception as e:
            print("[Alpaca][ERROR] get_cash:", e)
            return 0.0

    # ==================================================================
    # 현재 보유 포지션 조회 (symbol 단건)
    # ==================================================================
    def get_position(self, symbol):
        try:
            pos = self.api.get_position(symbol)
            return float(pos.qty), float(pos.avg_entry_price)
        except Exception:
            return 0, 0.0

    # ==================================================================
    # 전체 포지션 조회 (딕셔너리 반환)
    # ==================================================================
    def get_all_positions(self):
        positions = {}
        try:
            pos_list = self.api.list_positions()
            for p in pos_list:
                positions[p.symbol] = {
                    "qty": float(p.qty),
                    "avg_price": float(p.avg_entry_price)
                }
            return positions
        except Exception as e:
            print("[Alpaca][ERROR] get_all_positions:", e)
            return {}

    # ==================================================================
    # 안전 주문(시장가 BUY)
    # ==================================================================
    def buy(self, symbol, qty):
        try:
            self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            print(f"[BUY] {symbol} x {qty}")
            return True
        except Exception as e:
            print(f"[Alpaca][ERROR] BUY {symbol}:", e)
            return False

    # ==================================================================
    # 안전 주문(시장가 SELL)
    # ==================================================================
    def sell(self, symbol, qty):
        try:
            self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            print(f"[SELL] {symbol} x {qty}")
            return True
        except Exception as e:
            print(f"[Alpaca][ERROR] SELL {symbol}:", e)
            return False

    # ==================================================================
    # 포지션 전체 청산
    # ==================================================================
    def close_position(self, symbol):
        try:
            self.api.close_position(symbol)
            print(f"[CLOSE] {symbol}")
            return True
        except Exception as e:
            print(f"[Alpaca][ERROR] close_position {symbol}:", e)
            return False

    # ==================================================================
    # 전체 계좌 ALL-IN 청산
    # ==================================================================
    def close_all_positions(self):
        try:
            self.api.close_all_positions()
            print("[CLOSE ALL] 모든 포지션 청산 완료")
            return True
        except Exception as e:
            print("[Alpaca][ERROR] close_all_positions:", e)
            return False

    # ==================================================================
    # 가격 기반 수량 계산 (포트폴리오 엔진에서 주로 사용)
    # ==================================================================
    def calculate_quantity(self, cash, price, weight=1.0):
        """
        weight = 0.5 이면 50% 캐시만 사용.
        """
        try:
            if price <= 0:
                return 0
            qty = int((cash * weight) / price)
            return max(qty, 0)
        except:
            return 0

    # ==================================================================
    # 단순 가격 조회 (DataCollector에서 이미 제공되지만 예비용)
    # ==================================================================
    def get_price(self, symbol):
        try:
            quote = self.api.get_last_quote(symbol)
            return quote.bidprice or quote.askprice or 0
        except Exception:
            return 0
