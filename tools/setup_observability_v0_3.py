from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

files = {
"docs/observability/INCIDENT_TO_ALERT_MAPPING_v0.3.md": """
# INCIDENT_TO_ALERT_MAPPING_v0.3

status: SSOT
version: v0.3
owner: observability

Runtime Event → IncidentClassifier → Alert → Runbook mapping
""",

"docs/runbooks/RUNTIME_SCHEMA_VIOLATION.md": """
# Runtime Schema Violation

Severity: P2

Description
Runtime log event schema mismatch detected.

Immediate Action
1. Inspect runtime logs
2. verify schema_version
3. restart runtime emitter if necessary
""",

"docs/runbooks/GATE_BLOCK.md": """
# Governance Gate Block

Severity: P1

Description
Execution blocked by governance gate.
""",

"docs/runbooks/GOV_HEALTH_RED.md": """
# Governance Health RED

Severity: P1

Description
Governance health critical state detected.
""",

"docs/runbooks/GOV_HEALTH_AMBER.md": """
# Governance Health AMBER

Severity: P2

Description
Governance health degraded state detected.
""",

"docs/runbooks/RUNTIME_ERROR.md": """
# Runtime Error

Severity: P2

Description
Unexpected runtime exception occurred.
""",

"tests/test_observability_ssot_v0_3.py": """
from pathlib import Path

def test_runbooks_exist():
    root = Path(__file__).resolve().parents[1]

    runbooks = [
        "docs/runbooks/RUNTIME_SCHEMA_VIOLATION.md",
        "docs/runbooks/GATE_BLOCK.md",
        "docs/runbooks/GOV_HEALTH_RED.md",
        "docs/runbooks/GOV_HEALTH_AMBER.md",
        "docs/runbooks/RUNTIME_ERROR.md",
    ]

    for rb in runbooks:
        assert (root / rb).exists()
"""
}

for path, content in files.items():
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.strip(), encoding="utf-8")

print("Observability v0.3 files created.")