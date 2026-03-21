# 경로: E:\AI_TRADING\KR_US_INSTITUTIONAL_BOT\v2\factor\calculators\imbalance.py

from __future__ import annotations

from typing import Dict, Any


def compute_order_imbalance(windowed_data: Dict[str, Any]) -> float:
    """
    주문 불균형(매수/매도 imbalance) 지표 스켈레톤.

    TODO:
    - bid/ask 체결량 비교
    - 주문장 호가별 누적 잔량 기반 imbalance 계산
    """
    # TODO: 실제 계산 로직 구현
    return 0.0
