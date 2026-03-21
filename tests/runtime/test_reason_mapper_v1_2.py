from __future__ import annotations

from runtime.decision.reason_code import ReasonCode
from runtime.decision.reason_mapper_v1_2 import map_reason_to_code


def test_map_reason_to_code_known_reason():
    assert map_reason_to_code("account_healthy") == ReasonCode.EXECUTED_OK


def test_map_reason_to_code_unknown_reason_known_fallback():
    assert map_reason_to_code("nonexistent_reason_xyz") == ReasonCode.FAILED_UNKNOWN
