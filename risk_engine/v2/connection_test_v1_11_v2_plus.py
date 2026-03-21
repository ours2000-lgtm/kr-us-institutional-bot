"""
connection_test_v1_11_v2_plus.py
================================

목표:
- V1.11 Core Engine ↔ V2+ Orchestrator 연결 검증
- trace_id / run_id 전달 여부 확인
- core_result.schema_version == "1.11" 확인
- 최종 V2RiskResult 스키마 구조 검증
"""

from pprint import pprint
from datetime import datetime
from uuid import uuid4

# ==========================================================
# Dummy V1.11 Core Engine (V1.11 스키마에 100% 맞춘 버전)
# ==========================================================

class DummyCoreV1_11:
    """
    실제 V1.11 엔진과 동일한 run 시그니처:
    run(input_snapshot, trace_id, run_id, parent_span_id, previous_risk_level)
    """

    def run(
        self,
        input_snapshot,
        trace_id,
        run_id,
        parent_span_id,
        previous_risk_level=None,
    ):
        return {
            "schema_version": "1.11",
            "engine_version": "1.11",
            "risk_score": 0.42,
            "risk_level": "medium",
            "halt_trading": False,
            "events": [],
            "meta": {
                "engine_version": "1.11",
                "received_trace_id": trace_id,
                "received_run_id": run_id,
            },
            "trace": {
                "trace_id": trace_id,
                "span_id": "CORE-SPAN-DUMMY",
                "parent_span_id": parent_span_id,
                "run_id": run_id,
            },
        }


# ==========================================================
# V2+ Orchestrator import
# ==========================================================

from risk_engine_v2_plus import RiskOrchestratorV2Plus, FactorEngineInput


# ==========================================================
# 연결 테스트 함수
# ==========================================================

def run_connection_test():
    print("\n==============================")
    print("  V1.11 ↔ V2+ 연결 테스트 시작")
    print("==============================\n")

    core = DummyCoreV1_11()
    orchestrator = RiskOrchestratorV2Plus(core_engine=core, environment="test")

    # -----------------------------
    # 테스트 입력 구성
    # -----------------------------
    data: FactorEngineInput = {
        "symbol": "BTCUSDT",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "windowed_data": {
            "raw_market_state": {
                "last_price": 71500.0,
                "bid": 71490.0,
                "ask": 71510.0,
            }
        },
    }

    # -----------------------------
    # 실행
    # -----------------------------
    result = orchestrator.run(
        account_id="ACC_TEST",
        strategy_id="STRAT_TEST",
        session_id="SESSION_TEST",
        data=data,
    )

    print("\n[OK] orchestrator.run() 실행 성공\n")

    # -----------------------------
    # CoreResult 검사
    # -----------------------------
    core = result["core_result"]

    print("[검증] CoreResult 스키마 검사:")
    assert "schema_version" in core, "core_result에 schema_version 없음!"
    assert core["schema_version"] == "1.11", "schema_version 불일치!"

    assert "trace" in core, "core_result.trace 없음!"
    assert "trace_id" in core["trace"], "core_result.trace.trace_id 없음!"
    assert "run_id" in core["trace"], "core_result.trace.run_id 없음!"

    print("  - schema_version OK")
    print("  - trace_id/run_id OK")

    # -----------------------------
    # V2RiskResult 스키마 키 검사
    # -----------------------------
    required_keys = [
        "account_risk",
        "strategy_risk",
        "session_risk",
        "core_result",
        "factor_snapshot",
        "policy_context",
        "v2_events",
        "meta",
    ]

    print("\n[검증] V2RiskResult 전체 키 검사:")
    for k in required_keys:
        assert k in result, f"{k} 키가 result에 없습니다!"
        print(f"  - {k} OK")

    print("\n==============================")
    print("  모든 검증 항목 OK")
    print("==============================\n")

    print("\n===== 최종 V2RiskResult 출력 =====")
    pprint(result, width=120)


# ==========================================================
# 실행
# ==========================================================
if __name__ == "__main__":
    run_connection_test()
