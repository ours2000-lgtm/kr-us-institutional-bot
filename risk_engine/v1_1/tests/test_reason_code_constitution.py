import pytest

from decision.state import DecisionState
from decision.reason_category import ReasonCategory
from decision.reason_code import ReasonCode, REASON_CODE_MAP

# -------------------------------------------------------------------
# Constitution metadata
# -------------------------------------------------------------------

CONSTITUTION_VERSION = "v1.2"

# Canonical reason codes defined by the Constitution show exactly.
# (Source of truth: DECISION_REASON_CODE_TAXONOMY.md v1.2)
CONSTITUTION_REASON_CODES = {
    "EXECUTED.OK",
    "REJECTED.VALIDATION_FAILED",
    "REJECTED.RISK_LIMIT",
    "REJECTED.POLICY_RULE",
    "REJECTED.POLICY_GENERIC",
    "FAILED.SYSTEM_ERROR",
    "FAILED.INFRA_UNAVAILABLE",
    "FAILED.DEPENDENCY_TIMEOUT",
    "FAILED.DATA_INTEGRITY",
    "FAILED.UNKNOWN",
}

# Backlog (non-binding) codes — MUST NOT appear in enums
BACKLOG_REASON_CODES = {
    "EXECUTED.PARTIAL",
    "EXECUTED.ASYNC_CONFIRMED",
    "REJECTED.AUTHORIZATION_FAILED",
    "REJECTED.DATA_CONFLICT",
    "FAILED.CONFIGURATION_ERROR",
    "FAILED.SECURITY_EXCEPTION",
}


# -------------------------------------------------------------------
# 1️⃣ Enum ↔ Constitution exact match
# -------------------------------------------------------------------

def test_enum_matches_constitution_exactly() -> None:
    """
    Enum reason codes MUST match the Constitution exactly.

    - No missing codes
    - No extra codes
    """
    enum_codes = {c.value for c in ReasonCode}

    extra = enum_codes - CONSTITUTION_REASON_CODES
    missing = CONSTITUTION_REASON_CODES - enum_codes

    assert not extra and not missing, (
        f"[Constitution {CONSTITUTION_VERSION}] Enum mismatch detected. "
        f"extra={sorted(extra)}, missing={sorted(missing)}"
    )


# -------------------------------------------------------------------
# 2️⃣ Backlog boundary enforcement
# -------------------------------------------------------------------

def test_enum_does_not_include_backlog_codes() -> None:
    """
    Backlog reason codes MUST NOT appear in enums.
    """
    enum_codes = {c.value for c in ReasonCode}
    leaked = enum_codes & BACKLOG_REASON_CODES

    assert not leaked, (
        f"[Constitution {CONSTITUTION_VERSION}] "
        f"Backlog reason codes MUST NOT appear in enum: {sorted(leaked)}"
    )


# -------------------------------------------------------------------
# 3️⃣ REASON_CODE_MAP ↔ enum coverage
# -------------------------------------------------------------------

def test_reason_code_map_covers_all_enum_values() -> None:
    """
    REASON_CODE_MAP MUST cover all enum values exactly.
    """
    enum_codes = set(ReasonCode)
    map_codes = set(REASON_CODE_MAP.keys())

    extra = map_codes - enum_codes
    missing = enum_codes - map_codes

    assert not extra and not missing, (
        f"[Constitution {CONSTITUTION_VERSION}] "
        f"REASON_CODE_MAP coverage mismatch. "
        f"extra={sorted(c.name for c in extra)}, "
        f"missing={sorted(c.name for c in missing)}"
    )


# -------------------------------------------------------------------
# 4️⃣ Reverse coverage: terminal_state × category completeness
# -------------------------------------------------------------------

def test_reason_code_map_reverse_coverage() -> None:
    """
    Every canonical (terminal_state, reason_category) pair
    MUST have at least one concrete reason_code.
    """
    # Canonical pairs derived from the Constitution set
    canonical_pairs = {
        (meta.terminal_state, meta.category)
        for code, meta in REASON_CODE_MAP.items()
        if code.value in CONSTITUTION_REASON_CODES
    }

    reverse_index = {}
    for code, meta in REASON_CODE_MAP.items():
        pair = (meta.terminal_state, meta.category)
        reverse_index.setdefault(pair, []).append(code)

    missing_pairs = [
        pair for pair in canonical_pairs
        if not reverse_index.get(pair)
    ]

    assert not missing_pairs, (
        f"[Constitution {CONSTITUTION_VERSION}] "
        f"Missing reason_code coverage for pairs: {missing_pairs}"
    )

    # Guard against unexpected taxonomy expansion
    extra_pairs = set(reverse_index.keys()) - canonical_pairs
    assert not extra_pairs, (
        f"[Constitution {CONSTITUTION_VERSION}] "
        f"Unexpected (terminal_state, category) pairs present: {extra_pairs}"
    )


# -------------------------------------------------------------------
# 5️⃣ Edge absorbers must be last resort
# -------------------------------------------------------------------

def test_edge_absorbers_are_last_resort() -> None:
    """
    Edge absorber codes:
    - MUST NOT be the only code in a (terminal_state, category) bucket
    - MUST NOT appear more than once per bucket
    """
    reverse_index = {}
    for code, meta in REASON_CODE_MAP.items():
        pair = (meta.terminal_state, meta.category)
        reverse_index.setdefault(pair, []).append(code)

    for pair, codes in reverse_index.items():
        edge_codes = [
            c for c in codes if REASON_CODE_MAP[c].edge_case
        ]
        normal_codes = [
            c for c in codes if not REASON_CODE_MAP[c].edge_case
        ]

        if edge_codes:
            assert normal_codes, (
                f"[Constitution {CONSTITUTION_VERSION}] "
                f"Edge absorber without canonical code for pair {pair}: "
                f"{[c.name for c in edge_codes]}"
            )

            assert len(edge_codes) == 1, (
                f"[Constitution {CONSTITUTION_VERSION}] "
                f"Multiple edge absorbers for pair {pair}: "
                f"{[c.name for c in edge_codes]}"
            )
