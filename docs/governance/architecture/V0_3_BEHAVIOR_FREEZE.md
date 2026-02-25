# 🧱 v0.3 Implementation DoD (Single Source of Truth)

STATUS: BEHAVIOR_FREEZE  
SCOPE: v0.3 Consistency / Strict Reachability / Compliance Stub  
DATE: 2026-02-25

This document freezes the behavioral contract of v0.3.

Any subsequent changes MUST be treated as a versioned change
and MUST NOT silently alter the semantics defined here.

---

## 0️⃣ Definitions (Normative)

### Node prefixes
- PLAN-*
- VAL-*
- ROLLOUT-*
- Unknown prefixes MAY exist and MUST NOT crash the checker.

### Edge model (input contract)
edges: list[dict] with at least:
- from_id: str
- to_id: str
- rel: str
- rel_version: int

MVP required edge metadata (enforced in v0.2 and carried into v0.3):
- timestamp
- principal
- evidence_ref

Optional (NOT enforced in v0.3 baseline):
- policy_ref
- signature

### Allowed relations (MVP)
- PLAN_TO_VAL
- VAL_TO_ROLLOUT

---

## 1️⃣ strict reachability code

### 🎯 Goal
Freeze the decision logic:
For each ROLLOUT, determine whether there exists a **valid** PLAN→VAL→ROLLOUT path.

### 🧩 Scope

#### ✔ VAL invariant (VALID VAL definition)
A VAL node is considered **VALID** iff:
- incoming PLAN_TO_VAL edges == 1

Any VAL that has zero or more than one upstream PLAN_TO_VAL edge
MUST NOT be considered part of a valid PLAN→VAL→ROLLOUT path.

#### ✔ Path logic (STRICT reachability)
For each ROLLOUT:
- Start from PLAN nodes (as path sources)
- A path is valid only if it includes at least one VALID VAL
- The ROLLOUT passes strict reachability iff **at least one** valid path exists

#### ✔ Internal result model (behavioral contract)
StrictReachabilityResult
{
  rollout_id: str
  has_valid_path: bool
  reasons: list[str]
}

Notes:
- reasons[] MUST be deterministic and suitable for assertions in tests.
- reasons[] SHOULD contain stable keywords for debugging (e.g., "NO_VALID_PATH", "VAL_INVALID_UPSTREAM").

### ✅ Done criteria (must pass)
- VALID VAL predicate exists
- ROLLOUT-wise evaluation function exists
- Tests PASS:
  - valid chain
  - orphan VAL
  - multi PLAN VAL
- Tests can assert result model fields directly

---

## 2️⃣ ComplianceRecord builder + on_record

### 🎯 Goal
Freeze record creation as a pure function.

### 🧩 Scope

#### ✔ Builder (pure function)
build_compliance_record(
    snapshot_id,
    reachability_result,
    mode,
    principal,
    timestamp=None
) -> ComplianceRecord

- If timestamp is None, builder MUST generate UTC ISO8601 timestamp internally.

#### ✔ Record structure (minimum SSOT)
Required fields:
- snapshot_id OR graph_hash (at least one MUST be present)
- violations[]
- mode
- decision
- timestamp_utc
- principal

violations[] item minimal schema:
- code
- severity
- message

#### ✔ on_record hook
Callable[[ComplianceRecord], None]
- default is no-op

### ✅ Done criteria (must pass)
- builder is pure (no side effects)
- decision is deterministic given the same inputs
- violations mapping exists and is testable
- timestamp auto-generation test PASS
- on_record mock invocation test PASS
- Record can be produced without calling enforce() (builder-only path)

---

## 3️⃣ enforce(mode) wiring (Public API freeze)

### 🎯 Goal
Freeze the public API and mode semantics for v0.3.

### 🧩 Scope

enforce(
    nodes,
    edges,
    mode="warn"|"block"|"strict",
    on_record=None
) -> EnforcementDecision

#### ✔ Execution order (MUST)
1) strict reachability evaluation
2) ComplianceRecord creation (exactly one record)
3) on_record invocation (if provided)
4) decision return (or raise if blocking semantics require it)

#### ✔ Record cardinality (MUST)
Every enforce() call MUST produce exactly one ComplianceRecord,
regardless of decision (allowed/blocked).

#### ✔ Mode semantics (baseline v0.3)
| mode   | if valid path 없음 |
|--------|---------------------|
| strict | blocked             |
| block  | blocked             |
| warn   | allowed             |

Notes:
- warn mode MUST still emit violations and ComplianceRecord.
- strict/block MUST be behaviorally equivalent in v0.3 baseline.
  (Future versions MAY diverge; such divergence MUST be versioned.)

### ✅ Done criteria (must pass)
- EnforcementDecision model exists
- mode-specific decision tests PASS
- on_record is called exactly once
- decision is deterministic
- public API stable for external callers

---

## 4️⃣ Tests (Behavior lock)

### 🎯 Goal
Lock SSOT behavior via scenario tests.

#### 🧩 strict reachability tests
- valid single chain
- orphan VAL
- multi PLAN VAL
- mixed valid/invalid path

#### 🧩 ComplianceRecord tests
- enforce 1회 → record 1개
- timestamp/principal 존재
- violations mapping 확인

#### 🧩 Integration tests
Same graph:
- mode="warn"  → allowed
- mode="block" → blocked
- mode="strict"→ blocked

### ✅ Done criteria (must pass)
- All scenarios PASS
- enforce behavior deterministic
- record content is assertable
- coverage includes invariant path branches

---

## Non-goals (Explicitly out of scope)
- Policy aggregation semantics
- Evidence pipeline persistence
- Cross-graph consistency