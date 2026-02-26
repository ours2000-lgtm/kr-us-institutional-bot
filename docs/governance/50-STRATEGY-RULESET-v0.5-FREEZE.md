# STRATEGY-RULESET v0.5 FREEZE

Status: FROZEN  
Tag: STRATEGY-RULESET-v0.5-FREEZE  
Date: 2026-02-26  

---

## Scope of Freeze

The following components are hereby declared frozen:

- RuleSet.strategy dispatch semantics
- quorum strategy (k-based composite rule)
- fail_closed strategy behavior
- PolicyOverride semantics (replace / patch / force)
- run_consistency_pipeline override resolution logic
- CompositePolicyDecision marker invariants
- Evidence hash invariants (rich_context excluded)

---

## Behavioral Guarantees Locked

1. quorum strategy uses integer `k` and fails fast if `k > enabled_count`.
2. Composite marker reason code MUST appear:
   - Exactly once
   - At index 0
3. rich_context MUST NOT affect:
   - inputs_hash
   - evidence_hash
4. Override operations MUST NOT break marker or hash invariants.
5. Registry-based PolicySet resolution order is deterministic.

---

## Amendment Requirement

Any modification to:

- RuleSet parameters
- Strategy dispatch logic
- Override precedence rules
- Composite marker contract
- Hash construction inputs

REQUIRES formal amendment procedure.

---

## Intent

This freeze establishes:

- Institutional-grade policy strategy layer
- Deterministic override semantics
- Stable audit-grade evidence hashing

Further evolution (e.g., weighted strategy) MUST occur in a new version track.