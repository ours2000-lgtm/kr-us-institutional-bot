# COMMIT_PLAN_v1.0

## Scope
This commit plan covers MVP bootstrap for `integration_core` traceability contracts and the isolated `tests_mvp` suite.
Goal: Establish FAIL-CLOSED traceability ID contract (PREFIX-UUIDv4) and a stable MVP test entrypoint.

## Current Status (Evidence)
- pytest entrypoint: `pytest.ini` configured to run `tests_mvp`
- integration_core package present under `src/integration_core`
- tests_mvp suite passes (including negative tests)
- Latest observed: `14 passed`

## Files (Add/Modify)

### 1) Packaging / Test Harness
- `pyproject.toml`
  - MVP deps: cryptography, networkx, pydantic
  - dev deps: pytest, pytest-cov, mypy, ruff, hypothesis, pre-commit
- `pytest.ini`
  - `testpaths = tests_mvp`
  - `pythonpath = src`
  - marker stub(s) allowed

### 2) Integration Core (Traceability)
- `src/integration_core/__init__.py`
- `src/integration_core/ids.py`
  - Contract: `PREFIX-UUIDv4`
  - Prefix policy: STRICT uppercase + digits + underscore
  - Registry: default LOCK + optional env extension `TRACE_ID_PREFIXES`
  - Parser: UUID format + UUIDv4 enforcement
  - Fail-closed errors: `TraceabilityIdError`
- `src/integration_core/lifecycle.py`
- `src/integration_core/consistency.py`

### 3) MVP Tests (Isolated)
- `tests_mvp/integration_core/test_ids.py`
- `tests_mvp/integration_core/test_ids_negative.py`
- `tests_mvp/integration_core/test_lifecycle.py`
- `tests_mvp/integration_core/test_consistency_stub.py`

## Pre-Commit Verification Commands (Local)
Run from repo root:

1) Confirm root + config
- `cd /d E:\KR_US_INSTITUTIONAL_BOT`
- `python -c "import sys; print(sys.executable)"`

2) Unit tests
- `pytest -q`

3) Optional: show pytest config resolution
- `pytest --trace-config -q`

## Commit(s)
### Commit 1 — MVP: integration_core traceability contract + isolated tests
**Message (recommended):**
`[mvp][integration_core] TraceabilityId contract + tests_mvp harness`

**Includes:**
- integration_core traceability contract (PREFIX-UUIDv4, strict uppercase prefix)
- pytest.ini to isolate MVP suite (`tests_mvp`)
- tests_mvp positive/negative/property tests
- minimal lifecycle/consistency stubs for integration boundary

## Post-Commit Tag (Optional)
- `git tag -a mvp-traceability-v1.0 -m "MVP TraceabilityId contract (PREFIX-UUIDv4) + tests_mvp passing"`

## Notes / Guardrails
- Contract is FAIL-CLOSED: malformed prefix or non-v4 UUID MUST reject.
- Prefix registry default is LOCK; env-based extension is allowed only under governance control and must be evidenced.
- `tests/` (legacy) is intentionally excluded from MVP execution path to prevent unrelated import/contract drift.