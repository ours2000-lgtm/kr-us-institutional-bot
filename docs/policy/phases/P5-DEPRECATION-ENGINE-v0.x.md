# Phase 5 — Deprecation Engine Spec v0.x
Status: NON-BINDING (Operational Spec)

---

## 0. Metadata

- Document ID: P5-DEPRECATION-ENGINE-v0.x
- Status: NON-BINDING
- Scope:
  - Operational mechanics for lifecycle state evaluation and propagation
  - Event model for state transitions (Deprecation / Revocation)
  - Downstream enforcement signals and compatibility rules
  - Audit log schema requirements for lifecycle events
  - Replay/recovery expectations (engine-level)
- Parent References:
  - Phase5_Core_Policy_Bundle_v0x.md (FROZEN)
  - P5-DEPRECATION-POLICY-v0.x.md (HARDENED)
- Maintainer:
  - CE-WG (policy ownership) + Reliability/Platform (implementation)
- Change Policy:
  - MAY evolve without changing policy meaning
  - MUST remain consistent with policy semantics and core invariants

---

## 1. Purpose

This document defines *how to implement* lifecycle transitions and how to emit operational signals while preserving:
- policy meaning (Deprecated/Revoked semantics),
- core invariants (fail-closed posture for admission-critical).

---

## 2. Engine Inputs and Sources of Truth

### 2.1 Inputs
- Evidence Catalog entries (current state, attributes)
- Lifecycle events (deprecation/revocation actions)
- Integrity signals (hash chain verification results, signature checks, tooling integrity alerts)
- Optional: RTM references for dependency/impact computations

### 2.2 Sources of Truth
- Policy meaning: P5-DEPRECATION-POLICY-v0.x
- Core invariants: Phase5_Core_Policy_Bundle_v0x

---

## 3. State Transition Rules (Engine Constraints)

### 3.1 Allowed Transition Families
Engine MUST implement transitions consistent with policy semantics.

Typical transitions:
- Draft → Verified → Attested
- Verified/Attested → Stale → (Verified/Attested)   (re-validation path, if supported)
- Any → Deprecated
- Any → Revoked  (exceptional invalidation; terminal)

### 3.2 Forbidden Transitions
- Revoked → any other state (Revoked is terminal)

Deprecated → Verified/Attested MUST NOT occur via silent in-place mutation.  
Governance-authorized recoveries MUST be expressed as:
- new Evidence IDs, or
- explicit recovery events,
not silent overwrites.

---

## 4. Event Model

### 4.1 Lifecycle Event Types
- EVIDENCE_DEPRECATED
- EVIDENCE_REVOKED
- EVIDENCE_REVALIDATED (optional)
- EVIDENCE_RECOVERY_APPLIED (guarded; explicit)
- EVIDENCE_EVENT_REJECTED (engine-generated)

### 4.2 Required Envelope Fields (MUST)
All lifecycle events MUST include:
- schema_version
- correlation_id
- event_id
- event_type
- timestamp_utc
- actor_id
- evidence_id
- prev_state
- new_state
- reason_code

### 4.3 Correlation Consistency (MUST)
Events within the same governance workflow MUST share the same correlation_id.

### 4.4 Event Rejection Logging (MUST)
If EVIDENCE_EVENT_REJECTED is emitted, the engine MUST record:
- rejection_reason
- rejection_cause_category (e.g., taxonomy_mismatch, missing_replacement, cycle_detected)
- referenced_event_id (if applicable)

Rejected lifecycle events SHOULD also produce a GOVERNANCE_DEBT_SIGNAL with at least WARN severity.

### 4.5 Tamper-Evidence (SHOULD)
Event records SHOULD be tamper-evident via:
- hash chaining,
- signatures, or
- append-only ledgers.

---

## 5. Validation & Integrity Checks (Engine-Level)

### 5.1 Reason Code Validation (MUST)
Engine MUST validate reason_code against the configured centralized taxonomy set.  
Non-conforming reason codes MUST be rejected (EVIDENCE_EVENT_REJECTED).

