# =====================================================================
# Liquidity Analyzer V10 — Spread, Depth, Flow, Pressure Engine
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np


# ---------------------------------------------------------------------
# 결과 구조체
# ---------------------------------------------------------------------
@dataclass
class LiquidityResultV10:
    spread_abs: float
    spread_pct: float

    depth_bid: float
    depth_ask: float
    depth_ratio: float      # bid/(bid+ask)

    pressure: float         # -1 ~ +1 (체결강도)
    liquidity_score: float  # 0~1
    cluster: str            # VERY_HIGH / HIGH / NORMAL / LOW / CRITICAL


# =====================================================================
# Liquidity Analyzer V10 본체
# =====================================================================
class LiquidityAnalyzerV10:
    """
    유동성 분석 엔진 V10
    --------------------------------------------------
    제공 기능:
    - Spread 분석
    - Market Depth 분석
    - Microstructure Flow (체결강도)
    - Liquidity Score 산출
    - Liquidity Cluster 분류
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config.get("FEATURES", {})

        # 스프레드 기준값
        self.spread_norm = float(self.cfg.get("spread_norm", 0.001))  # 0.1%

        # depth normalization divisor
        self.depth_norm = float(self.cfg.get("depth_norm", 5000.0))

        # 체결강도 smoothing
        self.pressure_smooth = float(self.cfg.get("pressure_smooth", 0.4))

    # -----------------------------------------------------------------
    # Spread 계산
    # -----------------------------------------------------------------
    def calc_spread(self, bid: float, ask: float):
        if bid <= 0 or ask <= 0:
            return 0.0, 0.0

        spread_abs = ask - bid
        spread_pct = spread_abs / bid
        return float(spread_abs), float(spread_pct)

    # -----------------------------------------------------------------
    # Depth 기반 유동성 계산
    # -----------------------------------------------------------------
    def calc_depth(self, bid_sizes: np.ndarray, ask_sizes: np.ndarray):
        if bid_sizes is None or ask_sizes is None:
            return 0.0, 0.0, 0.5

        depth_bid = float(np.sum(bid_sizes))  # 예: 1~3단 합
        depth_ask = float(np.sum(ask_sizes))

        total = depth_bid + depth_ask
        if total <= 0:
            ratio = 0.5
        else:
            ratio = depth_bid / total

        return depth_bid, depth_ask, float(ratio)

    # -----------------------------------------------------------------
    # Microstructure 체결강도
    # pressure: -1 ~ +1
    # -----------------------------------------------------------------
    def calc_pressure(self, upticks: int, downticks: int, prev_pressure: float):
        total = upticks + downticks
        if total == 0:
            return prev_pressure

        raw = (upticks - downticks) / total  # -1 ~ +1
        # Smooth it
        pressure = self.pressure_smooth * prev_pressure + (1 - self.pressure_smooth) * raw
        return float(np.clip(pressure, -1, 1))

    # -----------------------------------------------------------------
    # Liquidity Score 계산
    # -----------------------------------------------------------------
    def calc_liquidity_score(self,
                             spread_pct: float,
                             depth_bid: float,
                             depth_ask: float,
                             pressure: float):
        """
        Score 0~1
        높은 유동성 = 1
        낮은 유동성 = 0
        """

        # Spread — spread_norm 대비 상대 점수
        spread_score = np.exp(-(spread_pct / self.spread_norm))  # spread 늘면 급감

        # Depth — depth_norm 기준
        depth_score = np.tanh((depth_bid + depth_ask) / (self.depth_norm))

        # Pressure — 양수면 매수우위, 음수면 매도우위
        pressure_score = (pressure + 1) / 2  # -1~+1 → 0~1

        total_score = (0.45 * spread_score +
                       0.35 * depth_score +
                       0.20 * pressure_score)

        return float(np.clip(total_score, 0, 1))

    # -----------------------------------------------------------------
    # Liquidity Cluster
    # -----------------------------------------------------------------
    @staticmethod
    def cluster(score: float) -> str:
        if score > 0.80:
            return "VERY_HIGH"
        elif score > 0.65:
            return "HIGH"
        elif score > 0.45:
            return "NORMAL"
        elif score > 0.25:
            return "LOW"
        else:
            return "CRITICAL"

    # -----------------------------------------------------------------
    # 메인 분석 함수
    # -----------------------------------------------------------------
    def analyze(self,
                bid: float,
                ask: float,
                bid_sizes: np.ndarray,
                ask_sizes: np.ndarray,
                upticks: int,
                downticks: int,
                prev_pressure: float = 0.0) -> LiquidityResultV10:

        # Spread
        spread_abs, spread_pct = self.calc_spread(bid, ask)

        # Depth
        depth_bid, depth_ask, depth_ratio = self.calc_depth(bid_sizes, ask_sizes)

        # Microstructure Flow
        pressure = self.calc_pressure(upticks, downticks, prev_pressure)

        # Liquidity Score
        liq_score = self.calc_liquidity_score(spread_pct, depth_bid, depth_ask, pressure)

        # Cluster
        cluster = self.cluster(liq_score)

        return LiquidityResultV10(
            spread_abs=spread_abs,
            spread_pct=spread_pct,
            depth_bid=depth_bid,
            depth_ask=depth_ask,
            depth_ratio=depth_ratio,
            pressure=pressure,
            liquidity_score=liq_score,
            cluster=cluster
        )
