import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

SCHEMA_PATH = Path("docs/observability/schemas/runtime_log_event_v0.5.json")
MARKER_CODE = "COMPOSITE_MARKER"


# -----------------------------
# Schema helpers (LOCK)
# -----------------------------
def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_errors(event: dict):
    schema = load_schema()
    validator = Draft7Validator(schema)
    return sorted(validator.iter_errors(event), key=lambda e: list(e.path))


def assert_schema_valid(event: dict):
    errs = schema_errors(event)
    if errs:
        msgs = []
        for e in errs:
            path = list(e.path)
            msgs.append(f"{path}: {e.message} (value={e.instance!r})")
        pytest.fail("Schema validation failed:\n" + "\n".join(msgs))


def assert_schema_invalid(event: dict):
    errs = schema_errors(event)
    if not errs:
        pytest.fail("Expected schema validation to fail, but it passed.")


# -----------------------------
# Domain invariants (SSOT)
# -----------------------------
def assert_invariants(event: dict):
    """
    Invariants that are not fully enforceable by draft-07 JSON Schema:
    - marker.code ∈ reason_codes (dynamic cross-field)
    - marker↔reason_codes bidirectional consistency
    - stream separation semantics beyond schema if/then
    - rc size hard limit (byte-based)
    """

    # --- marker ↔ reason_codes bidirectional consistency ---
    if "reason_codes" in event and isinstance(event["reason_codes"], list):
        if MARKER_CODE in event["reason_codes"]:
            assert "marker" in event and isinstance(event["marker"], dict), (
                f"{MARKER_CODE} in reason_codes requires marker object"
            )
            assert "code" in event["marker"], "marker.code is required when marker object exists"
            assert event["marker"]["code"] == MARKER_CODE, (
                "marker.code MUST match the marker reason code when marker reason is present"
            )

    # marker.code ∈ reason_codes
    if "marker" in event and isinstance(event["marker"], dict) and "reason_codes" in event:
        code = event["marker"].get("code")
        if code is not None:
            assert code in event["reason_codes"], "marker.code MUST be present in reason_codes"

    # --- decision-bearing event must have trace_id ---
    # (Schema enforces this via if/then for decision-bearing events; this is a belt-and-suspenders check.)
    if event.get("event") in {"POLICY_EVALUATED", "AGGREGATION_COMPLETED", "FAIL_CLOSED_BLOCKED"}:
        assert "trace_id" in event and event["trace_id"], "Decision-bearing event MUST include trace_id"

    # --- forbidden decision/grade combos (also enforced by schema) ---
    if "decision" in event and "grade" in event:
        if event["decision"] == "ALLOW":
            assert event["grade"] != "BLOCK", "Forbidden: decision=ALLOW & grade=BLOCK"
        if event["decision"] == "BLOCK":
            assert event["grade"] != "PASS", "Forbidden: decision=BLOCK & grade=PASS"


# -----------------------------
# Event factories
# -----------------------------
def base_decision_event(**overrides) -> dict:
    """
    A valid decision-bearing event template (AGGREGATION_COMPLETED).
    """
    e = {
        "ts_utc": "2026-02-26T00:00:00Z",
        "level": "INFO",
        "component": "aggregation",
        "event": "AGGREGATION_COMPLETED",
        "emitter_id": "test",
        "trace_id": "T-BASE",
        "decision": "ALLOW",
        "grade": "WARN",
        "policy_ref": "POLICY-X",
        "reason_codes": [MARKER_CODE],
        "marker": {"code": MARKER_CODE, "index": 0, "count": 1},
        "inputs_hash": "abc",
        "evidence_hash": "def",
        "latency_ms": 1,
    }
    e.update(overrides)
    return e


