# KR_US_INSTITUTIONAL_BOT/tests/test_layer1_shape.py
from src.fsm.invariants.layer1_shape import check_shape_and_order


def test_layer1_ok_post_canonicalize():
    events = [
        {"event_type": "TRANSITION", "from_state": "S0_INIT", "to_state": "S1_COLLECTED", "_seq_int": 1},
        {"event_type": "TRANSITION", "from_state": "S1_COLLECTED", "to_state": "S2_REHEARSAL_PROVEN", "_seq_int": 2},
    ]
    res = check_shape_and_order(events)
    assert res == []


def test_layer1_seq_gap_post_canonicalize():
    events = [
        {"event_type": "TRANSITION", "from_state": "S0_INIT", "to_state": "S1_COLLECTED", "_seq_int": 1},
        {"event_type": "TRANSITION", "from_state": "S1_COLLECTED", "to_state": "S2_REHEARSAL_PROVEN", "_seq_int": 3},
    ]
    res = check_shape_and_order(events)
    assert any(v.code == "L1_SEQ_GAP" for v in res)
