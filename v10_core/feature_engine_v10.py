# =====================================================================
# Feature Engineering V10 — Multi-Stage Feature Generator
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import pandas as pd
import numpy as np


@dataclass
class FeatureConfig:
    return_windows: tuple = (5, 10, 20, 60)
    vol_windows: tuple = (10, 20, 60)
    mom_windows: tuple = (10, 20, 60)
    liquidity_window: int = 20
    microstructure: bool = True


class FeatureEngineV10:
    """
    V10 Feature Engine
    - Signal / Regime / Meta Strategy 전용 특징 생성
    - 시계열, 변동성, 추세, 유동성, 미시구조 특징 자동 생성
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.cfg = FeatureConfig(**(config or {}))

    # ================================================================
    # 1) 수익률 기반 특징
    # ================================================================
    def _returns(self, df: pd.DataFrame, out: Dict[str, float]):
        close = df["close"]
        for w in self.cfg.return_windows:
            out[f"ret_{w}"] = float((close.iloc[-1] / close.iloc[-w] - 1)
                                    if len(close) >= w else 0)

    # ================================================================
    # 2) 변동성 기반 특징
    # ================================================================
    def _volatility(self, df: pd.DataFrame, out: Dict[str, float]):
        ret = df["close"].pct_change().fillna(0)
        for w in self.cfg.vol_windows:
            out[f"vol_{w}"] = float(ret.rolling(w).std().iloc[-1]
                                    if len(ret) >= w else 0)

    # ================================================================
    # 3) 모멘텀 / 추세 기반 특징
    # ================================================================
    def _momentum(self, df: pd.DataFrame, out: Dict[str, float]):
        close = df["close"]
        for w in self.cfg.mom_windows:
            ma = close.rolling(w).mean().iloc[-1] if len(close) >= w else close.iloc[-1]
            out[f"mom_{w}"] = float((close.iloc[-1] / ma - 1) if ma != 0 else 0)

    # ================================================================
    # 4) 유동성 특징 (거래량 기반)
    # ================================================================
    def _liquidity(self, df: pd.DataFrame, out: Dict[str, float]):
        vol = df["volume"]
        w = self.cfg.liquidity_window
        if len(vol) >= w:
            out["liq_score"] = float(vol.iloc[-1] / (vol.rolling(w).mean().iloc[-1] + 1e-9))
        else:
            out["liq_score"] = 1.0

    # ================================================================
    # 5) 미시구조 특징 (스프레드 등)
    # ================================================================
    def _microstructure(self, quote: Dict[str, float], out: Dict[str, float]):
        """
        quote = {"bid": float, "ask": float, "bid_size": float, "ask_size": float}
        """
        if not self.cfg.microstructure:
            return

        bid = float(quote.get("bid", 0))
        ask = float(quote.get("ask", 0))

        if bid > 0 and ask > 0:
            spread = ask - bid
            mid = (ask + bid) / 2
            out["spread"] = spread
            out["rel_spread"] = spread / mid
        else:
            out["spread"] = 0.0
            out["rel_spread"] = 0.0

        out["order_imbalance"] = float(
            quote.get("bid_size", 0) - quote.get("ask_size", 0)
        )

    # ================================================================
    # 6) Feature Pack 생성
    # ================================================================
    def generate_features(self,
                          df_ohlcv: pd.DataFrame,
                          quote: Dict[str, float] = None) -> Dict[str, float]:
        """
        반환값: Signal / Regime / Meta Strategy 모두가 사용하는 Feature Pack (dict)
        """

        if df_ohlcv is None or len(df_ohlcv) == 0:
            return {}

        out: Dict[str, float] = {}

        self._returns(df_ohlcv, out)
        self._volatility(df_ohlcv, out)
        self._momentum(df_ohlcv, out)
        self._liquidity(df_ohlcv, out)

        if quote:
            self._microstructure(quote, out)

        return out
