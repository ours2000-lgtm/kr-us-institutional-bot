# =====================================================================
# Data Federation Layer V10 — Unified Data Access API
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable
import pandas as pd
from datetime import datetime, timezone


@dataclass
class MarketFeed:
    """
    각 시장별 데이터 공급자(collector)의 공통 인터페이스 래퍼.
    collector: 데이터 제공 객체 (Alpaca, Kiwoom, Binance 등)
    """
    collector: Any
    market: str  # "KR", "US", "CRYPTO"


class DataFederationV10:
    """
    여러 시장(KR/US/Crypto)의 데이터를 하나의 표준 API로 묶어주는 엔진.
    Signal / Regime / Portfolio / Execution 엔진의 공식 데이터 진입점.
    """

    def __init__(self):
        self.feeds: Dict[str, MarketFeed] = {}

    # -----------------------------------------------------------------
    # 1) 시장 등록
    # -----------------------------------------------------------------
    def register_market(self, market: str, collector: Any):
        """
        market: "KR", "US", "CRYPTO"
        collector: get_price(), get_ohlcv(), get_orderbook() 등을 가진 객체
        """
        self.feeds[market] = MarketFeed(collector=collector, market=market)

    # -----------------------------------------------------------------
    # 내부 유틸: timestamp 통일
    # -----------------------------------------------------------------
    @staticmethod
    def _utc_now():
        return datetime.now(timezone.utc)

    @staticmethod
    def _ensure_utc(ts: datetime) -> datetime:
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)

    # -----------------------------------------------------------------
    # 2) 현재가 조회 (시장 자동 선택)
    # -----------------------------------------------------------------
    def get_price(self, market: str, symbol: str) -> float:
        feed = self.feeds.get(market)
        if not feed:
            return 0.0
        try:
            price = feed.collector.get_price(symbol)
            return float(price)
        except:
            return 0.0

    # -----------------------------------------------------------------
    # 3) 캔들 OHLCV 조회 (과거 데이터 포함)
    # -----------------------------------------------------------------
    def get_ohlcv(self, market: str, symbol: str, lookback: int = 200) -> pd.DataFrame:
        feed = self.feeds.get(market)
        if not feed:
            return pd.DataFrame()

        try:
            df = feed.collector.get_ohlcv(symbol, lookback)
        except Exception:
            return pd.DataFrame()

        # 표준 포맷 강제
        required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
        for c in required_cols:
            if c not in df.columns:
                return pd.DataFrame()

        df["timestamp"] = df["timestamp"].apply(lambda x: DataFederationV10._ensure_utc(x))
        df.sort_values("timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df

    # -----------------------------------------------------------------
    # 4) 실시간 호가 / 체결강도 데이터
    # -----------------------------------------------------------------
    def get_orderbook(self, market: str, symbol: str) -> Dict[str, Any]:
        feed = self.feeds.get(market)
        if not feed:
            return {}

        try:
            ob = feed.collector.get_orderbook(symbol)
            return {
                "bid": float(ob.get("bid", 0)),
                "ask": float(ob.get("ask", 0)),
                "bid_size": float(ob.get("bid_size", 0)),
                "ask_size": float(ob.get("ask_size", 0)),
                "timestamp": self._utc_now(),
            }
        except:
            return {}

    # -----------------------------------------------------------------
    # 5) 시장 구조(Market Microstructure) 데이터
    # -----------------------------------------------------------------
    def get_market_structure(self, market: str, symbol: str) -> Dict[str, Any]:
        """
        예: 스프레드, 유동성, 거래량 증가율, TICK, VWAP 등
        collector에 해당 기능이 있다면 전달, 없으면 기본값
        """
        feed = self.feeds.get(market)
        if not feed:
            return {}

        try:
            ms = feed.collector.get_market_structure(symbol)
            ms["timestamp"] = self._utc_now()
            return ms
        except:
            return {
                "spread": 0.0,
                "liquidity": 0.0,
                "vwap": 0.0,
                "timestamp": self._utc_now(),
            }

    # -----------------------------------------------------------------
    # 6) V10 전체 엔진에서 사용하는 통합 데이터 인터페이스
    # -----------------------------------------------------------------
    def get_feature_bundle(self, market: str, symbol: str) -> Dict[str, Any]:
        """
        Signal Engine / Regime Engine / Portfolio Engine 에서 공통으로 호출
        """
        price = self.get_price(market, symbol)
        ohlcv = self.get_ohlcv(market, symbol, lookback=200)
        ob = self.get_orderbook(market, symbol)
        ms = self.get_market_structure(market, symbol)

        return {
            "market": market,
            "symbol": symbol,
            "price": price,
            "ohlcv": ohlcv,
            "orderbook": ob,
            "micro": ms,
            "timestamp": self._utc_now(),
        }
