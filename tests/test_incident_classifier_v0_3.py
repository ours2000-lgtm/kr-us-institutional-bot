import random
from datetime import datetime, timezone

from tools.observability.incident_classifier_v0_3 import (
    classify_runtime_event,
    ALLOWED_INCIDENT_KEYS_V0_3,
    SCHEMA_RUNTIME_EVENT,
)

def test_classifier_returns_only_allowed_domain_or_none():
    samples = [
        # schema mismatch
        {"schema_version": "other", "event_type": "RUNTIME_HEALTH", "level": "INFO"},
        # gate block
        {"schema_version": SCHEMA_RUNTIME_EVENT, "event_type": "GATE_DECISION", "level": "INFO", "decision": "BLOCK"},
        # gate grade fail
        {"schema_version": SCHEMA_RUNTIME_EVENT, "event_type": "GATE_DECISION", "level": "INFO", "grade": "FAIL"},
        # gov health
        {"schema_version": SCHEMA_RUNTIME_EVENT, "event_type": "GOV_HEALTH", "level": "INFO", "grade": "WARN"},
        {"schema_version": SCHEMA_RUNTIME_EVENT, "event_type": "GOV_HEALTH", "level": "INFO", "grade": "FAIL"},
        # runtime error
        {"schema_version": SCHEMA_RUNTIME_EVENT, "event_type": "RUNTIME_ORDER_FAIL", "level": "ERROR"},
        # normal -> None
        {"schema_version": SCHEMA_RUNTIME_EVENT, "event_type": "RUNTIME_HEALTH", "level": "INFO"},
    ]

    # light fuzz without hypothesis
    event_types = ["RUNTIME_X", "GOV_HEALTH", "GATE_DECISION", "EVIDENCE_CHAIN", "UNKNOWN"]
    levels = ["DEBUG", "INFO", "ERROR", "WARN"]  # WARN은 upstream에서 INFO로 normalize 되지만 classifier는 그냥 처리
    decisions = [None, "ALLOW", "BLOCK", "PERMIT"]
    grades = [None, "PASS", "WARN", "FAIL", "OK"]

    for _ in range(200):
        samples.append(
            {
                "schema_version": random.choice([SCHEMA_RUNTIME_EVENT, "bad_schema"]),
                "event_type": random.choice(event_types),
                "level": random.choice(levels),
                "decision": random.choice(decisions),
                "grade": random.choice(grades),
                "ts_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
        )

    for e in samples:
        out = classify_runtime_event(e)
        assert (out is None) or (out in ALLOWED_INCIDENT_KEYS_V0_3)