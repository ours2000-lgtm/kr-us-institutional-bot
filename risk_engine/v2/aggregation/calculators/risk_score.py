"""
risk_score.py — account-level risk score adjuster (skeleton)
------------------------------------------------------------
CoreRiskResult의 base_risk_score를
exposure / leverage / policy overrides와 결합해 계좌 레벨 점수로 조정.
"""

from __future__ import annotations
from typing import Dict, Any
import math


def compute_account_risk_score(
    base_risk_score: float,
    exposure_ratio: float,
    leverage: float,
    policy_context: Dict[str, Any],
) -> float:
    """
    간단 스켈레톤:
      base_risk_score를 중심으로
      노출도와 레버리지에 따라 약간 가중.
    나중에:
      - aggregation.yaml 기반 정교한 공식 적용
      - overrides.force_halt 시 score 강제 1.0 등
    """
    score = base_risk_score

    # 노출도 영향 (노출이 클수록 리스크 증가)
    score *= (1.0 + 0.5 * exposure_ratio)

    # 레버리지 영향 (레버리지 1 초과 시 리스크 증가)
    if leverage > 1.0:
        score *= min(1.5, 1.0 + 0.2 * (leverage - 1.0))

    # overrides 반영 (force_halt시 강제 상향 등은 이후 구현)
    overrides = policy_context.get("overrides", {}) or {}
    if overrides.get("force_halt"):
        score = 1.0

    # 0.0 ~ 1.0 클램프 + 소수점 정리
    score = max(0.0, min(1.0, score))
    if math.isnan(score):
        score = 1.0

    return round(score, 4)
