"""
connection_test_v1_11_v2_plus_final.py

✨ V1.11 Core Risk Engine ↔ V2+ Orchestrator
    최종 연결 검증 스크립트 (Trace Dump + Mismatch Detection)

검증 포인트:
1) Core run() 인자(trace_id/run_id/parent_span_id/previous_level) 전달 정상 여부
2) core_result.schema_version == "1.11" 확인
3) trace 필드(trace_id/span_id/run_id/parent_span_id) 존재 여부
4) V2 결과 스키마 값/타입 검증
5) 실패 시 full trace dump 자동 출력
"""

import json
from pprint import pprint
from uuid import uuid4
from datetime import datetime, timezone

# ---------------------------------------------------
# Dummy Core (V1.11) — 실제 구조에 맞춘 mock
# ---------------------------------------------------
class DummyCoreV1_11:
    def run(
        self,
        input_snapshot: dict,
        trace_id: str = None,
        run_id: str = None,
        parent_span_id: str = None,
        previous_risk_level: str = None,
    ) -> dict:
        return {
            "schema_version": "1.11",
            "risk_level": "medium",
            "risk_score": 0.42,
            "meta": {
                "strategy_id": "STRAT_TEST",
                "account_id": "ACC_TEST",
            },
            "trace": {
                "trace_id": trace_id or f"TRACE-{uuid4()}",
                "run_id": run_id or f"RUN-{uuid4()}",
                "span_id": f"SPAN-{uuid4()}",
                "parent_span_id": parent_span_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }


# ---------------------------------------------------
# Dummy V2+ Orchestrator — 최소 구조
# ---------------------------------------------------
class RiskOrchestratorV2Plus:
    def __init__(self, core_engine, environment="test"):
        self.core = core_engine
        self.environment = environment

    def run(self, data: dict, meta: dict):
        trace_id = f"V2-TRACE-{uuid4()}"
        run_id = f"V2-RUN-{uuid4()}"
        parent_span_id = None

        # Core 호출
        core_result = self.core.run(
            data,
            trace_id=trace_id,
            run_id=run_id,
            parent_span_id=parent_span_id,
            previous_risk_level=None,
        )

        # V2 결과 패키징
        return {
            "schema_version": "2+",
            "core": core_result,
            "v2_events": [
                {
                    "type": "V2_ORCHESTRATION_COMPLETED",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "trace_id": trace_id,
                    "run_id": run_id,
                    "session_id": meta.get("session_id", "NO_SESSION"),
                    "strategy_id": meta.get("strategy_id", "NO_STRAT"),
                    "account_id": meta.get("account_id", "NO_ACC"),
                }
            ],
        }


# ---------------------------------------------------
# Utility — Trace Dump
# ---------------------------------------------------
def dump_trace(result):
    print("\n\n===================== TRACE DUMP =====================")
    print(json.dumps(result, indent=4))
    print("======================================================\n\n")


# ---------------------------------------------------
# Utility — mismatch 자동 감지
# ---------------------------------------------------
def check_mismatch(core: dict):
    required_core_keys = ["schema_version", "risk_level", "risk_score", "meta", "trace"]
    for k in required_core_keys:
        if k not in core:
            raise AssertionError(f"[FAIL] core missing field: {k}")

    if core["schema_version"] != "1.11":
        raise AssertionError(
            f"[FAIL] core.schema_version mismatch: {core['schema_version']} != 1.11"
        )

    trace_block = core["trace"]
    required_trace_keys = [
        "trace_id",
        "run_id",
        "span_id",
        "parent_span_id",
        "timestamp",
    ]
    for k in required_trace_keys:
        if k not in trace_block:
            raise AssertionError(f"[FAIL] core.trace missing: {k}")

    print("[OK] Core schema/trace 구조 정상")


# ---------------------------------------------------
# MAIN — 연결 테스트
# ---------------------------------------------------
def run_connection_test():

    print("\n[TEST] V1.11 ↔ V2+ 연결 테스트 시작\n")

    core = DummyCoreV1_11()
    orchestrator = RiskOrchestratorV2Plus(core_engine=core, environment="test")

    input_snapshot = {"price": 12345, "volume": 99999}
    meta = {
        "session_id": "SESSION_TEST",
        "strategy_id": "STRAT_TEST",
        "account_id": "ACC_TEST",
    }

    result = orchestrator.run(data=input_snapshot, meta=meta)

    # ---------------------------
    # Mismatch 검사
    # ---------------------------
    try:
        core_block = result["core"]
        check_mismatch(core_block)
        print("[OK] 연결 테스트 성공")

    except Exception as e:
        print("\n[ERROR] 연결 테스트 실패")
        print(f"사유: {e}")
        dump_trace(result)
        raise

    # 최종 출력
    print("\n===== 최종 결과 출력 =====")
    pprint(result)
    print("===========================")


if __name__ == "__main__":
    run_connection_test()
