# 경로: E:\AI_TRADING\KR_US_INSTITUTIONAL_BOT\v2\utils\validator.py

from __future__ import annotations

from typing import Any, Dict

from core.types_v2 import FactorEngineInput, FactorSnapshot, PolicyContext


def validate_factor_input(data: FactorEngineInput) -> None:
    """
    FactorEngineInput에 대한 최소 유효성 검사.
    """
    if not data.get("symbol"):
        raise ValueError("FactorEngineInput.symbol is required.")
    if not data.get("timestamp"):
        raise ValueError("FactorEngineInput.timestamp is required.")


def validate_factor_snapshot(snapshot: FactorSnapshot) -> None:
    """
    FactorSnapshot에 대한 sanity check (필요시 확장).
    """
    # TODO: rolling_volatility, rolling_liquidity 값 범위 검사 등
    _ = snapshot  # placeholder


def validate_policy_context(policy: PolicyContext) -> None:
    """
    PolicyContext 최소 유효성 검사.
    """
    if "regime" not in policy:
        raise ValueError("PolicyContext.regime is required.")
    thresholds = policy.get("thresholds")
    if not thresholds:
        raise ValueError("PolicyContext.thresholds is required.")
    if not (0.0 <= thresholds["low"] < thresholds["medium"] <= 1.0):
        raise ValueError(f"Invalid thresholds: {thresholds}")


def validate_v2_result_meta(meta: Dict[str, Any]) -> None:
    """
    V2RiskResult.meta에 대한 공통 검증.
    연결 테스트 및 CI에서 활용.
    """
    for key in ["v2_engine_version", "v2_schema_version", "environment", "trace_id", "run_id"]:
        value = meta.get(key)
        if value in (None, ""):
            raise ValueError(f"meta['{key}'] is missing or empty.")
