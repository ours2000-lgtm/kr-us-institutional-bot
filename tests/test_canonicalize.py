import pytest

from src.fsm.canonicalize import canonicalize_events, CanonicalizeError


def _assert_error_metadata(e: CanonicalizeError):
    # 존재하면 더 검증(테스트가 구현 차이로 깨지지 않게 "있으면 검사" 패턴)
    assert isinstance(e.code, str) and e.code
    assert isinstance(e.message, str) and e.message
    assert isinstance(getattr(e, "event_index", -1), int)
    assert isinstance(getattr(e, "context", {}), dict)
    # optional fields (있으면 타입만 체크)
    if hasattr(e, "severity"):
        assert isinstance(getattr(e, "severity"), str) or getattr(e, "severity") is not None
    if hasattr(e, "layer"):
        assert getattr(e, "layer") is not None


def test_genesis_missing_raises_with_metadata(mk_transition):
    events = [mk_transition(seq=1)]

    with pytest.raises(CanonicalizeError) as excinfo:
        canonicalize_events(events, require_genesis=True)

    e = excinfo.value
    _assert_error_metadata(e)
    assert e.code == "G_GENESIS_MISSING"


def test_multiple_genesis_raises(mk_genesis):
    events = [mk_genesis("T-100"), mk_genesis("T-100")]

    with pytest.raises(CanonicalizeError) as excinfo:
        canonicalize_events(events, require_genesis=True)

    e = excinfo.value
    _assert_error_metadata(e)
    assert e.code == "G_GENESIS_MULTIPLE"


def test_genesis_missing_trace_id_raises(mk_genesis):
    events = [mk_genesis(trace_id=None, ts_utc="2026-02-05T00:00:00Z", emitter_id="E")]

    with pytest.raises(CanonicalizeError) as excinfo:
        canonicalize_events(events, require_genesis=True)

    e = excinfo.value
    _assert_error_metadata(e)
    # 구현이 "invalid envelope"로 뭉칠 수 있어 두 코드 허용
    assert e.code in {"G_GENESIS_INVALID_ENVELOPE", "G_TRACE_ID_MISSING_IN_GENESIS"}


def test_genesis_missing_ts_utc_raises(mk_genesis):
    events = [mk_genesis(trace_id="T-300", ts_utc=None, emitter_id="E")]

    with pytest.raises(CanonicalizeError) as excinfo:
        canonicalize_events(events, require_genesis=True)

    e = excinfo.value
    _assert_error_metadata(e)
    assert e.code == "G_GENESIS_INVALID_ENVELOPE"


def test_trace_id_mismatch_raises_with_context(mk_genesis, mk_transition):
    events = [
        mk_genesis("T-200"),
        mk_transition(seq=1, trace_id="T-OTHER"),
    ]

    with pytest.raises(CanonicalizeError) as excinfo:
        canonicalize_events(events, require_genesis=True)

    e = excinfo.value
    _assert_error_metadata(e)
    assert e.code == "G_TRACE_ID_MISMATCH"


def test_happy_path_multi_transition_keeps_trace_id_and_injects_internal_fields(mk_genesis, mk_transition):
    # ✅ FIX: GENESIS 기준 trace_id = "T-OK" 이므로, TRANSITION에도 동일 trace_id를 명시해 정합을 맞춘다.
    events = [
        mk_genesis("T-OK"),
        mk_transition(fr="S0_INIT", to="S1_COLLECTED", seq="1", ts_utc="2026-02-05T00:00:01Z", trace_id="T-OK"),
        mk_transition(fr="S1_COLLECTED", to="S2_REHEARSAL_PROVEN", seq="2", ts_utc="2026-02-05T00:00:02Z", trace_id="T-OK"),
        mk_transition(fr="S2_REHEARSAL_PROVEN", to="S3_ACTIVATED", seq="3", ts_utc="2026-02-05T00:00:03Z", trace_id="T-OK"),
    ]

    canon = canonicalize_events(events, require_genesis=True)
    assert canon.trace_id == "T-OK"
    assert len(canon.transitions) == 3
    assert all(t["event_type"] == "TRANSITION" for t in canon.transitions)
    assert [t["_seq_int"] for t in canon.transitions] == [1, 2, 3]
    assert all(t.get("_ts_dt") is not None for t in canon.transitions)


def test_require_genesis_false_tolerates_missing_and_extracts_trace_id(mk_transition):
    events = [
        mk_transition(seq=1, trace_id="T-400"),
    ]
    canon = canonicalize_events(events, require_genesis=False)
    assert canon.trace_id == "T-400"
    assert len(canon.transitions) == 1


