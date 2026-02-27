# GOVERNANCE HEALTH SCORING v0.1

Status: DRAFT (LOCK Candidate)  
Version: v0.1  
Date: 2026-02-27  

---

## 1. Purpose

This document defines a quantitative and gate-based health model for governance-layer observability and policy execution.

It provides:

- A strict FAIL-CLOSED gating model
- Numerical health and quality scores (0–100)
- Sustained-condition detection
- Promotion hints for taxonomy/backlog evolution
- Operational window parameters for reproducibility

This document does NOT alter decision/grade contracts.  
It operates strictly above existing PASS/WARN/BLOCK semantics.

---

## 2. Dimensional Model

Governance Health is composed of two orthogonal dimensions:

1) StrategyHealth (execution stability)  
2) StrategyQuality (signal integrity)  

These dimensions are symmetric FAIL-CLOSED axes.

---

## 3. Strict Symmetry Rule (v0.1 LOCK Principle)

If StrategyHealth ≠ GOOD → Gate = BLOCK  
If StrategyQuality ≠ GOOD → Gate = BLOCK  

GOOD → ALLOW  
DEGRADED → BLOCK  
CRITICAL / POOR → BLOCK  

This symmetry is intentional and reflects a strict FAIL-CLOSED governance philosophy.

Quality degradation is treated as potential systemic risk, not merely a monitoring signal.

---

## 4. Gate vs Score Separation

### 4.1 Governance Gate (Per-Event, Deterministic)

Derived from:

- decision / grade envelope  
- FAIL_CLOSED events  
- schema violations  
- invariant violations  
- hash-bound contract violations  

Gate Output:

- ALLOW  
- BLOCK  

Gate MUST remain deterministic and audit-safe.

---

### 4.2 Governance Score (Per-Window, Analytical)

Scores:

- health_score: 0–100  
- quality_score: 0–100  
- snapshot_grade: A/B/C/D  

Score is informational and MUST NOT override Gate.

---

## 5. Runtime Interface Example

Gate is evaluated per event.  
Score is evaluated per sliding window.  
Both are returned together.

```python
from dataclasses import dataclass
from enum import Enum

class GovernanceGateResult(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"

@dataclass
class GovernanceScoreResult:
    health_score: int
    quality_score: int
    snapshot_grade: str

@dataclass
class GovernanceEvaluation:
    gate: GovernanceGateResult
    score: GovernanceScoreResult
6. StrategyHealth Definition

Measures execution stability.

Signals:

FAIL_CLOSED rate

schema validation failures

invariant violations

override_hash_safe=false rate

pipeline_result degradation

v0.1 Default Thresholds
Metric	GOOD	DEGRADED	CRITICAL
WARN density	< 20%	20–40%	≥ 40%
FAIL_CLOSED rate (per 1k runs)	0	1–3	> 3
invariant violations	0	1	≥ 2 or sustained
override_hash_safe=false rate	0%	>0% and <1%	≥ 1%

Environment-specific overrides are permitted.

7. StrategyQuality Definition

Measures signal integrity and taxonomy stability.

Signals:

WARN density

sustained WARN clusters

reason_codes drift

promotion_hint volume

v0.1 Default Thresholds
Metric	GOOD	DEGRADED	POOR
WARN density	< 20%	20–40%	≥ 40%
sustained WARN clusters	0	1–2	≥ 3

Drift detection may initially be heuristic.

8. Sustained Condition Rule

A condition is "sustained" if:

Same reason_code

Same policy_ref

Occurs ≥ N times within time window T

Defaults (v0.1)

N = 5
T = 1 hour

Example:

SUSTAINED_N = 5
SUSTAINED_T = 3600

N and T MAY be overridden per environment or per policy_ref.

Sustained conditions generate promotion_hint objects.

9. Promotion Hint Model

Structure:

reason_code

policy_ref

occurrence_count

window_duration

first_seen_at

last_seen_at

promotion_hint is read-only and does not modify policy.

Operational Integration (Recommended)

Alerting hooks

Backlog auto-ticket creation

Weekly governance review ingestion

10. Score Computation (v0.1 Fixed Penalty Model)

Base:

health_score = 100
quality_score = 100

Penalties:

sustained WARN cluster: -5

FAIL_CLOSED: -10

invariant violation: -20

override_hash_safe=false: -5

Floor: 0

Future versions MAY introduce weight parameters:

w_warn_cluster

w_fail_closed

w_invariant_violation

w_override_hash

11. SnapshotQualityGrade

Derived grade:

A: 90–100
B: 75–89
C: 60–74
D: <60

Recommended Usage

A → Normal operation
B → Monitor (weekly review)
C → Operational improvement task
D → Governance incident + rollout restriction

Snapshot grade does NOT affect Gate directly.

12. Operational Parameters (v0.1)

Event window size: 1 hour (configurable)
Sliding interval: 5 minutes (overlapping rolling windows)

Gate evaluation: per event
Score evaluation: per window

Window range:

[now − window_size, now]

The health model operates strictly as read-only analytics and MUST NOT mutate execution decisions, gate outcomes, evidence hashes, or trace identifiers.

13. Strict Mapping (Default)

Health:

GOOD → GOOD
DEGRADED → non-GOOD
CRITICAL → non-GOOD

Quality:

GOOD → GOOD
DEGRADED → non-GOOD
POOR → non-GOOD

Gate rule:

If any dimension is non-GOOD → BLOCK

14. Operational Override Flag

Implementation MAY introduce:

TREAT_QUALITY_DEGRADED_AS_GOOD (default: false)

When true:

Quality=DEGRADED is treated as GOOD for Gate evaluation,
while still impacting Score and dashboards.

This enables phased rollout without weakening constitutional symmetry.

15. Invariants

Health scoring MUST NOT modify Gate logic.

Score MUST NOT override BLOCK.

Sustained detection MUST be deterministic.

Window computation MUST be reproducible.

Health model MUST remain read-only analytics.

16. Window Computation Determinism (v0.1)

To guarantee audit-grade reproducibility, window evaluation MUST follow these rules:

1) Time Source

All timestamps MUST be interpreted as UTC.
Window boundaries MUST use event.ts_utc, not system clock at evaluation time.

2) Window Definition

Let:

W = window_size (default 3600 seconds)

S = sliding_interval (default 300 seconds)

t_now = evaluation timestamp (UTC)

Window range:

[t_now - W, t_now]

Boundary condition is inclusive on both ends.

Events included MUST satisfy:

event.ts_utc >= window_start
AND
event.ts_utc <= window_end

3) Ordering

Events inside a window MUST be processed in deterministic order:

Primary key: event.ts_utc (ascending)
Secondary key: trace_id (lexicographically ascending)
Tertiary key: event (string name)

4) Deduplication

If duplicate events are detected
(same trace_id + same event + same inputs_hash),
only one instance MUST be counted.

5) Metric Determinism

Given identical:

Event set

Window parameters

Configuration flags

The resulting:

health_score

quality_score

snapshot_grade

sustained cluster counts

MUST be identical across re-evaluations.

6) Snapshot Emission

Each window evaluation SHOULD emit:

event: GOV_HEALTH_SNAPSHOT

Fields:

window_start_utc

window_end_utc

health_score

quality_score

snapshot_grade

fail_closed_count

invariant_violation_count

override_hash_unsafe_count

sustained_cluster_count

This event is informational and MUST NOT affect Gate.

17. Intent

This model enforces strict FAIL-CLOSED governance symmetry,
while permitting controlled operational tuning through configuration flags.

Strategy is locked.
Observability is locked.
Health scoring operates above them without altering their contracts.