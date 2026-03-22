# ======================================================================
# Signal Engine V10 — Multi-Source / Multi-Asset Unified Signal Engine
# KR / US / CRYPTO 공통 구조 + V10 Meta 통합 기반
# ======================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import numpy as np
import time


# ======================================================================
# 시그널 출력을 위한 데이터 구조
# ======================================================================
@dataclass
class SignalResult:
    symbol: str
    score: float
    raw_signals: Dict[str, float]
    regime_adj_score: float
    final: str          # "BUY", "SELL", "HOLD"


# ======================================================================
# Signal Engine V10
# ======================================================================
class SignalEngineV10:

    def __init__(self, config: Dict[str, Any], regime_engine, meta_engine):
        """
        config: config_v10.yaml의 SIGNAL 섹션
        regime_engine: RegimeEngineV10 인스턴스
        meta_engine: MetaStrategyEngine V10 (가중치/필터링 담당)
        """
        self.cfg = config.get("SIGNAL", {})
        self.regime_engine = regime_engine
        self.meta_engine = meta_engine

        # 기술적 지표 파라미터
        self.ma_fast = int(self.cfg.get("ma_fast", 5))
        self.ma_slow = int(self.cfg.get("ma_slow", 20))
        self.vwap_window = int(self.cfg.get("vwap_window", 30))

        # 신호 기준
        self.min_score = float(self.cfg.get("min_score", 0.15))

    # ==================================================================
    # 1) 지표 계산
    # ==================================================================
    @staticmethod
    def SMA(prices: np.ndarray, window: int) -> float:
        if len(prices) < window:
            return 0.0
        return float(np.mean(prices[-window:]))

    @staticmethod
    def VWAP(prices: np.ndarray, volumes: np.ndarray) -> float:
        if len(prices) < 2:
            return 0.0
        return float(np.sum(prices * volumes) / np.sum(volumes))

    @staticmethod
    def ROC(prices: np.ndarray, n: int = 3) -> float:
        if len(prices) < n + 1:
            return 0.0
        prev = prices[-(n + 1)]
        now = prices[-1]
        return float((now - prev) / prev) if prev > 0 else 0.0

    # ==================================================================
    # 2) RAW Signal 계산 (기관급 기본형)
    # ==================================================================
    def calc_raw_signals(self, prices: np.ndarray, volumes: np.ndarray) -> Dict[str, float]:
        if prices is None or len(prices) < 5:
            return {}

        sma_fast = self.SMA(prices, self.ma_fast)
        sma_slow = self.SMA(prices, self.ma_slow)
        roc = self.ROC(prices, 3)
        vwap = self.VWAP(prices[-self.vwap_window:], volumes[-self.vwap_window:]) \
            if len(prices) >= self.vwap_window else prices[-1]

        return {
            "ma_signal": 1.0 if sma_fast > sma_slow else -1.0,
            "roc": roc,
            "vwap_diff": (prices[-1] - vwap) / vwap if vwap > 0 else 0.0,
        }

    # ==================================================================
    # 3) RAW → Score 변환
    # ==================================================================
    @staticmethod
    def normalize_score(raw: Dict[str, float]) -> float:
        if not raw:
            return 0.0

        s = 0.0
        s += raw.get("ma_signal", 0.0) * 0.4
        s += raw.get("roc", 0.0) * 2.0     # 변화율 강조
        s += raw.get("vwap_diff", 0.0) * 1.5

        return float(np.clip(s, -1.0, 1.0))

    # ==================================================================
    # 4) Regime 조정
    # ==================================================================
    def adjust_by_regime(self, score: float, symbol: str) -> float:
        regime = self.regime_engine.get_regime(symbol)
        m = regime.score  # [-1, +1] 분포
        adj = score * (1.0 + 0.5 * m)
        return float(np.clip(adj, -1.2, 1.2))

    # ==================================================================
    # 5) Meta Strategy 조정 (V10)
    # ==================================================================
    def adjust_by_meta_strategy(self, score: float, symbol: str) -> float:
        """
        meta_engine.apply()는 시그널 가중치, 위험도 필터링 등을 수행
        """
        return self.meta_engine.apply(symbol, score)

    # ==================================================================
    # 6) 최종 매수/매도 판단
    # ==================================================================
    def decision(self, score: float) -> str:
        if score >= self.min_score:
            return "BUY"
        if score <= -self.min_score:
            return "SELL"
        return "HOLD"

    # ==================================================================
    # 7) 전체 시그널 파이프라인
    # ==================================================================
    def generate(self,
                 symbol: str,
                 prices: np.ndarray,
                 volumes: np.ndarray) -> SignalResult:

        raw = self.calc_raw_signals(prices, volumes)
        raw_score = self.normalize_score(raw)

        regime_adj = self.adjust_by_regime(raw_score, symbol)
        final_score = self.adjust_by_meta_strategy(regime_adj, symbol)
        final = self.decision(final_score)

        return SignalResult(
            symbol=symbol,
            score=raw_score,
            raw_signals=raw,
            regime_adj_score=final_score,
            final=final
        )
