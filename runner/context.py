# runner/context.py
# ------------------------------------------------------------
# Runner-only execution context for observability (v1.2+)
# ------------------------------------------------------------

class PipelineRunContext:
    """
    Runner-scoped execution context.

    - Holds observability metadata only (e.g. trace_id)
    - MUST NOT be passed into v1.1 decision pipelines
    - MUST NOT influence decision logic or results
    - Introduced in v1.2 (observability-only)
    """

    def __init__(self, trace_id: str):
        self.trace_id = trace_id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(trace_id={self.trace_id!r})"


__all__ = ["PipelineRunContext"]
