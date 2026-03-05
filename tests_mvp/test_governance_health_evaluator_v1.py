# tests_mvp/test_governance_health_evaluator_v1.py
from __future__ import annotations

import pytest

from tools.governance_health.health_evaluator_v1 import GovernanceHealthEvaluatorV1, HealthConfig


def test_health_eval_green_when_gate_pass_and_chain_ok():
    ev = GovernanceHealthEvaluatorV1()
    gate = {"decision": "ALLOW", "grade": "PASS", "policy_ref": "POLICY-VALAGG-MED-001"}
    chain = {"status": "PASS"}
    r = ev.evaluate(gate_decision=gate, chain_result=chain)

    assert 0 <= r.score <= 100
    assert r.status == "GREEN"
    assert r.incident_class == "NONE"
    assert "gate_grade=PASS" in r.rationale


def test_health_eval_amber_when_gate_warn():
    ev = GovernanceHealthEvaluatorV1()
    gate = {"decision": "ALLOW", "grade": "WARN"}
    chain = {"status": "PASS"}
    r = ev.evaluate(gate_decision=gate, chain_result=chain)

    assert r.status == "AMBER"
    assert r.incident_class in ("P2", "P1", "P0")  # v1에서는 P2로 매핑
    assert r.incident_class == "P2"


def test_health_eval_red_when_gate_fail_or_block():
    ev = GovernanceHealthEvaluatorV1()
    gate = {"decision": "BLOCK", "grade": "FAIL", "reason": "AnyFailBlockPolicy"}
    chain = {"status": "PASS"}
    r = ev.evaluate(gate_decision=gate, chain_result=chain)

    assert r.status == "RED"
    assert r.incident_class == "P0"
    assert "gate_grade=FAIL" in r.rationale


def test_health_eval_chain_fail_caps_even_if_gate_pass():
    cfg = HealthConfig(chain_fail_cap=20, score_pass=90)
    ev = GovernanceHealthEvaluatorV1(cfg)
    gate = {"decision": "ALLOW", "grade": "PASS"}
    chain = {"status": "FAIL", "violations": [{"code": "X"}]}
    r = ev.evaluate(gate_decision=gate, chain_result=chain)

    assert r.score == 20
    assert r.status == "RED"
    assert "cap=20" in r.rationale


def test_health_eval_chain_errors_present_caps_to_warn():
    ev = GovernanceHealthEvaluatorV1()
    gate = {"decision": "ALLOW", "grade": "PASS"}
    chain = {"status": "PASS", "errors": ["something"]}
    r = ev.evaluate(gate_decision=gate, chain_result=chain)

    assert r.status in ("AMBER", "GREEN")
    assert r.status == "AMBER"
    assert "chain_errors_present" in r.rationale


@pytest.mark.parametrize("gate", [
    {"decision": "ALLOW"},        # grade missing
    {"grade": "PASS"},            # decision missing
    {},                           # both missing
])
def test_health_eval_duck_typing_accepts_partial_inputs(gate):
    ev = GovernanceHealthEvaluatorV1()
    chain = {"status": "PASS"}
    r = ev.evaluate(gate_decision=gate, chain_result=chain)

    assert 0 <= r.score <= 100
    assert r.status in ("GREEN", "AMBER", "RED")