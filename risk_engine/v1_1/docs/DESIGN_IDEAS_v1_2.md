# DESIGN_IDEAS_v1_2.md
# ACCOUNT + STRATEGY Pipeline — Design Ideas for v1.2+

> ⚠️ **IMPORTANT BOUNDARY NOTICE**  
> Any item that requires changing v1.1 tests MUST be modeled as a new contract (v1.2+),  
> not a patch or backport.  
> If v1.1 tests break, a version bump is mandatory.

This document collects **design ideas and expansion candidates** for  
ACCOUNT + STRATEGY Pipeline Contract v1.2 and later.

It intentionally contains **NO behavioral guarantees** and **NO executable tests**.  
All items here are **out of scope for v1.1** and MUST NOT be backported.

---

## 1. Purpose of This Document

- Preserve the integrity of **v1.1 FREEZE**
- Provide a **safe parking zone** for future ideas
- Prevent accidental behavioral drift
- Clearly separate:
  - what is constitutionally fixed (v1.1)
  - from what is intentionally deferred (v1.2+)

This document is **non-binding** and **exploratory**.

---

## 2. Strategy Evaluation Beyond ACCOUNT = ALLOW

### 2.1 Motivation

In v1.1:

- STRATEGY is evaluated **only** when `account_outcome == ALLOW`
- BLOCK / HARD_STOP states short-circuit immediately
- STRATEGY never participates in decision-making outside ALLOW

In v1.2, there may be value in evaluating STRATEGY  
for **diagnostic or advisory purposes** without affecting outcomes.

---

### 2.2 Strategy Evaluation Mode (Candidate)

Introduce an explicit evaluation mode:

```python
strategy_evaluation_mode: Literal[
    "DECISIVE",
    "ADVISORY",
    "DIAGNOSTIC",
] = "DECISIVE"
This field does not exist in v1.1 and MUST NOT be backported.

Mode Semantics
DECISIVE

May participate in final outcome selection

Subject to the non-weakening rule

Allowed only when account_outcome == ALLOW

ADVISORY

MUST NOT change final outcome

Outputs are explanatory only

Allowed in all ACCOUNT states

DIAGNOSTIC

MUST NOT affect outcome or source

For debugging / telemetry only

MUST NOT be visible to external consumers

2.3 ACCOUNT State × Strategy Mode Matrix (Conceptual)
ACCOUNT outcome	DECISIVE	ADVISORY	DIAGNOSTIC
ALLOW	✅	✅	✅
BLOCK	❌	✅	✅
HARD_STOP	❌	❌ (opt)	✅

In non-ALLOW states, STRATEGY MUST remain non-decisive.

3. Advisory Output Expansion
3.1 Advisory Fields (Candidate)
python
코드 복사
advisory_outcome: Optional[str]
advisory_reason: Optional[str]
advisory_confidence: Optional[float]  # 0.0 ~ 1.0
Used only in ADVISORY mode

Intended for UI, analytics, and ML interpretation

MUST NOT influence pipeline outcome

4. Diagnostic Mode & Non-Behavioral Tracing
4.1 Diagnostic Outputs
python
코드 복사
diagnostic_trace: List[str]
diagnostic_metadata: Dict[str, Any]
Captures evaluation path and internal signals

STRICTLY non-behavioral

No effect on outcome, source, or decision

5. Reason Code & Taxonomy Expansion
5.1 Enum-Based Reason Codes (Candidate)
python
코드 복사
from enum import Enum, auto

class ReasonCode(Enum):
    A_RISK_LIMIT = auto()
    A_ACCOUNT_INTEGRITY = auto()
    S_SIGNAL_CONFLICT = auto()
    F_PARSE_ERROR = auto()
5.2 Backward Compatibility Requirement
v1.2 MUST continue to emit v1.1-style string reasons
for external consumers, even if internal enums are introduced.

5.3 Reason Details Separation
python
코드 복사
reason: ReasonCode
reason_details: str  # human-readable explanation
6. Multiple Reasons & Evidence Sets
6.1 Evidence Set Structure
python
코드 복사
evidence_set: List[Dict[str, Any]]
# example:
# {"code": ReasonCode, "detail": str}
reason reflects primary evidence

Remaining items stored in evidence_set

7. Observability & Tracing (NON-BEHAVIORAL)
7.1 Trace Structure (Candidate)
python
코드 복사
trace = {
    "account_evaluated": bool,
    "strategy_evaluated": bool,
    "short_circuit": Optional[str],
    "evaluation_path": List[str],  # ["ACCOUNT", "STRATEGY"]
}
7.2 Audit Integration
python
코드 복사
audit_event_id: Optional[str]
Enables external compliance / audit linkage

MUST NOT affect runtime decisions

8. PipelineValidationResultV1_2 (Concept Sketch)
python
코드 복사
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

@dataclass(frozen=True)
class PipelineValidationResultV1_2:
    outcome: str
    source: Literal["ACCOUNT", "STRATEGY"]
    reason: ReasonCode
    reason_details: str
    trace: Dict[str, Any]

    advisory_outcome: Optional[str] = None
    advisory_reason: Optional[str] = None
    advisory_confidence: Optional[float] = None

    diagnostic_trace: Optional[List[str]] = None
    diagnostic_metadata: Optional[Dict[str, Any]] = None

    evidence_set: Optional[List[Dict[str, Any]]] = None
    audit_event_id: Optional[str] = None
9. Explicit Non-Goals for v1.2 Ideas
The following are NOT guaranteed by this document:

No behavioral changes are approved

No weakening of ACCOUNT decisions

No reinterpretation of v1.1 outcomes

No automatic promotion of advisory signals

No implicit fallback policies

All such changes require:

a new contract

new tests

explicit versioning

10. Closing Note
v1.1 is intentionally minimal, conservative, and fail-closed.

This document exists to ensure that future expansion
does not accidentally erode that foundation.

END OF DESIGN_IDEAS_v1_2.md