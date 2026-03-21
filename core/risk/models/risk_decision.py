from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class RiskDecision:
    """
    RiskManager v2 decision result (SSOT)

    역할:
    - 주문 평가 결과를 구조화하여 반환
    - 로그 / evidence / 테스트에서 동일하게 사용

    필드 정의:

    allowed:
        True  -> 주문 허용
        False -> 주문 차단

    decision:
        "ALLOW" | "DENY"
        (allowed의 문자열 표현, 로그/증적 가독성 목적)

    reasons:
        이번 evaluate(order) 실행 중 발생한 직접적인 차단 사유 목록
        예:
            - INVALID_QTY
            - MAX_POSITION_EXCEEDED
            - INSUFFICIENT_POSITION

    current_position_qty:
        현재 포지션 수량 (조회 실패 시 None 가능)

    projected_position_qty:
        주문 적용 후 예상 포지션 수량
        계산 실패 시 None 가능

    block_reason:
        현재 RiskManager의 전역 block latch 사유
        예:
            - TRADING_BLOCKED
            - RECON_QTY_MISMATCH
            - BROKER_SNAPSHOT_SUPPLIER_FAILED

        ※ reasons와 구분됨:
           - reasons      = 이번 주문 자체 문제
           - block_reason = 시스템 상태 문제
    """

    allowed: bool
    decision: str  # "ALLOW" | "DENY"
    reasons: List[str]

    current_position_qty: Optional[int]
    projected_position_qty: Optional[int]

    block_reason: Optional[str]