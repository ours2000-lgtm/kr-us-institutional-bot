# E:\KR_US_INSTITUTIONAL_BOT\tests\test_governance_validator.py
import json
from pathlib import Path

import pytest

from tools.governance_validator import validate_bundle


FIXTURE_DIR = Path("tests/fixtures/traces")


def _decision_token(result) -> str:
    """result.decision may be Enum or str."""
    d = getattr(result, "decision", None)
    if hasattr(d, "value"):
        return str(d.value)
    return str(d)


def _fail_closed_bool(result):
    """result.fail_closed may be bool or Enum-like."""
    fc = getattr(result, "fail_closed", None)
    if hasattr(fc, "value"):
        try:
            return bool(fc.value)
        except Exception:
            pass
    return fc


@pytest.mark.parametrize(
    "fixture_path",
    sorted(FIXTURE_DIR.glob("*.json")),
)
def test_validator_with_trace_fixtures(fixture_path: Path):
    bundle = json.loads(fixture_path.read_text(encoding="utf-8"))
    result = validate_bundle(bundle)

    assert result is not None
    assert hasattr(result, "decision")
    assert hasattr(result, "fail_closed")

    name = fixture_path.name.lower()
    decision = _decision_token(result)
    fail_closed = _fail_closed_bool(result)

    # ------------------------------------------------------------
    # CONST-001: ONLY ONE canonical golden fixture is ALLOW
    # ------------------------------------------------------------
    if name == "trace_ok_v1_signed.json":
        assert decision == "ALLOW"
        assert fail_closed is False
        return

    # ------------------------------------------------------------
    # Everything else must be FAIL_CLOSED (safe default)
    # ------------------------------------------------------------
    assert fail_closed is True
