# =====================================================================
# Feature Fusion Engine V10
# 시장 데이터 + 유동성 + 변동성 + 미시구조 위험을 하나의 벡터로 통합
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
import numpy as np

from microstructure_risk_v10 import MicroRiskResultV10


# ---------------------------------------------------------------------
# Feature 결과 구조체
# ---------------------------------------------------------------------
@dataclass
class FeatureVectorV10:
    vector: np.ndarray          # 최종 feature 벡터
    names: List[str]            # 각 feature 이름
    meta: Dict[str, Any]        # 부가 정보


# =====================================================================
# 본체
# =====================================================================
class FeatureFusionEngineV10:
    """
    시장 특징(Features)을 하나의 통합 벡터로 결합하는 엔진.
    ---------------------------------------------------------
    입력값 예:
    - price series (list or ndarray)
    - volume
    - spread
    - depth 정보
    - microstructure risk (from E6)
    - 시장 위험 지표 (VIX, KRWUSD, BTC volatility 등)

    출력:
    - FeatureVectorV10 (정규화 벡터 + feature 이름 리스트)
    """

    def __init__(self, config: Dict[str, Any]):
        self.cfg = config.get("FEATURES", {})
        self.ret_window = int(self.cfg.get("ret_window", 5))
        self.vol_window = int(self.cfg.get("vol_window", 20))

    # -----------------------------------------------------------------
    # 1) 수익률 Feature
    # -----------------------------------------------------------------
    def compute_returns(self, prices: np.ndarray) -> float:
        if prices is None or len(prices) < 2:
            return 0.0
        return float((prices[-1] - prices[-2]) / max(prices[-2], 1e-9))

    # -----------------------------------------------------------------
    # 2) 모멘텀 Feature (n-period)
    # -----------------------------------------------------------------
    def compute_momentum(self, prices: np.ndarray) -> float:
        if prices is None or len(prices) < self.ret_window:
            return 0.0
        return float((prices[-1] - prices[-self.ret_window]) /
                     max(prices[-self.ret_window], 1e-9))

    # -----------------------------------------------------------------
    # 3) 변동성 Feature
    # -----------------------------------------------------------------
    def compute_volatility(self, prices: np.ndarray) -> float:
        if prices is None or len(prices) < self.vol_window:
            return 0.0
        window = prices[-self.vol_window:]
        returns = np.diff(window) / window[:-1]
        return float(np.std(returns))

    # -----------------------------------------------------------------
    # 4) 유동성 Feature (spread%)
    # -----------------------------------------------------------------
    @staticmethod
    def compute_liquidity(spread_pct: float) -> float:
        return float(spread_pct)

    # -----------------------------------------------------------------
    # 5) 호가 깊이 Feature
    # -----------------------------------------------------------------
    @staticmethod
    def compute_depth_ratio(bid_depth: float, ask_depth: float) -> float:
        total = bid_depth + ask_depth
        if total <= 0:
            return 0.0
        return float(bid_depth / total)

    # -----------------------------------------------------------------
    # 6) 미시구조 위험 Feature (from MicroRiskResultV10)
    # -----------------------------------------------------------------
    def extract_micro_features(self, m: MicroRiskResultV10) -> List[float]:
        return [
            m.spread_risk,
            m.depth_risk,
            m.pressure_risk,
            m.jump_risk,
            m.total_risk
        ]

    # -----------------------------------------------------------------
    # 7) Feature Normalization
    # -----------------------------------------------------------------
    @staticmethod
    def normalize_vector(vec: List[float]) -> np.ndarray:
        arr = np.array(vec, dtype=float)
        if np.all(arr == 0):
            return arr
        # 정규화 (L2)
        norm = np.linalg.norm(arr) + 1e-9
        return arr / norm

    # -----------------------------------------------------------------
    # 8) 메인 Feature Fusion 함수
    # -----------------------------------------------------------------
    def fuse(self,
             prices: np.ndarray,
             spread_pct: float,
             bid_depth: float,
             ask_depth: float,
             micro: MicroRiskResultV10,
             market_risk: float = 0.0) -> FeatureVectorV10:

        features = []
        names = []

        # --- 가격 기반 ---
        ret = self.compute_returns(prices)
        features.append(ret); names.append("return")

        mom = self.compute_momentum(prices)
        features.append(mom); names.append("momentum")

        vol = self.compute_volatility(prices)
        features.append(vol); names.append("volatility")

        # --- 유동성 ---
        liq = self.compute_liquidity(spread_pct)
        features.append(liq); names.append("spread_pct")

        depth_ratio = self.compute_depth_ratio(bid_depth, ask_depth)
        features.append(depth_ratio); names.append("depth_ratio")

        # --- 미시구조 위험 ---
        micro_f = self.extract_micro_features(micro)
        mic_names = ["micro_spread", "micro_depth", "micro_pressure", "micro_jump", "micro_total"]
        features.extend(micro_f); names.extend(mic_names)

        # --- 시장 위험 (optional feature) ---
        features.append(float(market_risk))
        names.append("market_risk")

        # --- 정규화 ---
        normalized = self.normalize_vector(features)

        return FeatureVectorV10(
            vector=normalized,
            names=names,
            meta={
                "raw_features": features,
                "micro_cluster": micro.cluster
            }
        )
