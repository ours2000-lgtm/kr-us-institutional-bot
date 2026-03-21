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