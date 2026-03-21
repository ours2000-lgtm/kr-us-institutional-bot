"""
core_wrapper.py — V1.11 Core → V2 공통 인터페이스 어댑터

역할:
- V2 레이어에서 V1.11 RiskEngine 코어를 사용할 수 있도록 감싸는 Adapter.
- EngineBase 인터페이스를 구현해서 Orchestrator / 상위 레이어가
  "버전과 상관없이" 동일한 방식으로 코어 엔진을 호출할 수 있게 해준다.

중요 포인트:
- V1.11 엔진의 run(...) 시그니처를 그대로 노출하지 않고, EngineBase.run(...)으로 통일.
- schema_version 체크를 통해 V1.x 교체 시 호환성 문제를 조기에 감지.
- 이후 V1.12 / V2 Core로 바뀌어도, 이 레이어만 교체하면 상위 코드는 그대로 유지.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .engine_base import EngineBase, RiskEngineInput, RiskEngineOutput


class V1_11CoreAdapter(EngineBase):
    """
    V1.11 RiskEngine 코어를 V2 공통 인터페이스(EngineBase)로 감싸는 어댑터.

    사용 예시 (orchestrator 등에서):

        from v1.risk_engine_v1_11 import RiskEngineV1_11

        core_v1 = RiskEngineV1_11(...)
        core_adapter = V1_11CoreAdapter(core_v1, expected_schema_version="1.11")

        result = core_adapter.run(
            {
                "price": 123.45,
                "volatility": 0.12,
                "liquidity": 0.8,
                "timestamp": "2025-12-12T09:00:00Z",
                "symbol": "005930",
                "market": "KR",
            }
        )

    설계 원칙:
    - V2 세계에서는 EngineBase.run(...)만 바라본다.
    - 내부에서만 V1.11의 input 스냅샷 구조로 매핑한다.
    - core_result의 schema_version을 검사해서 호환성 문제를 조기에 감지한다.
    """

    def __init__(
        self,
        core_engine: Any,
        expected_schema_version: str = "1.11",
        strict_schema_check: bool = False,
    ) -> None:
        """
        :param core_engine:
            실제 V1.11 RiskEngine 인스턴스
            (예: risk_engine_v1_11.RiskEngineV1_11)

        :param expected_schema_version:
            V2에서 기대하는 V1 Core 스키마 버전.
            기본값은 "1.11" 이며, V1.x 교체 시에도 여기만 조정하면 된다.

        :param strict_schema_check:
            True 인 경우, schema_version mismatch가 발생하면 예외를 던진다.
            False 인 경우, TODO: 로깅 후 계속 진행하는 정책 사용.
        """
        self._core_engine = core_engine
        self._expected_schema_version = expected_schema_version
        self._strict_schema_check = strict_schema_check

    # ------------------------------------------------------------------
    # EngineBase 인터페이스 구현
    # ------------------------------------------------------------------
    def run(self, data: RiskEngineInput) -> RiskEngineOutput:
        """
        V2 공통 인터페이스.

        입력: RiskEngineInput (V2 표준 인풋)
        - price        : float
        - volatility   : float
        - liquidity    : float
        - timestamp    : str (ISO8601)
        - symbol       : str (옵션)
        - market       : str (옵션)
        - 기타 필드는 raw_input 등에 포함 가능

        출력: RiskEngineOutput (V1.11 Core 결과를 그대로 or 변환해서 전달)

        내부 동작:
        1. V2 Input → V1.11 input 스냅샷으로 매핑
        2. V1.11 코어의 run(...) 호출
        3. schema_version 검증
        4. 필요 시 RiskEngineOutput 스키마로 변환/래핑
        """

        # 1) V2 Input → V1.11 입력 스냅샷으로 최소 매핑
        v1_snapshot: Dict[str, Any] = {
            "price": data.get("price"),
            "volatility": data.get("volatility"),
            "liquidity": data.get("liquidity"),
            "timestamp": data.get("timestamp"),
            # 선택적으로 symbol/market을 raw에 묶어서 넘길 수도 있다.
            "raw": {
                "symbol": data.get("symbol"),
                "market": data.get("market"),
                "raw_input": dict(data),  # 전체 입력 백업 (옵션)
            },
        }

        # 2) V1.11 코어 호출
        # 실제 V1.11 run 시그니처에 맞게 trace_id/run_id/parent_span_id 등을
        # 추가 인자로 넘기고 싶다면 아래 TODO 부분에서 확장하면 된다.
        core_result: Dict[str, Any] = self._core_engine.run(v1_snapshot)  # type: ignore[arg-type]

        # 3) schema_version 검증
        self._validate_core_schema(core_result)

        # 4) RiskEngineOutput 형태로 확실히 보정해서 반환
        #   - 현재는 V1.11 결과 스키마가 거의 그대로 RiskEngineOutput과
        #     매칭된다는 가정 하에, 최소한의 타입 래핑만 수행.
        return self._normalize_core_result(core_result)

    # ------------------------------------------------------------------
    # 내부 유틸 메서드들
    # ------------------------------------------------------------------
    def _validate_core_schema(self, core_result: Dict[str, Any]) -> None:
        """
        V1.11 코어의 schema_version이 기대 버전과 맞는지 확인.

        - mismatch 발생 시:
          strict_schema_check=True  → ValueError
          strict_schema_check=False → TODO: 로깅 후 계속 진행
        """
        schema_version = core_result.get("schema_version")
        if schema_version != self._expected_schema_version:
            msg = (
                f"[V1_11CoreAdapter] Core schema_version mismatch: "
                f"expected={self._expected_schema_version}, got={schema_version}"
            )
            if self._strict_schema_check:
                raise ValueError(msg)
            # TODO: 여기서 logger를 붙여서 WARNING 로그 남기기
            # 예: logger.warning(msg)
            # 지금은 스켈레톤 단계이므로 일단 pass
            pass

    def _normalize_core_result(self, core_result: Dict[str, Any]) -> RiskEngineOutput:
        """
        V1.11 결과 딕셔너리를 RiskEngineOutput 타입으로 정리.

        현재 설계 상 V1.11 결과 스키마와 RiskEngineOutput 스키마가
        거의 동일하다고 가정하고, 최소한의 디폴트값만 채워 넣는다.
        """

        # 필수 필드(기대 스키마 기준)
        schema_version = core_result.get("schema_version", "1.11")
        risk_score = float(core_result.get("risk_score", 0.0))
        risk_level = core_result.get("risk_level", "low")  # type: ignore[assignment]
        halt_trading = bool(core_result.get("halt_trading", False))

        # 선택 필드
        events = core_result.get("events") or []
        meta = core_result.get("meta") or {}
        trace = core_result.get("trace") or {}

        # 여기서 타입을 RiskEngineOutput으로 강제 래핑
        normalized: RiskEngineOutput = {
            "schema_version": schema_version,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "halt_trading": halt_trading,
            "events": events,
            "meta": meta,
            "trace": trace,
        }
        return normalized


# ======================================================================
# 간단 수동 테스트용 블록 (원하면 삭제해도 됨)
# ======================================================================
if __name__ == "__main__":

    class DummyV1Core:
        """V1.11 RiskEngine을 흉내내는 더미 엔진 (연결 테스트용)."""

        def run(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "schema_version": "1.11",
                "risk_score": 0.42,
                "risk_level": "medium",
                "halt_trading": False,
                "events": [],
                "meta": {
                    "engine_version": "1.11",
                    "received_at": snapshot.get("timestamp"),
                },
                "trace": {
                    "trace_id": "DUMMY-TRACE",
                    "span_id": "DUMMY-SPAN",
                    "parent_span_id": None,
                    "run_id": "DUMMY-RUN",
                },
            }

    dummy_core = DummyV1Core()
    adapter = V1_11CoreAdapter(dummy_core, expected_schema_version="1.11")

    sample_input: RiskEngineInput = {
        "price": 100_000.0,
        "volatility": 0.15,
        "liquidity": 0.75,
        "timestamp": "2025-12-12T09:00:00Z",
        "symbol": "TEST",
        "market": "KR",
    }

    from pprint import pprint

    print("[TEST] V1_11CoreAdapter.run(...) 결과 ↓")
    result = adapter.run(sample_input)
    pprint(result)
