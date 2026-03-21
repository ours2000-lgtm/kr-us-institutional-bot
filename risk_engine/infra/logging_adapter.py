# risk_engine/infra/logging_adapter.py

import logging
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)


def log_info(msg: str, *, ctx: Optional[Any] = None, **kwargs: Any) -> None:
    """
    Common logging adapter.

    v1.2 observability:
    - trace_id is read-only metadata attached to logs
    - MUST NOT be used for branching, retries, or business decisions
    - v1.1 behavior and contracts remain unchanged
    """

    # Normalize extra dict from kwargs
    extra: Dict[str, Any] = dict(kwargs.pop("extra", {}) or {})

    # Silent extension: attach trace_id only if present
    trace_id = getattr(ctx, "trace_id", None) if ctx is not None else None
    if trace_id is not None:
        extra["trace_id"] = str(trace_id)

    # Core logging call (unchanged)
    logger.info(msg, extra=extra, **kwargs)
