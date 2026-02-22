"""
integration_core

SSOT primitives shared across domains:
- traceability IDs (PLAN/VAL/ROLLOUT)
- global lifecycle enum
- cross-domain consistency check interface
"""
from .ids import TraceabilityId, TraceabilityIdError, generate_id, parse_id, validate_id
from .lifecycle import LifecycleState
from .consistency import ConsistencyMode, ConsistencyResult, ConsistencyChecker

__all__ = [
    "TraceabilityId",
    "TraceabilityIdError",
    "generate_id",
    "parse_id",
    "validate_id",
    "LifecycleState",
    "ConsistencyMode",
    "ConsistencyResult",
    "ConsistencyChecker",
]