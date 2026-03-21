# 경로: E:\AI_TRADING\KR_US_INSTITUTIONAL_BOT\v2\core\engine_base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from .types_v2 import CoreRiskResult


class RiskEngineCore(ABC):
    """
    V1.x / V2.x / V3.x 코어 엔진이 공통으로 따라야 하는 인터페이스.
    - V1.11 실제 구현
    - 향후 V1.12 / V2 Core 등도 이 인터페이스를 구현하면 됨.
    """

    @abstractmethod
    def run(
        self,
        input_snapshot: Dict[str, Any],
        *,
        trace_id: Optional[str] = None,
        run_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        previous_risk_level: Optional[str] = None,
    ) -> CoreRiskResult:
        """
        단일 스냅샷에 대한 리스크 평가 실행.

        input_snapshot 스키마는 V1.11 문서/코드 기준으로 유지.
        trace_id / run_id 등은 상위에서 내려주거나 wrapper에서 생성.
        """
        raise NotImplementedError
