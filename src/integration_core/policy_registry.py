from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from src.integration_core.policy_composition import PolicySpec, RuleSet


# ============================================================
# PolicySet
# ============================================================


@dataclass(frozen=True)
class PolicySet:
    """
    Registry-level immutable policy set definition.

    - key: stable identifier ("default", "strict", ...)
    - ruleset: RuleSet(strategy, params)
    - policies: full list of PolicySpec (enabled=True/False included)

    Notes:
    - Disabled specs remain in this list.
    - Composition layer decides enabled/disabled and records meta.
    """

    key: str
    ruleset: RuleSet
    policies: List[PolicySpec]


# ============================================================
# Internal Registry (SSOT)
# ============================================================


# --- DEFAULT POLICY SET ------------------------------------------------------

_DEFAULT_RULESET = RuleSet(
    name="default",
    version="v0.5",
    strategy="fail_closed",
)

_DEFAULT_POLICIES: List[PolicySpec] = [
    PolicySpec(
        ref="AnyFailBlockPolicy",
        version="v0.4",
        enabled=True,
        priority=100,
    )
]

# --- STRICT EXAMPLE (optional future extension) ------------------------------

_STRICT_RULESET = RuleSet(
    name="strict",
    version="v0.5",
    strategy="quorum",
    k=1,  # k=1 => fail-closed equivalent
)

_STRICT_POLICIES: List[PolicySpec] = [
    PolicySpec(
        ref="AnyFailBlockPolicy",
        version="v0.4",
        enabled=True,
        priority=100,
    )
]

# --- QUORUM-2 POLICY SET ------------------------------------------------------

_QUORUM2_RULESET = RuleSet(
    name="quorum-2",
    version="v0.5",
    strategy="quorum",
    k=2,
)

_QUORUM2_POLICIES: List[PolicySpec] = [
    PolicySpec(
        ref="AnyFailBlockPolicy",
        version="v0.4",
        enabled=True,
        priority=100,
    ),
    PolicySpec(
        ref="SoftWarnPolicy",
        version="v0.5",
        enabled=True,
        priority=50,
    ),
]

# Registry is initialized once at import time (thread-safe by design)
_REGISTRY: Dict[str, PolicySet] = {
    "default": PolicySet(
        key="default",
        ruleset=_DEFAULT_RULESET,
        policies=_DEFAULT_POLICIES,
    ),
    "strict": PolicySet(
        key="strict",
        ruleset=_STRICT_RULESET,
        policies=_STRICT_POLICIES,
    ),
    "quorum-2": PolicySet(
        key="quorum-2",
        ruleset=_QUORUM2_RULESET,
        policies=_QUORUM2_POLICIES,
    ),
}


# ============================================================
# Public API
# ============================================================


def get_policy_set(key: str) -> PolicySet:
    """
    Retrieve registered policy set.

    Raises:
        KeyError if key does not exist (fail-fast contract).
    """
    try:
        return _REGISTRY[key]
    except KeyError:
        raise KeyError(f"Unknown policy set key: {key}") from None


def list_policy_sets() -> List[str]:
    """
    Return sorted list of available policy set keys.

    Sorting is deterministic and part of contract.
    """
    return sorted(_REGISTRY.keys())


# ============================================================
# Invariants (documented contract)
# ============================================================

# MUST always contain default
assert "default" in _REGISTRY, "Registry invariant violated: 'default' missing"