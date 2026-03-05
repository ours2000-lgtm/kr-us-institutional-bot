from __future__ import annotations

from typing import FrozenSet

# ------------------------------
# Runtime schema SSOT
# ------------------------------
SCHEMA_RUNTIME_EVENT_V0_5 = "runtime_log_event_v0.5"

# Backward-compat alias (tests/legacy import)
SCHEMA_RUNTIME_EVENT = SCHEMA_RUNTIME_EVENT_V0_5

# ------------------------------
# Incident keys SSOT (v0.3)
# ------------------------------
INCIDENT_RUNTIME_SCHEMA_VIOLATION = "INCIDENT_RUNTIME_SCHEMA_VIOLATION"
INCIDENT_GOV_HEALTH_RED = "INCIDENT_GOV_HEALTH_RED"
INCIDENT_GOV_HEALTH_AMBER = "INCIDENT_GOV_HEALTH_AMBER"
INCIDENT_GATE_BLOCK = "INCIDENT_GATE_BLOCK"
INCIDENT_RUNTIME_ERROR = "INCIDENT_RUNTIME_ERROR"

# Reserved (v0.4+)
INCIDENT_CRYPTO_GATE_BLOCK = "INCIDENT_CRYPTO_GATE_BLOCK"

ALLOWED_INCIDENT_KEYS_V0_3: FrozenSet[str] = frozenset(
    {
        INCIDENT_RUNTIME_SCHEMA_VIOLATION,
        INCIDENT_GOV_HEALTH_RED,
        INCIDENT_GOV_HEALTH_AMBER,
        INCIDENT_GATE_BLOCK,
        INCIDENT_RUNTIME_ERROR,
    }
)