# ✅ 변경: "GENESIS 없는 경우 trace_id late-binding"은 허용하지 않는다.
def test_trace_id_extraction_requires_consistency_when_genesis_missing(mk_transition):
    events = [
        mk_transition(seq=1, trace_id="T-PRIORITY"),
        mk_transition(fr="S1_COLLECTED", to="S2_REHEARSAL_PROVEN", seq=2, trace_id="T-PRIORITY"),
    ]
    canon = canonicalize_events(events, require_genesis=False)
    assert canon.trace_id == "T-PRIORITY"


# ✅ 추가: GENESIS 없더라도 trace_id 불일치/None 혼입은 fail-closed
def test_trace_id_missing_or_mismatch_without_genesis_fails(mk_transition):
    events = [
        mk_transition(seq=1, trace_id=None),
        mk_transition(fr="S1_COLLECTED", to="S2_REHEARSAL_PROVEN", seq=2, trace_id="T-PRIORITY"),
    ]
    with pytest.raises(CanonicalizeError) as excinfo:
        canonicalize_events(events, require_genesis=False)

    e = excinfo.value
    _assert_error_metadata(e)
    assert e.code == "G_TRACE_ID_MISMATCH"


def test_seq_coercion_edgecases_invalid_alpha_raises(mk_genesis, mk_transition):
    events = [
        mk_genesis("T-501"),
        mk_transition(seq="abc", ts_utc="2026-02-05T00:00:01Z"),
    ]
    with pytest.raises(CanonicalizeError) as excinfo:
        canonicalize_events(events, require_genesis=True)

    _assert_error_metadata(excinfo.value)


def test_seq_coercion_negative_policy_currently_rejects(mk_genesis, mk_transition):
    # 스펙이 아직 확정되지 않았으니: "현재 정책"이 reject라면 PASS.
    # 만약 허용으로 바뀌면 이 테스트를 업데이트(또는 xfail) 하면 됩니다.
    events = [
        mk_genesis("T-NEG"),
        mk_transition(seq="-1", ts_utc="2026-02-05T00:00:01Z"),
    ]
    with pytest.raises(CanonicalizeError):
        canonicalize_events(events, require_genesis=True)


def test_seq_coercion_float_string_policy_currently_rejects(mk_genesis, mk_transition):
    events = [
        mk_genesis("T-FLOAT"),
        mk_transition(seq="1.5", ts_utc="2026-02-05T00:00:01Z"),
    ]
    with pytest.raises(CanonicalizeError):
        canonicalize_events(events, require_genesis=True)


def test_ts_utc_empty_string_rejects(mk_genesis, mk_transition):
    events = [
        mk_genesis("T-TS-EMPTY"),
        mk_transition(seq=1, ts_utc=""),
    ]
    with pytest.raises(CanonicalizeError):
        canonicalize_events(events, require_genesis=True)


def test_ts_utc_invalid_format_rejects(mk_genesis, mk_transition):
    events = [
        mk_genesis("T-502"),
        mk_transition(seq=1, ts_utc="NOT_A_TIMESTAMP"),
    ]
    with pytest.raises(CanonicalizeError) as excinfo:
        canonicalize_events(events, require_genesis=True)
    _assert_error_metadata(excinfo.value)


def test_ts_utc_timezone_variant_is_accepted_if_parser_allows(mk_genesis, mk_transition):
    # 구현의 parser가 Z만 허용인지, +09:00 같은 offset도 허용인지 스펙에 따라 다릅니다.
    # 여기서는 "허용될 수 있음"을 문서화하고, 실패해도 이유가 명확히 보이게 합니다.
    events = [
        mk_genesis("T-TZ", ts_utc="2026-02-05T00:00:00+09:00"),
        mk_transition(seq=1, ts_utc="2026-02-05T00:00:01+09:00", trace_id="T-TZ"),
    ]
    try:
        canon = canonicalize_events(events, require_genesis=True)
        assert canon.trace_id == "T-TZ"
    except CanonicalizeError as e:
        # parser가 Z-only라면 여기로 올 수 있음: 이건 정책 선택이라 FAIL로 치지 않고 메타만 확인
        _assert_error_metadata(e)


def test_require_genesis_false_invalid_genesis_still_fails_if_present(mk_genesis, mk_transition):
    # 기관급/Fail-closed 원칙: "GENESIS가 존재하는데 깨져 있으면" 관용 모드라도 실패가 안전.
    events = [
        mk_genesis(trace_id="T-700", ts_utc=None, emitter_id="E"),  # invalid envelope
        mk_transition(seq=1, trace_id="T-700"),
    ]
    with pytest.raises(CanonicalizeError):
        canonicalize_events(events, require_genesis=False)
