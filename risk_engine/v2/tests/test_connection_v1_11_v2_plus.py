# test_connection_v1_11_v2_plus.py
from __future__ import annotations
from typing import Dict, Any
import uuid
from datetime import datetime

# --- 올바른 import 구조 (절대 수정 금지) ---
from core.engine_base import RiskEngineCore
from core.types_v2 import CoreRiskResult, FactorEngineInput
from orchestrator.orchestrator_v2_plus import RiskOrchestratorV2Plus
from utils.validator import validate_v2_result_meta


# -----------------------------------------------------
# V1.11 Dummy Core (테스트용 최소 구현)
# -----------------------------------------------------
class DummyCoreV1_11(RiskEngineCore):
    """
    V1.11 RiskEngine 흉내용.
    """

    def run(
        self,
        input_snapshot: Dict[str, Any],
    ) -> CoreRiskResult:

        trace_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())

        return {
            "schema_version": "1.11",
            "core_engine_version": "v1.11-mock",
            "environment": "test",
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": trace_id,
            "run_id": run_id,
            "acc_id": "ACC_TEST",
            "session_id": "SESSION_TEST",
            "strategy_id": "STRAT_TEST",
            "raw_snapshot": input_snapshot,
            "risk_score": 0.42,
        }


# -----------------------------------------------------
# 연결 테스트
# -----------------------------------------------------
def test_connection() -> bool:
    print("\n[ Running V1.11 → V2+ Connection Test ]")

    core = DummyCoreV1_11()
    orchestrator = RiskOrchestratorV2Plus(core_engine=core, env="test")

    dummy_input: FactorEngineInput = {
        "price": 100,
        "volume": 200,
        "timestamp": datetime.utcnow().isoformat(),
    }

    v2_output = orchestrator.run(dummy_input)

    # ---------- 필수 키 검증 ----------
    required_keys = ["schema_version", "v2_engine_version", "environment",
                     "timestamp", "core_result", "meta"]
    for k in required_keys:
        if k not in v2_output:
            raise AssertionError(f"[FAIL] Missing top-level field: {k}")

    # ---------- meta 검증 ----------
    meta = v2_output["meta"]
    for k in ["trace_id", "run_id", "environment", "core_schema_version"]:
        if meta.get(k) in (None, ""):
            raise AssertionError(f"[FAIL] meta['{k}'] is missing or empty.")

    # ---------- 메타 스키마 검증 ----------
    validate_v2_result_meta(meta)

    print("[PASS] V1.11 → V2+ 연결 테스트 성공")
    return True


if __name__ == "__main__":
    test_connection()
