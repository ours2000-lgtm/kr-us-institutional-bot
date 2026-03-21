"""
leverage.py — leverage calculator (skeleton)
-------------------------------------------
향후:
  계좌별 포지션 / 담보 / 파생상품 레버리지까지 반영.
지금은 단순 placeholder.
"""

from __future__ import annotations
from typing import Dict, Any


def compute_leverage(
    account_id: str,
    strategy_id: str,
    factor_snapshot: Dict[str, Any],
) -> float:
    """
    TODO:
      - 실제 레버리지 계산 로직 연결
    현재:
      - 1.0 고정 (현물-only 가정)
    """
    return 1.0
