"""
exposure.py — exposure ratio calculator (skeleton)
--------------------------------------------------
나중에 실제 포지션/잔고 데이터를 기반으로 노출 비율 계산.
지금은 placeholder 수준의 mock 로직.
"""

from __future__ import annotations
from typing import Dict, Any


def compute_exposure_ratio(
    account_id: str,
    strategy_id: str,
    factor_snapshot: Dict[str, Any],
) -> float:
    """
    TODO:
      - account 포지션 / equity 기반 실제 노출 비율 계산
    현재:
      - rolling_volume 등을 참고해 0.0 ~ 1.0 사이의 mock 값 반환
    """
    # placeholder: 항상 0.32로 고정
    return 0.32
