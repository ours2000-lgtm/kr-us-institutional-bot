# =====================================================================
# Gap Analyzer V10 — Gap Direction, Strength, Volatility Signal Engine
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np


@dataclass
class GapResultV10:
    symbol: str
    gap_pct: float
    gap_dir: int                # +1 gap up / -1 gap down / 0 neutral
    strength_score: float       # [-1, +1]
    volatility_score: float     # [0, 1]
    confidence: float           # [0, 1]


class GapAnalyzerV10:
    """
    시장 갭 분석 엔진 V10
    ------------------------------------------------
    기능:
    - 전일 종가 vs 오늘 시가 → Gap 비율 계산
    - 방향성(gap up / down)
    - 갭 크기 기반 strength score
    - 시초 변동성 기반 volatility score
    - confidence score 계산 (신뢰도)
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config.get("FEATURES", {})
        self.max_gap_pct = float(self.cfg.get("max_gap_pct", 0.12))     # 12% 이상은 clip
        self.max_vol_window = int(self.cfg.get("gap_vol_window", 5))    # 시초 5틱 변동성

    # ==========================================================
    # Gap % 계산
    # ==========================================================
    @staticmethod
    def calc_gap_pct(prev_close: float, open_price: float) -> float:
        if prev_close <= 0 or open_price <= 0:
            return 0.0
        return (open_price - prev_close) / prev_close

    # ==========================================================
    # Gap 방향성 판단
    # ==========================================================
    @staticmethod
    def gap_direction(gap_pct: float) -> int:
        if abs(gap_pct) < 1e-4:
            return 0
        return 1 if gap_pct > 0 else -1

    # ==========================================================
    # Gap Strength Score ([-1, +1] 정규화)
    # ==========================================================
    def calc_strength_score(self, gap_pct: float) -> float:
        g = float(np.clip(gap_pct / self.max_gap_pct, -1, 1))
        return g

    # ==========================================================
    # Volatility Score ([0, 1])
    # ==========================================================
    def calc_volatility_score(self, prices: np.ndarray) -> float:
        if prices is None or len(prices) < 3:
            return 0.0
        window = prices[: self.max_vol_window]
        returns = np.diff(window) / window[:-1]
        vol = float(np.std(returns))
        return float(np.clip(vol * 10, 0, 1))  # 0.1 std → 1.0 스케일

    # ==========================================================
    # Confidence Score (신뢰도)
    # ----------------------------------------------------------
    # 갭 크기 + 방향성 일관성 + 시초 변동성 안정성 기반
    # ==========================================================
    def calc_confidence(self, strength: float, vol_score: float) -> float:
        base = abs(strength)
        stability = 1.0 - vol_score  # 변동성 높으면 confidence 낮아짐
        conf = float(np.clip((base * 0.7 + stability * 0.3), 0, 1))
        return conf

    # ==========================================================
    # Main 분석 함수
    # ==========================================================
    def analyze(self,
                symbol: str,
                prev_close: float,
                open_price: float,
                early_prices: Optional[np.ndarray]) -> GapResultV10:

        # (1) gap %
        gap_pct = self.calc_gap_pct(prev_close, open_price)

        # (2) gap direction
        gap_dir = self.gap_direction(gap_pct)

        # (3) strength score
        strength = self.calc_strength_score(gap_pct)

        # (4) early volatility
        vol_score = self.calc_volatility_score(early_prices)

        # (5) confidence
        conf = self.calc_confidence(strength, vol_score)

        return GapResultV10(
            symbol=symbol,
            gap_pct=gap_pct,
            gap_dir=gap_dir,
            strength_score=strength,
            volatility_score=vol_score,
            confidence=conf,
        )
