import uuid
import pytest

from integration_core.ids import parse_id, validate_id, TraceabilityIdError


def test_lowercase_prefix_rejected():
    u = uuid.uuid4()
    with pytest.raises(TraceabilityIdError):
        parse_id(f"plan-{u}")


def test_invalid_uuid_rejected():
    with pytest.raises(TraceabilityIdError):
        parse_id("PLAN-1234")


def test_uuid_v1_rejected():
    u = uuid.uuid1()
    with pytest.raises(TraceabilityIdError):
        parse_id(f"PLAN-{u}")


def test_uuid_v5_rejected():
    u = uuid.uuid5(uuid.NAMESPACE_DNS, "example.com")
    with pytest.raises(TraceabilityIdError):
        parse_id(f"PLAN-{u}")


def test_validate_returns_false_on_invalid():
    assert validate_id("PLAN-1234") is False