### 5.2 Replacement Chain Integrity (MUST for Admission-critical)
On receipt of an event with replacement_evidence_id, engine MUST validate:
- replacement exists (or is resolvable), and
- replacement chain is acyclic (DAG validation; depth limits MAY be applied).

If validation fails:
- engine MUST emit EVIDENCE_EVENT_REJECTED, and
- for Admission-critical impacted scopes, engine MUST emit an ADMISSION_BLOCK_SIGNAL (fail-closed).

---

## 6. Downstream Signals & Enforcement Hooks

### 6.1 Signal Types (Recommended Set)
Engine SHOULD produce machine-readable signals such as:
- ADMISSION_BLOCK_SIGNAL
- ADMISSION_RISK_SIGNAL
- DEPRECATION_WARNING
- REPLACEMENT_REQUIRED
- HISTORY_ONLY_ALLOWED
- GOVERNANCE_DEBT_SIGNAL
- GRACE_WINDOW_ACTIVE (if grace is applied downstream)

Signals MUST include severity.  
Severity SHOULD be one of: info, warn, critical, block.

Signal TTL / expiry semantics MAY be supported; if supported, TTL MUST be explicit in the signal payload.

### 6.2 Default Enforcement Guidance
- Revoked MUST emit ADMISSION_BLOCK_SIGNAL.
- Deprecated SHOULD emit rejection-by-default signal for new admissions, while preserving historical reproducibility modes.

---

## 7. Retroactive Invalidation (Propagation Pattern)

### 7.1 Revocation Propagation (MUST baseline)
If Evidence X is Revoked, engine MUST propagate invalidation signals at least to 1-hop dependent evidence scopes.  
Propagation beyond 1-hop SHOULD require governance-approved configuration or explicit policy setting.

Engine MUST record propagation mode in event metadata:
- propagation_mode: realtime | batch (or equivalent)

### 7.2 Ghost / Zombie Approval Prevention (Fail-Closed) (MUST)
Admission evaluators MUST NOT rely solely on local caches for revocation status.

At decision time, evaluators MUST consult a global revocation source of truth (revocation registry/index).  
If the evaluator cannot reach the global revocation source:
- the decision MUST default to fail-closed behavior (e.g., treat as UNKNOWN and HOLD/BLOCK as configured for admission-critical scope).

---

## 8. Auditability, Replay, and Determinism

### 8.1 As-of Reconstruction (MUST capability)
Systems MUST support “as-of” reconstruction to determine:
- what state was known,
- what evidence was eligible,
- what lifecycle events were active,
at the time an admission decision was made.

### 8.2 Dual Timeline (MUST)
Implementations MUST distinguish and store:
- Valid Time: when evidence was produced
- Transaction Time: when events/states were recorded and used

Audit queries MUST be able to surface both.

### 8.3 Replay Determinism (MUST)
Given the same event stream (ordered by Transaction Time) and the same initial state,
the engine MUST reproduce the same resulting states and emitted signals.

Event handlers SHOULD be designed to be idempotent to support safe replay.

---

## 9. Compatibility With Freshness Engine

Shared taxonomy:
- reason_code taxonomies SHOULD be shared across lifecycle and freshness engines where feasible.

Cross-engine fail-closed rule:
- Revoked Evidence MUST be treated as RED-equivalent for freshness evaluation and MUST NOT be considered eligible regardless of computed freshness.

Shared envelope fields MUST at minimum include:
- event_id, schema_version, correlation_id, evidence_id, timestamp_utc, actor_id, prev_state, new_state, reason_code

---

## 10. References

- Phase5_Core_Policy_Bundle_v0x.md (FROZEN)
- P5-DEPRECATION-POLICY-v0.x.md (HARDENED)
- Evidence_Catalog.md
- RTM_v0x.md
- Reason_Code_Taxonomy.md (placeholder)
