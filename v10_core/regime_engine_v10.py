# =====================================================================
# Regime Engine V10 — 시장 국면 판별 엔진 (Feature 기반 + Microstructure + Risk)
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import numpy as np

from feature_fusion_v10 import FeatureVectorV10
from microstructure_risk_v10 import MicroRiskResultV10


# ---------------------------------------------------------------------
# Regime 상태 정의
# ---------------------------------------------------------------------
class RegimeState:
    BULL = "BULL"
    BEAR = "BEAR"
    NEUTRAL = "NEUTRAL"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    MICRO_RISK = "MICRO_RISK"
    CRASH_WARNING = "CRASH_WARNING"


# ---------------------------------------------------------------------
# Regime 결과 구조체
# ---------------------------------------------------------------------
@dataclass
class RegimeResultV10:
    state: str
    score: float          # -1.0 ~ +1.0
    confidence: float     # 0.0 ~ 1.0
    meta: Dict[str, Any]


# =====================================================================
# 본체
# =====================================================================
class RegimeEngineV10:
    """
    시장 국면을 정밀하게 판단하는 V10 엔진.
    ----------------------------------------------------------
    평가 요소:
    - Feature vector 기반 가격/유동성/변동성/모멘텀
    - Microstructure 위험 지표(점프/스프레드/깊이)
    - 시장 위험도(VIX·환율·BTC 등)
    """

    def __init__(self, config: Dict[str, Any]):

        self.cfg = config.get("REGIME", {})

        # feature 중 어떤 항목을 중요하게 볼지 가중치 설정
        self.weights = np.array(self.cfg.get("feature_weights",
                                             [1.0, 1.2, -1.0, -0.5, 0.5, -1.0, -1.2, -1.1, -1.3, -0.8]),
                                dtype=float)

        # microstructure risk thresholds
        self.micro_threshold = float(self.cfg.get("micro_threshold", 0.65))
        self.crash_threshold = float(self.cfg.get("crash_threshold", 0.80))

        # 시장 위험도 임계값
        self.market_risk_high = float(self.cfg.get("market_risk_high", 0.6))
        self.market_risk_extreme = float(self.cfg.get("market_risk_extreme", 0.8))

    # -----------------------------------------------------------------
    # 1) Feature Vector 기반 국면 스코어 계산
    # -----------------------------------------------------------------
    def compute_feature_score(self, fv: FeatureVectorV10) -> float:
        # 벡터와 가중치를 내적하여 초기 score 생성
        vec = fv.vector
        w = self.weights[:len(vec)]  # 길이 안정화
        score = float(np.dot(vec, w))

        # 점수를 -1 ~ +1로 정규화
        return float(np.tanh(score))

    # -----------------------------------------------------------------
    # 2) market risk feature는 마지막 index라고 가정
    # -----------------------------------------------------------------
    @staticmethod
    def extract_market_risk(fv: FeatureVectorV10) -> float:
        return float(fv.vector[-1])

    # -----------------------------------------------------------------
    # 메인 국면 판별
    # -----------------------------------------------------------------
    def classify(self,
                 fv: FeatureVectorV10,
                 micro: MicroRiskResultV10) -> RegimeResultV10:

        feature_score = self.compute_feature_score(fv)
        market_risk = self.extract_market_risk(fv)

        micro_total = micro.total_risk

        # --------------------------------------------------------------
        # 1) 크래시 위험 → 시스템 전체 보수 모드
        # --------------------------------------------------------------
        if micro_total > self.crash_threshold or market_risk > self.market_risk_extreme:
            return RegimeResultV10(
                state=RegimeState.CRASH_WARNING,
                score=-1.0,
                confidence=1.0,
                meta={
                    "reason": "CRASH: extreme micro risk or extreme market risk",
                    "micro_total": micro_total,
                    "market_risk": market_risk
                }
            )

        # --------------------------------------------------------------
        # 2) 미시구조 위험 높은 경우
        # --------------------------------------------------------------
        if micro_total > self.micro_threshold:
            return RegimeResultV10(
                state=RegimeState.MICRO_RISK,
                score=-0.7,
                confidence=0.8,
                meta={
                    "reason": "high microstructure risk",
                    "micro_total": micro_total
                }
            )

        # --------------------------------------------------------------
        # 3) 유동성 위험 (spread↑ or depth 낮음)
        # depth_ratio feature는 0~1 범위 → 0.5 미만이면 위험
        depth_ratio = fv.meta["raw_features"][4]
        if depth_ratio < 0.5:
            return RegimeResultV10(
                state=RegimeState.LOW_LIQUIDITY,
                score=-0.4,
                confidence=0.7,
                meta={
                    "reason": "low liquidity (depth_ratio<0.5)",
                    "depth_ratio": depth_ratio
                }
            )

        # --------------------------------------------------------------
        # 4) 시장 위험도 중간 수준
        # --------------------------------------------------------------
        if market_risk > self.market_risk_high:
            return RegimeResultV10(
                state=RegimeState.BEAR,
                score=-0.5,
                confidence=0.6,
                meta={
                    "reason": "market risk elevated",
                    "market_risk": market_risk
                }
            )

        # --------------------------------------------------------------
        # 5) Feature 기반 BULL/BEAR 판정
        # --------------------------------------------------------------
        if feature_score > 0.25:
            return RegimeResultV10(
                state=RegimeState.BULL,
                score=feature_score,
                confidence=0.7,
                meta={"feature_score": feature_score}
            )

        if feature_score < -0.25:
            return RegimeResultV10(
                state=RegimeState.BEAR,
                score=feature_score,
                confidence=0.7,
                meta={"feature_score": feature_score}
            )

        # --------------------------------------------------------------
        # 6) 중립 상태
        # --------------------------------------------------------------
        return RegimeResultV10(
            state=RegimeState.NEUTRAL,
            score=feature_score,
            confidence=0.5,
            meta={"feature_score": feature_score}
        )
