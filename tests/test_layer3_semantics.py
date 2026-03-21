# KR_US_INSTITUTIONAL_BOT/tests/test_layer3_semantics.py
from src.fsm.invariants.layer3_semantics import check_semantics


def test_layer3_missing_required_payload_fields():
    events = [
        {
            "event_type": "TRANSITION",
            "from_state": "S1_COLLECTED",
            "to_state": "S2_REHEARSAL_PROVEN",
            "payload": {},
        }
    ]
    res = check_semantics(events, terminal_states=set())
    assert any(v.code == "L3_PAYLOAD_MISSING_FIELD" for v in res)
