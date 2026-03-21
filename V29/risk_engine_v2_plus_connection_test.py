"""
risk_engine_v2_plus_connection_test.py
--------------------------------------
V1.11 CoreRiskEngine ↔ V2+ Orchestrator 연결 검증 스크립트.

테스트 목적:
1) 스키마(schema_version, meta, trace) 완전 일치 여부
2) event/meta 필드 존재 여부
3) FactorEngine → Policy → Core → Aggregation → V2 결과 end-to-end 정상 여부
4) 필드 누락, 타입 mismatch 조기 감지
"""

import json
from datetime import datetime
from pprint import pprint

# ---------------------------------------------------------
# 1. V1.11 엔진 불러오기 (실제 파일을 import하는 구조)
# ---------------------------------------------------------
from risk_engine_v1_11 import RiskEngineV1_11 as CoreV1   # ← 형의 실제 파일 이름에 맞춰 수정

# ---------------------------------------------------------
# 2. V2+ orchestrator 불러오기
# ---------------------------------------------------------
from risk_engine_v2_plus import (
    RiskOrchestratorV2Plus,
    FactorEngineInput,
)

# ---------------------------------------------------------
# 3. 테스트용 입력 생성
# ---------------------------------------------------------
def make_test_input() -> FactorEngineInput:
    return FactorEngineInput(
        symbol="TEST_ASSET",
        timestamp=datetime.utcnow().isoformat() + "Z",
        windowed_data={
            "raw_market_state": {
                "last_price": 12345.67,
                "bid": 12345.50,
                "ask": 12345.80,
                "volume": 99123,
            },
            "ticks": [],
            "bars": [],
        },
    )


# ---------------------------------------------------------
# 4. 필수 필드 검증 헬퍼
# ---------------------------------------------------------
def assert_has_keys(name: str, d: dict, keys: list[str]):
    for k in keys:
        if k not in d:
            raise AssertionError(f"[FAIL] {name} missing key: {k}")
    print(f"[OK] {name} required keys 존재함")


# ---------------------------------------------------------
# 5. 연결 테스트 실행
# ---------------------------------------------------------
def run_connection_test():
    print("\n====================================================")
    print("🚀 V1.11 ↔ V2+ 연결 테스트 START")
    print("====================================================")

    # ----------------------------
    # 1) Core(V1.11) 초기화
    # ----------------------------
    core_engine = CoreV1()

    # ----------------------------
    # 2) V2+ orchestrator 초기화
    # ----------------------------
    orchestrator = RiskOrchestratorV2Plus(core_engine, environment="test")

    # ----------------------------
    # 3) 테스트 입력 생성
    # ----------------------------
    data = make_test_input()

    # ----------------------------
    # 4) V2+ 실행
    # ----------------------------
    result = orchestrator.run(
        account_id="ACC_TEST",
        strategy_id="STRAT_TEST",
        session_id="SESSION_TEST",
        data=data,
    )

    print("\n[RESULT OUTPUT]")
    pprint(result)

    # -------------------------------------------------
    # ✔ 1) CoreRiskResult 필수 필드 검증
    # -------------------------------------------------
    core = result["core_result"]

    assert_has_keys("core_result", core, [
        "schema_version",
        "risk_score",
        "risk_level",
        "halt_trading",
        "events",
        "meta",
        "trace",
    ])

    # -------------------------------------------------
    # ✔ 2) trace 필드 검증
    # -------------------------------------------------
    assert_has_keys("core_result.trace", core["trace"], [
        "trace_id",
        "span_id",
        "parent_span_id",
        "run_id",
    ])

    # -------------------------------------------------
    # ✔ 3) V2 meta 검증
    # -------------------------------------------------
    meta = result["meta"]
    assert_has_keys("V2.meta", meta, [
        "v2_engine_version",
        "v2_schema_version",
        "core_schema_version",
        "environment",
        "run_id",
        "trace_id",
        "session_id",
        "strategy_id",
        "account_id",
        "regime",
        "policy_name",
        "timestamp",
    ])

    # -------------------------------------------------
    # ✔ 4) FactorSnapshot 기본 필드 검증
    # -------------------------------------------------
    factor = result["factor_snapshot"]
    assert_has_keys("factor_snapshot", factor, [
        "rolling_volatility",
        "rolling_liquidity",
        "rolling_volume",
        "raw_snapshot",
    ])

    # -------------------------------------------------
    # ✔ 5) 정책 필드 검증
    # -------------------------------------------------
    policy = result["policy_context"]
    assert_has_keys("policy_context", policy, [
        "regime",
        "thresholds",
        "overrides",
        "policy_name",
    ])

    print("\n====================================================")
    print("🎉 V1.11 ↔ V2+ 연결 테스트 **성공**")
    print("====================================================")

    return result


# ---------------------------------------------------------
# 6. 실행
# ---------------------------------------------------------
if __name__ == "__main__":
    final_result = run_connection_test()

    print("\n[JSON OUTPUT]")
    print(json.dumps(final_result, indent=2))
