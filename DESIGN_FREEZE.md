---

## STRATEGY v1.1 — Design Contract (PRE-FREEZE)

**Effective Date:** 2025-12-18  
**Owner:** Risk Engine  
**Status:** Active (Not Frozen)

### Role & Scope
- STRATEGY decisions are advisory-only with respect to ACCOUNT; they can only tighten, never relax, ACCOUNT outcomes.
- ACCOUNT validator MUST reject AppliesScope.STRATEGY.
- STRATEGY validator MUST require ACCOUNT outcome as input (fact).
- STRATEGY validator MUST short-circuit when ACCOUNT outcome ≠ ALLOW.

### Input Model
- account_outcome: ValidationOutcome (fact; immutable)
- strategy_id: str
- snapshot_quality_grade: StrategyQualityGrade
- system_health_grade: StrategyHealthGrade

### Grade System
- Grades: GOOD / DEGRADED / UNKNOWN
- DEGRADED and UNKNOWN MUST map to FAIL-CLOSED at STRATEGY level.
- UNKNOWN always escalates to at least BLOCK.

### FAIL-CLOSED Rules
- ACCOUNT ≠ ALLOW → STRATEGY outcome MUST equal ACCOUNT outcome.
- ACCOUNT == ALLOW:
  - GOOD + GOOD → ALLOW
  - Any DEGRADED or UNKNOWN → BLOCK
- Any case not explicitly listed MUST default to BLOCK (FAIL-CLOSED).

### Prohibited Behavior
- STRATEGY v1.1 MUST NOT generate HARD_STOP independently.
- STRATEGY validator MUST NOT reinterpret, override, or downgrade ACCOUNT outcomes.
- No dependency on wall-clock time, global process state, or external I/O during evaluation.

### Determinism & Invariants
- Deterministic evaluation (same input → same output).
- Strict enum handling.
- FAIL-CLOSED is non-overridable.

### Testing Invariants
- ACCOUNT outcomes are treated as fixtures/facts, not recomputed.
- Cross-layer invariants MUST hold:
  - ACCOUNT = HARD_STOP → STRATEGY = HARD_STOP
  - ACCOUNT = BLOCK → STRATEGY = BLOCK
  - ACCOUNT = ALLOW → STRATEGY determined solely by strategy grades

---

## Risk Engine Versioning
ACCOUNT v1.1 defines the immutable base contract for all higher-level risk layers.
See DESIGN_FREEZE.md (ACCOUNT v1.1 Freeze Contract).
Future: STRATEGY and ORDER layers extend this baseline without modifying ACCOUNT v1.1.
ACCOUNT v1.1 guarantees forward compatibility for all higher-level layers as long as they do not modify the frozen contract.