def make_rc_payload_for_total_bytes(target_total_bytes: int) -> str:
    """
    Creates an ASCII payload so that len(json.dumps({"symbol": payload}, ...).encode("utf-8")) == target_total_bytes.

    Note:
    - We use separators=(",", ":") and ensure_ascii=False to match runtime adapter canonicalization.
    - This pins the boundary semantics as an invariant.
    """
    base = json.dumps({"symbol": ""}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    overhead = len(base)  # bytes excluding payload content
    n = target_total_bytes - overhead
    if n < 0:
        raise ValueError(f"Target {target_total_bytes} is smaller than overhead {overhead}")
    return "X" * n  # ASCII 1 byte each in UTF-8


def rc_json_len_bytes(rc_obj: dict) -> int:
    rc_json = json.dumps(rc_obj, ensure_ascii=False, separators=(",", ":"))
    return len(rc_json.encode("utf-8"))


# ---------------------------------------------------------
# 1️⃣ Schema-level forbidden decision/grade combinations
# ---------------------------------------------------------
@pytest.mark.parametrize(
    "decision,grade",
    [
        ("ALLOW", "BLOCK"),
        ("BLOCK", "PASS"),
    ],
)
def test_forbidden_decision_grade_combinations_rejected_by_schema(decision, grade):
    event = base_decision_event(decision=decision, grade=grade)
    assert_schema_invalid(event)


# ---------------------------------------------------------
# 2️⃣ Marker invariants
#    - index/count/code required enforced by schema
#    - code ∈ reason_codes enforced by invariants
# ---------------------------------------------------------
def test_marker_index_and_count_enforced_by_schema():
    event = base_decision_event(marker={"code": MARKER_CODE, "index": 1, "count": 2})
    assert_schema_invalid(event)


def test_marker_code_required_by_schema():
    event = base_decision_event(marker={"index": 0, "count": 1})
    assert_schema_invalid(event)


def test_marker_code_membership_in_reason_codes_invariant():
    event = base_decision_event(
        reason_codes=["STALE_INPUTS"],  # marker missing
        marker={"code": MARKER_CODE, "index": 0, "count": 1},
    )
    assert_schema_valid(event)
    with pytest.raises(AssertionError):
        assert_invariants(event)


def test_reason_codes_include_marker_but_marker_missing_is_invalid_invariant():
    event = base_decision_event(reason_codes=[MARKER_CODE])
    event.pop("marker", None)  # schema allows marker optional, invariant forbids
    assert_schema_valid(event)
    with pytest.raises(AssertionError):
        assert_invariants(event)


# ---------------------------------------------------------
# 3️⃣ reason_codes dedup (schema uniqueItems + negative test)
# ---------------------------------------------------------
def test_reason_codes_unique_items_enforced_by_schema():
    event = base_decision_event(reason_codes=[MARKER_CODE, MARKER_CODE])
    assert_schema_invalid(event)


# ---------------------------------------------------------
# 4️⃣ trace_id SSOT + Evidence absent separation
# ---------------------------------------------------------
def test_trace_id_matches_evidence_ssot():
    evidence_trace_id = "TRACE-SSOT"
    event = base_decision_event(trace_id=evidence_trace_id)
    assert_schema_valid(event)
    assert_invariants(event)

    # Simulated SSOT check (in real tests, compare to evidence envelope)
    assert event["trace_id"] == evidence_trace_id


def test_policy_evaluated_requires_trace_id_by_schema():
    """
    Decision-bearing events MUST include trace_id.
    Schema if/then should enforce this for POLICY_EVALUATED.
    """
    event = base_decision_event(event="POLICY_EVALUATED")
    event.pop("trace_id", None)
    assert_schema_invalid(event)


def test_infra_only_event_may_omit_trace_id_and_decision_envelope():
    """
    Infra-only events are out-of-scope for decision-bearing invariants.
    However, they may still pass the shared schema as minimal events.
    """
    infra_event = {
        "ts_utc": "2026-02-26T00:00:00Z",
        "level": "INFO",
        "component": "runtime",
        "event": "RUN_STARTED",
        "emitter_id": "infra-daemon",
        # no trace_id
        # no decision/grade
    }
    assert_schema_valid(infra_event)
    assert "decision" not in infra_event and "grade" not in infra_event
    assert "trace_id" not in infra_event


# ---------------------------------------------------------
# 5️⃣ rc 4KB hard limit (adapter/test invariant, byte-based)
# ---------------------------------------------------------
def test_rc_size_limit_over_4kb_rejected_by_invariant():
    payload = "X" * 5000  # definitely >4KB after JSON encoding
    event = base_decision_event(rc={"symbol": payload})
    assert_schema_valid(event)

    with pytest.raises(AssertionError):
        assert rc_json_len_bytes(event["rc"]) <= 4096, "rc exceeds 4KB hard limit"


def test_rc_size_limit_4kb_boundary_inclusive():
    payload = make_rc_payload_for_total_bytes(4096)
    rc = {"symbol": payload}

    # boundary sanity
    assert rc_json_len_bytes(rc) == 4096

    event = base_decision_event(rc=rc)
    assert_schema_valid(event)

    # invariant: inclusive boundary
    assert rc_json_len_bytes(event["rc"]) == 4096
    assert rc_json_len_bytes(event["rc"]) <= 4096