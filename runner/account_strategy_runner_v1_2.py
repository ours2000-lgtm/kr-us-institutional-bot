from typing import Optional

from runner.context import PipelineRunContext
from runner.trace import generate_trace_id


def run_account_strategy_pipeline_v1_2(
    *args,
    trace_id: Optional[str] = None,
    **kwargs,
):
    """
    v1.2 runner entrypoint.

    - Generates trace_id if absent
    - Creates runner-scoped PipelineRunContext
    - Context is NOT propagated yet (observability preparation step)
    - Delegates execution to v1.1 pipeline unchanged

    NOTE:
    - ctx usage begins in a later v1.2 commit (observability attach)
    """

    trace_id = trace_id or generate_trace_id()
    ctx = PipelineRunContext(trace_id)

    # NOTE: import is intentionally delayed to avoid early import side effects
    from risk_engine.v1_1.account_strategy_runner import (
        run_account_strategy_pipeline_v1_1,
    )

    try:
        return run_account_strategy_pipeline_v1_1(*args, **kwargs)
    except Exception:
        # TODO: attach trace_id / ctx to error logging in v1.3+
        raise
