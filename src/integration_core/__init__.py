from __future__ import annotations

from integration_core.consistency import (
    ConsistencyResult,
    enforce,
    # v0.2 functional checks
    check_dag,
    check_edge_metadata,
    check_no_duplicates,
    check_reachability,
    check_required_edges,
)

from integration_core.ids import (
    TraceabilityId,
    TraceabilityIdError,
    allowed_prefixes,
    generate_id,
    parse_id,
    validate_id,
)

__all__ = [
    # ids
    "TraceabilityId",
    "TraceabilityIdError",
    "allowed_prefixes",
    "generate_id",
    "parse_id",
    "validate_id",
    # consistency
    "ConsistencyResult",
    "enforce",
    "check_required_edges",
    "check_no_duplicates",
    "check_reachability",
    "check_dag",
    "check_edge_metadata",
]