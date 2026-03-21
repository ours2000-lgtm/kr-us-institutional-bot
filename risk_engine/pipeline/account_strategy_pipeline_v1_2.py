import uuid
from typing import Optional

from risk_engine.pipeline.account_strategy_pipeline_v1_1 import (
    run_account_strategy_pipeline,
    PipelineValidationResultV1_1,
)

# ============================================================
# ACCOUNT + STRATEGY Pipeline — v1.2
# SILENT EXTENSION ENTRY POINT
#
# Purpose:
# - Introduce read-only, non-decisive observability metadata
# - Preserve v1.1 behavior, contracts, and tests unchanged
#
# This file MUST NOT:
# - Modify decision logic
# - Modify v1.1 result objects
# - Influence pipeline outcomes
# ============================================================


def generate_trace_id() -> str:
    """
    Generate a unique trace identifier for observability purposes.

    v1.2 rules:
    - Read-only metadata only
    - MUST NOT be used for decision branching
    - MUST NOT affect pipeline behavior
    """
    return uuid.uuid4().hex


def run_account_strategy_pipeline_v1_2(
    *,
    account_decision: dict,
    strategy_decision: dict,
    trace_id: Optional[str] = None,
) -> PipelineValidationResultV1_1:
    """
    v1.2 wrapper entry point for ACCOUNT + STRATEGY pipeline.

    Notes:
    - trace_id is generated or accepted here ONLY
    - trace_id is NOT passed into v1.1 decision logic
    - v1.1 execution remains a pure function

    Observability intent:
    - trace_id may be attached to logging / metrics / audit layers
    - decision outcome remains fully v1.1-defined
    """

    # --------------------------------------------------------
    # Observability metadata (read-only, non-decisive)
    # --------------------------------------------------------
    effective_trace_id = trace_id or generate_trace_id()

    # NOTE:
    # At this stage, effective_trace_id is intentionally unused.
    # It will be consumed by logging / metrics layers ONLY.
    # No propagation into decision logic is allowed.

    # --------------------------------------------------------
    # Delegate to v1.1 executable pipeline (UNCHANGED)
    # --------------------------------------------------------
    result = run_account_strategy_pipeline(
        account_decision=account_decision,
        strategy_decision=strategy_decision,
    )

    return result
