from __future__ import annotations

from integration_core.lifecycle import LifecycleState


def test_lifecycle_values():
    assert LifecycleState.Draft.value == "Draft"
    assert LifecycleState.Reviewed.value == "Reviewed"
    assert LifecycleState.Approved.value == "Approved"
    assert LifecycleState.Active.value == "Active"
    assert LifecycleState.Deprecated.value == "Deprecated"
    assert LifecycleState.Archived.value == "Archived"