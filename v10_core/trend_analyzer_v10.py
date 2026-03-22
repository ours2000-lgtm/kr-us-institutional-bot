# =====================================================================
# Trend Analyzer V10 — Multi-Horizon Trend + Strength + Clustering
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np


# ---------------------------------------------------------------------
# 결과 구조
# ---------------------------------------------------------------------
@dataclass
class TrendResultV10:
    short_slope: float
    mid_slope: float
    long_slope: float
    ma_alignment: str      # "BULL", "NEUTRAL", "BEAR"
    rsi_slope: float
    roc: float
    momentum: float
    cluster: str           # Trend Cluster
    trend_score: float     # 0 ~ 1 normalized score


# =====================================================================
# Trend Analyzer Engine V10
# =====================================================================
class TrendAnalyzerV10:
    """
    추세 분석 엔진 V10
    ---------------------------------------------------------------
    제공 기능:
    - Short/Mid/Long MA trend
    - MA alignment (정배열/역배열)
    - RSI slope, ROC, 단기 Momentum
    - Trend clustering
    - Trend Score (0~1)
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config.get("FEATURES", {})

        # 이동평균 기간
        self.short_ma = int(self.cfg.get("ma_short", 20))
        self.mid_ma   = int(self.cfg.get("ma_mid", 60))
        self.long_ma  = int(self.cfg.get("ma_long", 120))

        # RSI 기간
        self.rsi_period = int(self.cfg.get("rsi_period", 14))

    # -----------------------------------------------------------------
    # 유틸: 이동평균
    # -----------------------------------------------------------------
    @staticmethod
    def ma(arr: np.ndarray, period: int) -> float:
        if arr is None or len(arr) < period:
            return float(np.mean(arr)) if len(arr) > 0 else 0.0
        return float(np.mean(arr[-period:]))

    # -----------------------------------------------------------------
    # 기울기 계산 (slope)
    # -----------------------------------------------------------------
    @staticmethod
    def slope(arr: np.ndarray) -> float:
        if len(arr) < 3:
            return 0.0
        x = np.arange(len(arr))
        coef = np.polyfit(x, arr, 1)
        return float(coef[0])

    # -----------------------------------------------------------------
    # RSI 계산
    # -----------------------------------------------------------------
    def calc_rsi(self, prices: np.ndarray) -> float:
        if len(prices) < self.rsi_period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-self.rsi_period:])
        avg_loss = np.mean(losses[-self.rsi_period:])

        if avg_loss == 0:
            return 70.0

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    # -----------------------------------------------------------------
    # ROC / Momentum 계산
    # -----------------------------------------------------------------
    @staticmethod
    def roc(arr: np.ndarray, period: int = 10) -> float:
        if len(arr) <= period:
            return 0.0
        return float((arr[-1] - arr[-period]) / arr[-period])

    @staticmethod
    def momentum(arr: np.ndarray, period: int = 5) -> float:
        if len(arr) <= period:
            return 0.0
        return float(arr[-1] - arr[-period])

    # -----------------------------------------------------------------
    # Trend Cluster
    # -----------------------------------------------------------------
    @staticmethod
    def cluster_trend(score: float) -> str:
        if score > 0.75:
            return "STRONG_UP"
        elif score > 0.55:
            return "UP"
        elif score > 0.45:
            return "SIDEWAYS"
        elif score > 0.25:
            return "DOWN"
        else:
            return "STRONG_DOWN"

    # -----------------------------------------------------------------
    # 메인 분석 함수
    # -----------------------------------------------------------------
    def analyze(self, prices: np.ndarray) -> TrendResultV10:

        if prices is None or len(prices) < 10:
            return TrendResultV10(
                short_slope=0, mid_slope=0, long_slope=0,
                ma_alignment="NEUTRAL",
                rsi_slope=0, roc=0, momentum=0,
                cluster="SIDEWAYS",
                trend_score=0.5
            )

        # -------------------------
        # 1) MA & Slope
        # -------------------------
        short_ma_val = self.ma(prices, self.short_ma)
        mid_ma_val   = self.ma(prices, self.mid_ma)
        long_ma_val  = self.ma(prices, self.long_ma)

        short_slope = self.slope(prices[-self.short_ma:])
        mid_slope   = self.slope(prices[-self.mid_ma:])
        long_slope  = self.slope(prices[-self.long_ma:])

        # 정배열 / 역배열
        if short_ma_val > mid_ma_val > long_ma_val:
            ma_align = "BULL"
        elif long_ma_val > mid_ma_val > short_ma_val:
            ma_align = "BEAR"
        else:
            ma_align = "NEUTRAL"

        # -------------------------
        # 2) Local Trend (RSI slope + ROC + Momentum)
        # -------------------------
        rsi = self.calc_rsi(prices)
        rsi_slope = self.slope(np.array([rsi - 50]))  # 단기 경사 표현

        roc10 = self.roc(prices, period=10)
        mom5 = self.momentum(prices, period=5)

        # -------------------------
        # 3) Trend Score 계산
        # -------------------------
        # 정규화용 스케일링
        slope_norm = np.tanh(short_slope * 15)
        roc_norm = np.tanh(roc10 * 5)
        momentum_norm = np.tanh(mom5 * 3)

        score_raw = (0.5 * slope_norm +
                     0.25 * roc_norm +
                     0.25 * momentum_norm +
                     (0.1 if ma_align == "BULL" else -0.1 if ma_align == "BEAR" else 0))

        trend_score = float(np.clip((score_raw + 1) / 2, 0, 1))

        # -------------------------
        # 4) Trend Cluster
        # -------------------------
        cluster = self.cluster_trend(trend_score)

        return TrendResultV10(
            short_slope=short_slope,
            mid_slope=mid_slope,
            long_slope=long_slope,
            ma_alignment=ma_align,
            rsi_slope=rsi_slope,
            roc=roc10,
            momentum=mom5,
            cluster=cluster,
            trend_score=trend_score
        )
