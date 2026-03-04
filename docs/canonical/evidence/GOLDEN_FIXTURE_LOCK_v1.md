# GOLDEN_FIXTURE_LOCK_v1 (CONST-001) — LOCK

Status: **LOCK**  
Const ID: **CONST-001**  
Scope: **Golden ALLOW fixture contract** for KR_US_INSTITUTIONAL_BOT Governance Validator  
Change Policy: **Amendment required** (Constitutional change)

## 0. Boundary
This document defines ONLY the **ALLOW Golden Path** fixture.  
FAIL_CLOSED / NOT_ALLOW fixtures and expectations are handled in a separate document set (e.g., FAIL_CLOSED_FIXTURES_v1).

## 1. Purpose
This document locks the minimal, canonical **ALLOW** evidence fixture.  
Any change to Golden semantics, required fields, or expected ALLOW outcome MUST follow Amendment Procedure.

## 2. Canonical Golden Fixture
Canonical fixture file:
- `tests/fixtures/traces/trace_ok_v1_signed.json`

The fixture MUST represent:
- A valid RUN_START (GENESIS marker)
- A valid lifecycle transition chain
- Version bindings present and valid
- Crypto Annex binding present and valid

## 3. State Machine Constraints (Minimal)
Allowed lifecycle (minimal):
- S0_INIT → S1_COLLECTED → S2_REHEARSAL_PROVEN → S3_ACTIVATED

Forbidden by default (non-exhaustive):
- Jumping to S2_* without S1_* (no skip)
- Any reverse transition (no rollback)
- Any transition out of terminal state (after-terminal forbidden)

## 4. Timeline Constraints (Minimal)
Within a single trace:
- `ts_utc` MUST be monotonic non-decreasing by event order.
- Future timestamps SHOULD be rejected in higher layers (policy-dependent); Golden fixture MUST NOT contain future timestamps.

## 5. Required Fields (Minimum)
Each record MUST contain:
- `event_type` (string)
- `ts_utc` (ISO8601 UTC string)
- `trace_id` (string)

RUN_START MUST contain:
- `emitter_id`
- `trace_id`
- `ts_utc`

TRANSITION MUST contain:
- `from_state`
- `to_state`
- `seq`
- `trace_id`
- `ts_utc`

Payload requirements:
- `payload` is REQUIRED for `to_state == "S2_REHEARSAL_PROVEN"`
- Minimal required payload keys for S2_REHEARSAL_PROVEN (L3):
  - `rehearsal_id`
  - `proof_hash`

## 6. Version Bindings (GSR-000)
At least one record MUST include:
- `semantic_ruleset_version == "GOV_SEMANTIC_RULES_v1"`
- `canonicalizer_profile_version == "CANONICALIZER_v1"`
- `cryptographic_policy_version == "CRYPTO_POLICY_v1"`

Interpretation:
- Missing bindings MUST result in FAIL_CLOSED.

## 7. Crypto Annex Envelope (GSR-051)
At least one record MUST include:
- `sig_alg` (e.g., "ED25519")
- `signer_id` (e.g., "gov-root")
- `key_ref` (e.g., "key-ed25519-gov-root-v1")
- `signature_value` (opaque string)

Interpretation:
- Invalid/missing Annex requirements MUST result in FAIL_CLOSED.

## 8. Expected Validator Outcome (LOCKED)
For `trace_ok_v1_signed.json`:
- `decision == "ALLOW"`
- `fail_closed == false`
- `failed_stage == "NONE"`
- `violations` MAY include WARNING/INFO only, but MUST NOT include BLOCKING/CRITICAL.

## 9. Example Snippets (Non-normative)

RUN_START example:
```json
{"event_type":"RUN_START","emitter_id":"E-LOCAL","trace_id":"T-001","ts_utc":"2026-02-05T00:00:00Z"}
TRANSITION example:

{"event_type":"TRANSITION","from_state":"S0_INIT","to_state":"S1_COLLECTED","seq":1,"trace_id":"T-001","ts_utc":"2026-02-05T00:00:01Z"}
10. Amendment Notes
Suggested storage:

docs/canonical/amendments/CONST-001_v2.md

Any changes to:

Required fields

Version binding semantics

Crypto Annex required fields

Expected ALLOW conditions
MUST be proposed as an amendment and reviewed.