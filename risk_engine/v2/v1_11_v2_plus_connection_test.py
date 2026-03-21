# ======================================================================
# v1_11_v2_plus_connection_test.py
# V1.11 Core → V2+ Orchestrator 연결 최종 검증 스크립트
# ======================================================================

from datetime import datetime, timezone
from pprint import pprint

# -----------------------------------------------------------
# 1) V1.11 Dummy Core 엔진 (스키마 100% 일치)
# -----------------------------------------------------------

class DummyRiskEngineV1_11:
    """
    실제 V1.11 RiskEngine의 최소 호환 버전.
    - schema_version: "1.11"
    - meta.engine_version 포함
    - trace 구조 포함
    """

    def run(
        self, 
        snapshot: dict,
        trace_id: str = None,
        run_id: str = None,
        parent_span_id: str = None,
        previous_risk_level: str = None
    ):
        return {
            "schema_version": "1.11",
            "risk_score": 0.45,
            "risk_level": "medium",
            "halt_trading": False,
            "events": [],
            "meta": {
                "engine_version": "1.11",
                "input_snapshot": snapshot,
            },
            "trace": {
                "trace_id": trace_id or "DUMMY_TRACE",
                "span_id": "CORE_SPAN",
                "parent_span_id": parent_span_id,
                "run_id": run_id or "DUMMY_RUN",
            },
        }


# -----------------------------------------------------------
# 2) V2+ Orchestrator (최신 패치본)
# -----------------------------------------------------------

from engine_v2.orchestrator.orchestrator_v2_plus import RiskOrchestratorV2Plus


# -----------------------------------------------------------
# 3) V2+ 테스트 데이터 생성
# -----------------------------------------------------------

def make_factor_engine_input():
    return {
        "symbol": "BTCUSDT",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "windowed_data": {
            "raw_market_state": {
                "last_price": 71500.0,
                "bid": 71490.0,
                "ask": 71510.0,
                "volume_1m": 120.3,
            },
            "ticks": [],
            "bars": [],
        },
    }


# -----------------------------------------------------------
# 4) 연결 테스트 실행
# -----------------------------------------------------------

def run_connection_test():
    print("\n[1] V1.11 Dummy Core → V2+ Orchestrator 연결 테스트 시작")

    # 1) Dummy Core 생성
    core = DummyRiskEngineV1_11()

    # 2) orchestrator 생성
    orchestrator = RiskOrchestratorV2Plus(
        core_engine=core,
        environment="test",
        v2_engine_version="2.0.0",
        v2_schema_version="2.0.0"
    )

    # 3) FactorEngineInput 생성
    data = make_factor_engine_input()

    # 4) 실행
    result = orchestrator.run(
        account_id="ACC001",
        strategy_id="STRAT001",
        session_id="SESS001",
        data=data,
    )

    print("\n[2] 결과 출력 =============================")
    pprint(result)

    # ---------------------------------------------------
    # [핵심 검증 포인트] - 자동 검증
    # ---------------------------------------------------

    print("\n[3] 검증 시작 =============================")

    # 1) core schema_version 검증
    assert result["core_result"]["schema_version"] == "1.11"
    print("✔ core_result.schema_version == 1.11")

    # 2) trace 구조 검증
    trace = result["core_result"]["trace"]
    assert "trace_id" in trace and "span_id" in trace and "run_id" in trace
    print("✔ trace 구조 검증 완료")

    # 3) meta 필드 검증
    meta = result["meta"]
    required_meta_keys = [
        "v2_engine_version",
        "v2_schema_version",
        "core_schema_version",
        "environment",
        "run_id",
        "trace_id",
        "session_id",
        "strategy_id",
        "account_id",
    ]
    for key in required_meta_keys:
        assert key in meta, f"❌ meta.{key} 누락됨"
    print("✔ meta 필드 구조 검증 완료")

    # 4) factor_snapshot 최소 필드 확인
    fs = result["factor_snapshot"]
    assert "rolling_volatility" in fs and "rolling_liquidity" in fs
    print("✔ factor_snapshot 구조 검증 완료")

    # 5) policy_context 구조 검증
    pc = result["policy_context"]
    assert "regime" in pc and "thresholds" in pc and "overrides" in pc
    print("✔ policy_context 구조 검증 완료")

    # 6) aggregation 구조 검증
    assert "account_risk" in result
    assert "strategy_risk" in result
    assert "session_risk" in result
    print("✔ aggregation 구조 검증 완료")

    print("\n🎉 모든 검증 성공! (V1.11 ↔ V2+ 완전 호환)")



if __name__ == "__main__":
    run_connection_test()
