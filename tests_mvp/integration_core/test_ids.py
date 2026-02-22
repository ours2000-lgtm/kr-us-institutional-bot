from __future__ import annotations

import re

import pytest
from hypothesis import given, strategies as st

from integration_core.ids import TraceabilityIdError, allowed_prefixes, generate_id, parse_id, validate_id

UUIDV4_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def test_generate_id_format():
    tid = generate_id("PLAN")
    assert tid.value.startswith("PLAN-")
    assert UUIDV4_RE.search(tid.value.split("-", 1)[1]) is not None


def test_parse_id_roundtrip():
    tid = generate_id("VAL")
    parsed = parse_id(tid.value)
    assert parsed.prefix == "VAL"
    assert parsed.uuid == tid.uuid


def test_validate_id_prefix_filter():
    tid = generate_id("ROLLOUT")
    assert validate_id(tid.value, prefixes=["ROLLOUT"]) is True
    assert validate_id(tid.value, prefixes=["PLAN"]) is False


def test_parse_rejects_bad_prefix():
    with pytest.raises(TraceabilityIdError):
        parse_id("BADPREFIX-00000000-0000-4000-8000-000000000000")


@given(
    prefix=st.sampled_from(list(allowed_prefixes())),
)
def test_validate_generated_ids_are_valid(prefix: str):
    # hypothesis: generated ids must always validate
    tid = generate_id(prefix)  # type: ignore[arg-type]
    assert validate_id(tid.value) is True