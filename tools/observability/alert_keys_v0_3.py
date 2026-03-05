from __future__ import annotations

from typing import FrozenSet

# ------------------------------------
# Alert keys SSOT (v0.3)
# ------------------------------------
# "alert_key" is a stable routing identifier used by:
# - alert rules
# - alertmanager routes
# - runbook selection
#
# IMPORTANT:
# - alert_key must be stable (SSOT)
# - incident_key -> alert_key mapping must be 1:1 deterministic

ALERT_RUNTIME_SCHEMA_VIOLATION = "ALERT_RUNTIME_SCHEMA_VIOLATION"
ALERT_GOV_HEALTH_RED = "ALERT_GOV_HEALTH_RED"
ALERT_GOV_HEALTH_AMBER = "ALERT_GOV_HEALTH_AMBER"
ALERT_GATE_BLOCK = "ALERT_GATE_BLOCK"
ALERT_RUNTIME_ERROR = "ALERT_RUNTIME_ERROR"

# SSOT: allowed alert keys for v0.3 (excluding None)
ALLOWED_ALERT_KEYS_V0_3: FrozenSet[str] = frozenset(
    {
        ALERT_RUNTIME_SCHEMA_VIOLATION,
        ALERT_GOV_HEALTH_RED,
        ALERT_GOV_HEALTH_AMBER,
        ALERT_GATE_BLOCK,
        ALERT_RUNTIME_ERROR,
    }
)