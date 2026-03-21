# 경로: E:\AI_TRADING\KR_US_INSTITUTIONAL_BOT\v2\policy\overrides\override_engine.py

from __future__ import annotations

from typing import Dict, Any

from core.types_v2 import Overrides, PolicyContext


class OverrideEngine:
    """
    이벤트/상황에 따라 정책을 덮어쓰는 Override 엔진 스켈레톤.

    TODO:
    - overrides.yaml 기반 규칙 로딩
    - 특정 이벤트/계좌/전략/세션에 대한 force_halt, exposure_cap 등 적용
    """

    def __init__(self) -> None:
        # TODO: E:\AI_TRADING\KR_US_INSTITUTIONAL_BOT\v2\config\overrides.yaml 로드
        pass

    def apply_overrides(
        self,
        base_overrides: Overrides,
        context: Dict[str, Any],
    ) -> Overrides:
        """
        base_overrides 를 입력으로 받고,
        context (account_id, strategy_id, session_id, regime 등)에 따라
        추가 override 를 적용한 결과를 반환.
        """
        # TODO: 실제 override 규칙 적용 로직
        return base_overrides
