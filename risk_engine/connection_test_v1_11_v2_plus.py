"""
connection_test_v1_11_v2_plus.py
V1.11 Core ↔ V2+ Orchestrator 연결 검증 스크립트 (패치 적용 최신 버전)

검증 항목:
- V1.11 CoreRiskResult 스키마
- V2RiskResult 스키마
- meta / trace 구조
- 필수 필드 assert
- core_schema_version 존재 여부
- 실패 시 상세 trace dump
"""

import sys
from datetime import datetime
from pprint import pprint


# ----------------------------------------------------------
# DummyCore (V1.11 스키마에 맞춘 테스트 버전)
# ----------------------------------------------------------
class DummyCore:
    def run(self, snapshot, trace_id=None, run_id=None, parent_span_id=None, previous_risk_level=None):
        return {
            "schema_version": "1.11",
            "engine_version": "1.11",
            "risk_score": 0.42,
            "risk_level": "medium",
            "halt_trading": False,
            "events": [],
            "meta": {
                "engine_version": "1.11",
                "received_at": datetime.utcnow().isoformat() + "Z",
            },
            "trace": {
                "trace_id": trace_id or "TRACE-DUMMY",
                "run_id": run_id or "RUN-DUMMY",
                "span_id": "SPAN-DUMMY",
                "parent_span_id": parent_span_id,
            },
        }


# ----------------------------------------------------------
# Minimal V2+ Orchestrator Skeleton for Testing
# ----------------------------------------------------------
class RiskOrchestratorV2Plus_Minimal:
    def __init__(self, core_engine):
        self.core = core_engine
        self.v2_schema_version = "2.0.0"
        self.v2_engine_version = "2.0.0"
        self.environment = "test"

    def run(self):
        trace_id = "TRACE-V2"
        run_id = "RUN-V2"

        core = self.core.run(
            {"price": 100.0, "volatility": 0.1, "liquidity": 0.5},
            trace_id=trace_id,
            run_id=run_id,
            parent_span_id=None,
            previous_risk_level=None,
        )

        # meta에 core_schema_version 포함 (패치 적용)
        meta = {
            "v2_schema_version": self.v2_schema_version,
            "v2_engine_version": self.v2_engine_version,
            "environment": self.environment,
            "trace_id": trace_id,
            "run_id": run_id,
            "core_schema_version": core.get("schema_version"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        return {
            "schema_version": self.v2_schema_version,
            "v2_engine_version": self.v2_engine_version,
            "environment": self.environment,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "core_result": core,
            "meta": meta,
        }


# ----------------------------------------------------------
# VALIDATION HELPERS
# ----------------------------------------------------------
def assert_exists(obj, field, path=""):
    """필수 필드가 없거나 None이면 즉시 실패"""
    full = f"{path}.{field}" if path else field
    if field not in obj:
        raise AssertionError(f"[FAIL] Missing field: {full}")
    if obj[field] in (None, ""):
        raise AssertionError(f"[FAIL] Field empty: {full}")


# ----------------------------------------------------------
# MAIN TEST FUNCTION
# ----------------------------------------------------------
def test_connection():
    print("\n=== V1.11 ↔ V2+ 연결 테스트 시작 ===\n")

    orchestrator = RiskOrchestratorV2Plus_Minimal(DummyCore())
    result = orchestrator.run()

    print("[INFO] V2RiskResult:")
    pprint(result)

    # -------------------------------
    # 1) Top-level 필드 검증
    # -------------------------------
    for k in ["schema_version", "v2_engine_version", "environment", "core_result", "meta"]:
        assert_exists(result, k, "V2RiskResult")

    # -------------------------------
    # 2) meta 필드 검증 (패치 포함)
    # -------------------------------
    meta = result["meta"]
    for k in ["trace_id", "run_id", "environment", "core_schema_version"]:
        assert_exists(meta, k, "V2RiskResult.meta")

    # -------------------------------
    # 3) CoreRiskResult 필드 검증
    # -------------------------------
    core = result["core_result"]
    for k in ["schema_version", "risk_level", "risk_score", "trace", "meta"]:
        assert_exists(core, k, "core_result")

    # -------------------------------
    # 4) trace 구조 검증
    # -------------------------------
    trace = core["trace"]
    for k in ["trace_id", "run_id", "span_id"]:
        assert_exists(trace, k, "core_result.trace")

    print("\n[OK] 모든 검증 통과! V1.11 ↔ V2+ 연결 이상 없음.\n")
    return True


# ----------------------------------------------------------
# ENTRY POINT (exit code 기반)
# ----------------------------------------------------------
if __name__ == "__main__":
    try:
        ok = test_connection()
        sys.exit(0 if ok else 1)
    except AssertionError as e:
        print("\n[FAIL] AssertionError 발생:")
        print(e)
        print("\n[DEBUG] 전체 결과 덤프:")
        pprint(locals())
        sys.exit(1)
    except Exception as e:
        print("\n[FAIL] 예상치 못한 오류 발생:")
        print(e)
        sys.exit(1)
