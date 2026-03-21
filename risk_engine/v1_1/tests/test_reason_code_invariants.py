import pytest
from typing import Dict, Tuple, List, Set

from decision.state import DecisionState
from decision.reason_category import ReasonCategory
from decision.reason_category_validator import (
    validate_terminal_reason_category,
    InvalidReasonCategoryError,
)
from decision.reason_code import ReasonCode, REASON_CODE_MAP

# ------------------------------------------------------------
# Constitution version anchor
# ------------------------------------------------------------
CONSTITUTION_VERSION = "v1.2"

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _fmt_codes(codes: Set[ReasonCode]) -> list[str]:
    """Human-friendly enum formatting for pytest output."""
    return sorted(f"{c.name} ({c.value})" for c in codes)


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------
class TestReasonCodeInvariants:
    """
    Constitutional invariants for (terminal_state, reason_category, reason_code).

    These tests are the constitutional guardrail.
    If any of these fail, the Constitution is violated.
    """

    # --------------------------------------------------------
    # 1) Validator sanity (terminal_state x reason_category)
    # --------------------------------------------------------
    @pytest.mark.parametrize(
        "terminal,category",
        [
            (DecisionState.EXECUTED, ReasonCategory.BUSINESS),
            (DecisionState.REJECTED, ReasonCategory.VALIDATION),
            (DecisionState.REJECTED, ReasonCategory.RISK),
            (DecisionState.REJECTED, ReasonCategory.POLICY),
            (DecisionState.FAILED, ReasonCategory.SYSTEM),
            (DecisionState.FAILED, ReasonCategory.INFRA),
            (DecisionState.FAILED, ReasonCategory.DEPENDENCY),
            (DecisionState.FAILED, ReasonCategory.DATA),
            (DecisionState.FAILED, ReasonCategory.UNKNOWN),
        ],
    )
    def test_valid_terminal_category_passes(
        self,
        terminal: DecisionState,
        category: ReasonCategory,
    ) -> None:
        validate_terminal_reason_category(terminal, category)

    @pytest.mark.parametrize(
        "terminal,category",
        [
            (DecisionState.EXECUTED, ReasonCategory.RISK),
            (DecisionState.EXECUTED, ReasonCategory.INFRA),
            (DecisionState.FAILED, ReasonCategory.POLICY),
            (DecisionState.REJECTED, ReasonCategory.INFRA),
        ],
    )
    def test_invalid_terminal_category_is_rejected(
        self,
        terminal: DecisionState,
        category: ReasonCategory,
    ) -> None:
        with pytest.raises(InvalidReasonCategoryError):
            validate_terminal_reason_category(terminal, category)

    # --------------------------------------------------------
    # 2) Enum ↔ Constitution exact match
    # --------------------------------------------------------
    def test_enum_matches_constitution_exactly(self) -> None:
        enum_codes: Set[ReasonCode] = set(ReasonCode)
        constitution_codes: Set[ReasonCode] = set(REASON_CODE_MAP.keys())

        extra = enum_codes - constitution_codes
        missing = constitution_codes - enum_codes

        assert not extra and not missing, (
            f"[Constitution {CONSTITUTION_VERSION}] Enum mismatch detected. "
            f"extra={_fmt_codes(extra)}, missing={_fmt_codes(missing)}"
        )

    # --------------------------------------------------------
    # 3) REASON_CODE_MAP covers all enum values
    # --------------------------------------------------------
    def test_reason_code_map_covers_all_enum_values(self) -> None:
        enum_codes = set(ReasonCode)
        map_codes = set(REASON_CODE_MAP.keys())

        missing = enum_codes - map_codes
        extra = map_codes - enum_codes

        assert not missing and not extra, (
            f"[Constitution {CONSTITUTION_VERSION}] "
            f"REASON_CODE_MAP coverage mismatch. "
            f"missing={_fmt_codes(missing)}, extra={_fmt_codes(extra)}"
        )

    # --------------------------------------------------------
    # 4) Reverse coverage: every (terminal_state, category)
    #     must have at least one concrete reason_code
    # --------------------------------------------------------
    def test_reason_code_map_reverse_coverage(self) -> None:
        reverse_index: Dict[
            Tuple[DecisionState, ReasonCategory],
            List[ReasonCode]
        ] = {}

        for code, meta in REASON_CODE_MAP.items():
            key = (meta.terminal_state, meta.category)
            reverse_index.setdefault(key, []).append(code)

        missing_pairs = [
            pair for pair, codes in reverse_index.items() if not codes
        ]

        assert not missing_pairs, (
            f"[Constitution {CONSTITUTION_VERSION}] "
            f"Missing reason_code coverage for pairs: {missing_pairs}"
        )

    # --------------------------------------------------------
    # 5) Edge absorbers are last-resort only
    # --------------------------------------------------------
    def test_edge_absorbers_are_last_resort(self) -> None:
        reverse_index: Dict[
            Tuple[DecisionState, ReasonCategory],
            List[ReasonCode]
        ] = {}

        for code, meta in REASON_CODE_MAP.items():
            key = (meta.terminal_state, meta.category)
            reverse_index.setdefault(key, []).append(code)

        for pair, codes in reverse_index.items():
            edge_codes = [
                c for c in codes if REASON_CODE_MAP[c].edge_case
            ]
            non_edge_codes = [
                c for c in codes if not REASON_CODE_MAP[c].edge_case
            ]

            # Rule 1: At most one absorber per (terminal, category)
            assert len(edge_codes) <= 1, (
                f"[Constitution {CONSTITUTION_VERSION}] "
                f"Multiple edge absorbers found for {pair}: "
                f"{_fmt_codes(set(edge_codes))}"
            )

            # Rule 2: Absorber cannot be the only code
            if edge_codes:
                assert non_edge_codes, (
                    f"[Constitution {CONSTITUTION_VERSION}] "
                    f"Edge absorber without canonical code for {pair}: "
                    f"{_fmt_codes(set(edge_codes))}"
                )

    # --------------------------------------------------------
    # 6) Meta field validity
    # --------------------------------------------------------
    def test_reason_code_meta_fields_are_valid(self) -> None:
        for code, meta in REASON_CODE_MAP.items():
            assert isinstance(meta.terminal_state, DecisionState), (
                f"[Constitution {CONSTITUTION_VERSION}] "
                f"{code.name}: invalid terminal_state {meta.terminal_state}"
            )
            assert isinstance(meta.category, ReasonCategory), (
                f"[Constitution {CONSTITUTION_VERSION}] "
                f"{code.name}: invalid category {meta.category}"
            )
            assert isinstance(meta.edge_case, bool), (
                f"[Constitution {CONSTITUTION_VERSION}] "
                f"{code.name}: edge_case must be bool"
            )
