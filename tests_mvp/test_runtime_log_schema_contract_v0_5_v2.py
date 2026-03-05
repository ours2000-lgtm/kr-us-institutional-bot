# tests_mvp/test_runtime_log_schema_contract_v0_5_v2.py
from __future__ import annotations

from pathlib import Path
import json
import pytest

from tools.observability.schema_loader import load_runtime_schema_v0_5


def test_runtime_log_schema_v0_5_loadable_or_skip():
    """
    계약:
    - 스키마 파일이 존재하면 반드시 load 가능해야 한다.
    - 존재하지 않으면(로컬 환경 미구성) 이 테스트는 SKIP 한다.
    """
    # loader 내부가 FileNotFoundError를 던지므로, 먼저 경로 힌트를 직접 검사하기 어렵다.
    # 따라서 예외 기반으로 SKIP 처리.
    try:
        schema = load_runtime_schema_v0_5()
    except FileNotFoundError as e:
        pytest.skip(f"runtime schema missing (local env): {e}")

    assert isinstance(schema, dict)
    assert schema.get("type") in (None, "object")  # 느슨하게: 스키마가 dict임만 보장


def test_runtime_log_schema_v0_5_minimum_shape_or_skip():
    """
    최소 계약:
    - $schema / title / properties 중 하나 이상은 있어야 '스키마'로서 의미가 있다.
    """
    try:
        schema = load_runtime_schema_v0_5()
    except FileNotFoundError as e:
        pytest.skip(f"runtime schema missing (local env): {e}")

    assert isinstance(schema, dict)
    assert any(k in schema for k in ("$schema", "title", "properties"))