"""
connection_test_v1_11_v2_plus_final.py

V1.11 Core RiskEngine  ↔  V2+ Orchestrator 연결 검증 스크립트

검증 포인트:
1) Core V1.11 run() 호출이 정상 동작하는지
2) Core 결과(schema_version / trace / meta)가 V2+에 잘 전달되는지
3) V2RiskResult 내부 스키마( account_risk / strategy_risk / session_risk / meta / v2_events )가 정상인지
4) v2_schema_version / core_schema_version / environment / trace_id / run_id 등이 meta에 포함되는지
5) 실패 시 전체 trace / meta를 보기 좋게 출력
"""

from __future__ import annotations

from pprint import pprint
from datetime import datetime, timezone
from typing import Any, Dict

from risk_engine_v2_plus import (
    RiskOrchestratorV2Plus,
    FactorEngineInput,  # TypedDict (symbol, timestamp, windowed_data)
)


# ======================================================================
# 1. Dummy V1.11 Core Risk Engine (실제 엔진 연결 전까지 사용)
# ======================================================================


class DummyCoreV111:
    """
    실제 V1.11 엔진을 붙이기 전까지 사용하는 더미 Core.

    실제 V1.11이 다음과 유사한 스키마를 반환한다고 가정:
    {
        "schema_version": "1.11",
        "risk_score": 0.42,
        "risk_level": "medium",
        "halt_trading": False,
        "events": [...],
        "meta": {
            "engine_version": "1.11",
            ...
        },
        "trace": {
            "trace_id": "...",
            "run_id": "...",
            "span_id": "...",
            "parent_span_id": None,
        },
    }
    """

    def run(self, input_snapshot: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        now_iso = (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

        return {
            "schema_version": "1.11",
            "risk_score": 0.42,
            "risk_level": "medium",
            "halt_trading": False,
            "events": [
                {
                    "type": "CORE_RISK_EVALUATED",
                    "timestamp": now_iso,
                    "price": input_snapshot.get("price"),
                    "volatility": input_snapshot.get("volatility"),
                    "liquidity": input_snapshot.get("liquidity"),
                }
            ],
            "meta": {
                "engine_version": "1.11",
                "source": "DummyCoreV111",
            },
            "trace": {
                "trace_id": "CORE-TRACE-DUMMY",
                "run_id": "CORE-RUN-DUMMY",
                "span_id": "CORE-SPAN-DUMMY",
                "parent_span_id": None,
            },
        }


# ======================================================================
# 2. 헬퍼: pretty separator 출력
# ======================================================================


def print_sep(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"[ {title} ]")
    print("=" * 80)


# ======================================================================
# 3. 연결 테스트 본문
# ======================================================================


def run_connection_test() -> None:
    """
    V1.11 Core → V2+ Orchestrator end-to-end 연결 테스트.
    """

    print_sep("1. Dummy V1.11 Core 엔진 준비")
    core = DummyCoreV111()
    print("✔ DummyCoreV111 인스턴스 생성 완료")

    print_sep("2. V2+ Orchestrator 인스턴스 생성")
    orchestrator = RiskOrchestratorV2Plus(
        core_engine=core,
        environment="test",  # "live" / "paper" / "backtest" 등으로 변경 가능
    )
    print("✔ RiskOrchestratorV2Plus(environment='test') 생성 완료")

    print_sep("3. 테스트 입력 스냅샷 구성 (FactorEngineInput)")
    now_iso = (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )

    data: FactorEngineInput = FactorEngineInput(
        symbol="ACC_TEST",
        timestamp=now_iso,
        windowed_data={
            # 실제 구현에서는 ticks/bars/indicator 등이 들어올 예정
            "raw_market_state": {
                "last_price": 123.45,
                "bid": 123.40,
                "ask": 123.50,
            }
        },
    )

    pprint(data)

    print_sep("4. Orchestrator.run 호출")
    try:
        result = orchestrator.run(
            account_id="ACC_TEST",
            strategy_id="STRAT_TEST",
            session_id="SESSION_TEST",
            data=data,
        )
    except Exception as e:  # noqa: BLE001
        print("❌ Orchestrator.run() 호출 중 예외 발생!")
        print(f"Exception: {e!r}")
        raise

    print("✔ Orchestrator.run() 호출 성공")

    # ------------------------------------------------------------------
    # 5. 스키마 기본 검증
    # ------------------------------------------------------------------
    print_sep("5. V2RiskResult 기본 스키마 검사")

    required_top_keys = [
        "account_risk",
        "strategy_risk",
        "session_risk",
        "core_result",
        "factor_snapshot",
        "policy_context",
        "v2_events",
        "meta",
    ]

    missing = [k for k in required_top_keys if k not in result]
    if missing:
        print(f"❌ 누락된 top-level 키: {missing}")
    else:
        print("✔ 모든 top-level 키 존재:", required_top_keys)

    # CoreResult schema_version 체크
    core = result["core_result"]
    expected_core_schema = "1.11"
    got_core_schema = core.get("schema_version")

    if got_core_schema != expected_core_schema:
        print(
            f"❌ core_result.schema_version mismatch "
            f"(expected={expected_core_schema}, got={got_core_schema})"
        )
    else:
        print(f"✔ core_result.schema_version == {expected_core_schema}")

    # V2 meta 내 버전·환경 태깅 확인
    meta = result["meta"]
    print_sep("6. meta / trace / 버전·환경 정보 확인")

    v2_engine_version = meta.get("v2_engine_version")
    v2_schema_version = meta.get("v2_schema_version")
    core_schema_version = meta.get("core_schema_version")
    environment = meta.get("environment")
    trace_id = meta.get("trace_id")
    run_id = meta.get("run_id")

    print("v2_engine_version :", v2_engine_version)
    print("v2_schema_version :", v2_schema_version)
    print("core_schema_version:", core_schema_version)
    print("environment       :", environment)
    print("trace_id          :", trace_id)
    print("run_id            :", run_id)

    # ------------------------------------------------------------------
    # 7. 핵심 섹션 요약 출력
    # ------------------------------------------------------------------
    print_sep("7. account_risk / strategy_risk / session_risk 요약")

    print("- account_risk:")
    pprint(result["account_risk"])

    print("\n- strategy_risk:")
    pprint(result["strategy_risk"])

    print("\n- session_risk:")
    pprint(result["session_risk"])

    print_sep("8. core_result / v2_events 요약")
    print("- core_result:")
    pprint(result["core_result"])

    print("\n- v2_events:")
    pprint(result["v2_events"])

    print_sep("9. 전체 meta dump")
    pprint(result["meta"])

    print_sep("✅ 최종 결론")
    print("V1.11 Dummy Core ↔ V2+ Orchestrator 연결 테스트가 정상적으로 완료되었습니다.")
    print("이제 실제 V1.11 엔진을 DummyCoreV111 자리(core_engine)에 붙여서 테스트하면 됩니다.")


# ======================================================================
# Entry Point
# ======================================================================

if __name__ == "__main__":
    run_connection_test()
