DECISION REASON CODE TAXONOMY

Version: v1.2 (Constitution)

0. Purpose

This document defines the constitutional taxonomy for decision reason codes.

It specifies:

Canonical terminal outcomes

The minimum invariant classification of reason codes

The boundary between binding Constitution and non-binding Backlog

This taxonomy is intended to be used consistently across:

State machines

APIs

Storage schemas

Logs and metrics

Automated tests

1. Scope

This document applies to canonical terminal outcomes:

EXECUTED

REJECTED

FAILED

and defines the minimum invariant taxonomy for reason codes associated with those outcomes.

Interpretation of MUST / MUST NOT / MAY / SHOULD follows the constitutional semantics defined in Section A.

This document defines classification and invariants only.
It does NOT define:

Execution strategies

Retry algorithms

Monitoring thresholds

Alerting behavior

Those concerns are addressed in implementation guides or future versions (v1.3+).

Part I. Constitution (v1.2 — Binding)

Reason codes defined in this section are binding.

They:

MUST be represented in code (e.g., enums)

MUST be enforced by automated tests

Define stable API and observability contracts

2. Canonical Reason Codes
2.1 EXECUTED
terminal_state	reason_category	reason_code	is_edge_case	Notes
EXECUTED	BUSINESS	EXECUTED.OK	false	Canonical successful execution
2.2 REJECTED
terminal_state	reason_category	reason_code	is_edge_case	Notes
REJECTED	VALIDATION	REJECTED.VALIDATION_FAILED	false	Input or schema validation failed
REJECTED	RISK	REJECTED.RISK_LIMIT	false	Risk or exposure limit breached
REJECTED	POLICY	REJECTED.POLICY_RULE	false	Explicit policy rule rejection
REJECTED	POLICY	REJECTED.POLICY_GENERIC	true	Absorber for rare or uncategorized policy rejections
2.3 FAILED
terminal_state	reason_category	reason_code	is_edge_case	Notes
FAILED	SYSTEM	FAILED.SYSTEM_ERROR	false	Internal system error
FAILED	INFRA	FAILED.INFRA_UNAVAILABLE	false	Infrastructure unavailable
FAILED	DEPENDENCY	FAILED.DEPENDENCY_TIMEOUT	false	External dependency timeout
FAILED	DATA	FAILED.DATA_INTEGRITY	false	Data corruption or integrity failure
FAILED	UNKNOWN	FAILED.UNKNOWN	true	Absorber for unknown or unexpected failures
2.4 Edge Case Definition

is_edge_case = false
→ Canonical, deterministic reason code

is_edge_case = true
→ Absorber or unknown bucket
→ SHOULD be rare
→ SHOULD be monitored and reduced over time

3. Relationship to Code

Only Constitution reason codes MUST appear in enums.

All Constitution invariants MUST be enforced by automated tests.

Logs and metrics MUST clearly distinguish Constitution codes from Backlog codes.

4. Testability Clause

All MUST and MUST NOT invariants defined by this document
MUST be enforced by automated tests
(at one or more appropriate levels: unit, integration, or contract).

MAY and SHOULD rules:

Are not required for canonical correctness validation

MAY be validated by non-blocking or advisory tests

MUST remain observable via logs and/or metrics

Part II. Backlog (v1.3+ — Non-binding Candidates)

Reason codes in this section are NOT binding.

They:

MUST NOT appear in enums

MUST NOT be treated as stable API contracts

MAY appear in logs or metrics for observation only

Backlog entries are promotion candidates, not exclusions.

5. Backlog Reason Code Candidates
5.1 EXECUTED
reason_code	Rationale	Notes
EXECUTED.PARTIAL	Partial success semantics	Depends on lifecycle model
EXECUTED.ASYNC_CONFIRMED	Async confirmation pattern	Requires async execution model
5.2 REJECTED
reason_code	Rationale	Notes
REJECTED.AUTHORIZATION_FAILED	Permission or auth failure	Overlaps with policy layer
REJECTED.DATA_CONFLICT	Data-level conflict	Requires concurrency model
5.3 FAILED
reason_code	Rationale	Notes
FAILED.CONFIGURATION_ERROR	Environment misconfiguration	Infra vs config boundary
FAILED.SECURITY_EXCEPTION	Security-related failure	Requires security model
6. Promotion Rules

A Backlog reason code MAY be promoted to Constitution when:

Its classification is stable and unambiguous

Tests and invariants can be clearly defined

At least one documented validation scenario exists

Promotion does not weaken existing Constitution invariants

Promotion requires an explicit versioned update (v1.3+).

7. Summary

Constitution defines the minimum invariant taxonomy (binding)

Backlog captures observed or anticipated extensions (non-binding)

Enums reflect Constitution only

Tests enforce Constitution invariants

Logs and metrics MAY observe Backlog candidates, but MUST distinguish them​