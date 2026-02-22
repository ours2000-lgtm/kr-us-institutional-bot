from __future__ import annotations

import pytest

from integration_core.consistency import ConsistencyMode, ConsistencyResult, enforce


def test_enforce_warn_never_raises():
    enforce(ConsistencyResult(ok=False, message="drift", drift_code="DRIFT_X"), mode=ConsistencyMode.warn)


def test_enforce_block_raises_on_drift():
    with pytest.raises(RuntimeError):
        enforce(ConsistencyResult(ok=False, message="drift", drift_code="DRIFT_X"), mode=ConsistencyMode.block)


def test_enforce_ok_never_raises():
    enforce(ConsistencyResult(ok=True, message="ok"), mode=ConsistencyMode.block)