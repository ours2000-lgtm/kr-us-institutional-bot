"""
volatility.py — rolling volatility calculator (skeleton)
--------------------------------------------------------
실제 구현은 tick/bars 기반 stddev, ATR 등으로 확장될 예정.
"""

from __future__ import annotations
from typing import Dict, Any


def compute_volatility(windowed_data: Dict[str, Any]) -> float:
    """
    placeholder:
      return 0.12 같은 mock 값
    이후 구현:
      ticks → returns → stddev
      또는 bars → ATR 기반 계산
    """
    # TODO: 실제 계산 로직 구현 예정
    return 0.12
