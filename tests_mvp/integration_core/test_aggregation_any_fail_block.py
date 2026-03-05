from __future__ import annotations

from integration_core.aggregation import AnyFailBlockPolicy, ValidationOutcome


def test_any_fail_block_allows_when_all_pass():
    p = AnyFailBlockPolicy()
    outcomes = [
        ValidationOutcome(val_id="VAL-1", status="PASS"),
        ValidationOutcome(val_id="VAL-2", status="PASS"),
    ]
    d = p.evaluate(outcomes)
    assert d.decision == "ALLOW"
    assert d.summary["counts"]["FAIL"] == 0
    assert d.summary["total"] == 2


def test_any_fail_block_allows_when_warn_only():
    p = AnyFailBlockPolicy()
    outcomes = [
        ValidationOutcome(val_id="VAL-1", status="WARN"),
        ValidationOutcome(val_id="VAL-2", status="WARN"),
    ]
    d = p.evaluate(outcomes)
    assert d.decision == "ALLOW"
    assert d.summary["counts"]["FAIL"] == 0
    assert d.summary["counts"]["WARN"] == 2


def test_any_fail_block_blocks_when_any_fail_exists():
    p = AnyFailBlockPolicy()
    outcomes = [
        ValidationOutcome(val_id="VAL-1", status="PASS"),
        ValidationOutcome(val_id="VAL-2", status="FAIL"),
        ValidationOutcome(val_id="VAL-3", status="WARN"),
    ]
    d = p.evaluate(outcomes)
    assert d.decision == "BLOCK"
    assert d.summary["counts"]["FAIL"] == 1
    assert "failed_val_ids" in d.summary
    assert d.summary["failed_val_ids"] == ["VAL-2"]


def test_any_fail_block_blocks_when_empty_fail_safe():
    p = AnyFailBlockPolicy()
    d = p.evaluate([])
    assert d.decision == "BLOCK"
    assert d.summary["total"] == 0