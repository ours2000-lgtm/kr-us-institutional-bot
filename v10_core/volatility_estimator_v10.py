# =====================================================================
# Volatility Estimator V10 — Multi-Horizon Volatility + Clustering Engine
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np


@dataclass
class VolatilityResultV10:
    short_vol: float
    mid_vol: float
    long_vol: float
    realized_vol: float
    range_vol: float
    cluster: str           # {"LOW", "NORMAL", "HIGH", "EXTREME"}
    vol_score: float       # 0~1 정규화


class VolatilityEstimatorV10:
    """
    변동성 추정 엔진 V10
    -------------------------------------------------------
    제공 기능:
    - 단기/중기/장기 변동성 계산
    - 실현변동성 (realized vol)
    - Parkinson 고/저 변동성
    - 변동성 클러스터링
    - vol_score: 포트폴리오 엔진 + 메타전략에 바로 사용
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config.get("FEATURES", {})

        self.short_win = int(self.cfg.get("short_window", 20))
        self.mid_win = int(self.cfg.get("mid_window", 60))
        self.long_win = int(self.cfg.get("long_window", 120))

        self.cluster_low = float(self.cfg.get("vol_cluster_low", 0.008))       # 0.8%
        self.cluster_high = float(self.cfg.get("vol_cluster_high", 0.02))      # 2.0%
        self.cluster_extreme = float(self.cfg.get("vol_cluster_extreme", 0.035))  # 3.5%

    # =====================================================================
    # Helper: 표준 변동성 계산
    # =====================================================================
    @staticmethod
    def calc_vol(prices: np.ndarray) -> float:
        if prices is None or len(prices) < 3:
            return 0.0
        r = np.diff(prices) / prices[:-1]
        return float(np.std(r))

    # =====================================================================
    # Realized Volatility (연속 log return 기반)
    # =====================================================================
    @staticmethod
    def realized_vol(prices: np.ndarray) -> float:
        if prices is None or len(prices) < 3:
            return 0.0
        log_ret = np.diff(np.log(prices))
        rv = np.sqrt(np.sum(log_ret**2))
        return float(rv)

    # =====================================================================
    # Parkinson Range Volatility (고/저 기반)
    # =====================================================================
    @staticmethod
    def parkinson_vol(high: np.ndarray, low: np.ndarray) -> float:
        if high is None or low is None:
            return 0.0
        n = len(high)
        if n < 2:
            return 0.0
        term = np.log(high / low)
        return float(np.sqrt(np.sum(term**2) / (4 * np.log(2) * n)))

    # =====================================================================
    # Multi-horizon volatility
    # =====================================================================
    def calc_multi_horizon_vol(self, prices: np.ndarray) -> tuple:
        short_vol = self.calc_vol(prices[-self.short_win:]) if len(prices) >= self.short_win else self.calc_vol(prices)
        mid_vol   = self.calc_vol(prices[-self.mid_win:])   if len(prices) >= self.mid_win else self.calc_vol(prices)
        long_vol  = self.calc_vol(prices[-self.long_win:])  if len(prices) >= self.long_win else self.calc_vol(prices)
        return short_vol, mid_vol, long_vol

    # =====================================================================
    # Volatility Clustering (Regime Engine 연결)
    # =====================================================================
    def cluster_volatility(self, vol: float) -> str:
        if vol < self.cluster_low:
            return "LOW"
        elif vol < self.cluster_high:
            return "NORMAL"
        elif vol < self.cluster_extreme:
            return "HIGH"
        else:
            return "EXTREME"

    # =====================================================================
    # 최종 Volatility 분석 결과 생성
    # =====================================================================
    def analyze(self,
                prices: np.ndarray,
                high: Optional[np.ndarray] = None,
                low: Optional[np.ndarray] = None) -> VolatilityResultV10:

        # (1) multi-horizon volatility
        short_vol, mid_vol, long_vol = self.calc_multi_horizon_vol(prices)

        # (2) realized vol
        realized = self.realized_vol(prices)

        # (3) Parkinson high/low volatility
        range_vol = 0.0
        if high is not None and low is not None:
            range_vol = self.parkinson_vol(high, low)

        # (4) 대표변동성 = max(short, realized, range)
        main_vol = max(short_vol, realized, range_vol)

        # (5) clustering
        cluster = self.cluster_volatility(main_vol)

        # (6) normalize vol → vol_score (0~1)
        max_vol = self.cluster_extreme * 2
        vol_score = float(np.clip(main_vol / max_vol, 0, 1))

        return VolatilityResultV10(
            short_vol=short_vol,
            mid_vol=mid_vol,
            long_vol=long_vol,
            realized_vol=realized,
            range_vol=range_vol,
            cluster=cluster,
            vol_score=vol_score,
        )
