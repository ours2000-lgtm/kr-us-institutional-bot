from __future__ import annotations

import pytest

from src.integration_core.policy_registry import (
    get_policy_set,
    list_policy_sets,
)
from src.integration_core.policy_composition import PolicySpec


# ---------------------------------------------------------
# Registry existence contracts
# ---------------------------------------------------------

def test_default_always_exists():
    assert "default" in list_policy_sets()


def test_list_policy_sets_is_sorted():
    keys = list_policy_sets()
    assert keys == sorted(keys)


def test_get_unknown_policy_set_raises():
    with pytest.raises(KeyError):
        get_policy_set("unknown-key")


# ---------------------------------------------------------
# PolicySet structural contracts
# ---------------------------------------------------------

def test_default_policy_set_not_empty():
    ps = get_policy_set("default")
    assert ps.policies, "default policy set must not be empty"


def test_policy_specs_are_deterministic_order():
    ps = get_policy_set("default")
    specs = ps.policies

    assert all(isinstance(s, PolicySpec) for s in specs)

    sorted_specs = sorted(
        specs,
        key=lambda s: (not s.enabled, s.priority, s.ref, s.version),
    )
    assert specs == sorted_specs