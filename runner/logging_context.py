# runner/logging_context.py
# ------------------------------------------------------------
# Commit N: Attach runner-scoped trace_id to logger context
#
# - Side-effect free (observability only)
# - Attach occurs once at v1.2 runner entrypoint
# - Lower layers use logger.info(...) without passing trace_id
# - Decision pipelines (v1.1) remain unaffected
# ------------------------------------------------------------

import logging
from contextvars import ContextVar


# Runner-scoped trace context
# NOTE:
# - trace_id is optional
# - Logs emitted without an attached trace will have trace_id = None
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)


class TraceIdFilter(logging.Filter):
    """
    Injects trace_id into log records.

    Characteristics:
    - Side-effect free: does not affect control flow or log level
    - Observability only: enriches logs, never behavior
    - Safe when trace_id is absent (None)
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # trace_id is optional; logs without a bound trace will have None.
        record.trace_id = trace_id_var.get(None)
        return True


def attach_trace_filter(logger: logging.Logger) -> None:
    """
    Attach TraceIdFilter to the given logger.

    Contract:
    - Must be called once at v1.2 runner entrypoint
    - Must NOT be attached in lower layers (v1.1 and below)
    - Intended for top-level application logger, not per-module loggers

    This function is idempotent to prevent duplicate filter attachment.
    """
    if not any(isinstance(f, TraceIdFilter) for f in logger.filters):
        logger.addFilter(TraceIdFilter())
