"""
volume.py — rolling volume calculator (skeleton)
------------------------------------------------
실제 구현은 N틱 누적 거래량, bar volume 합계 등 기반.
"""

from __future__ import annotations
from typing import Dict, Any


def compute_volume(windowed_data: Dict[str, Any]) -> float:
    """
    placeholder:
      return 15000.0 같은 mock 값
    이후 구현:
      ticks → size 누적
      bars → volume 합산
    """
    # TODO: 실제 계산 로직 구현 예정
    return 15000.0
