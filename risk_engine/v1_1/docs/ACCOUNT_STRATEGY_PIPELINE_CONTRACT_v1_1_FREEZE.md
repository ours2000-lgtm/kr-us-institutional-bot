16. Freeze Declaration (v1.1)

This document, together with its corresponding test suite
(test_pipeline_account_strategy_v1_1.py), is hereby declared FROZEN
as the ACCOUNT + STRATEGY Pipeline Contract v1.1.

16.1 Scope of Freeze

The following elements are immutable in v1.1:

Entrypoint name and signature
run_account_strategy_pipeline(...)

Execution order and short-circuit semantics

ACCOUNT is always evaluated first

ACCOUNT outcomes HARD_STOP and BLOCK MUST short-circuit

STRATEGY MUST NOT be evaluated unless account_outcome == ALLOW

Outcome partial order and comparison rules
HARD_STOP ≻ BLOCK ≻ ALLOW

Outcome propagation rules (§6)

FAIL-CLOSED behavior and default resolution to HARD_STOP (§8)

Weakening prohibition semantics (§7), applicable only when ACCOUNT == ALLOW

Error model boundaries (ValueError vs AssertionError)

Result contract:

PipelineValidationResultV1_1

outcome, source, reason semantics

Clause ↔ Test mapping as encoded by P01–P08

Any behavior not explicitly guaranteed above is out of scope for v1.1.

16.2 Test Canonicality

The test suite P01–P08 is the canonical executable specification
of this contract.

All tests MUST pass for any implementation claiming v1.1 compliance.

Any change that causes a test to fail is, by definition,
a breaking behavioral change.

16.3 Prohibited Changes in v1.1

The following changes are explicitly forbidden in v1.1:

Evaluating STRATEGY when account_outcome != ALLOW

Introducing strategy validation, analysis, or error handling
in ACCOUNT BLOCK or HARD_STOP states

Weakening or relaxing ACCOUNT decisions under any circumstances

Adding new outcomes, reinterpretations, or fallback policies

Reclassifying FAIL-CLOSED behavior to anything other than HARD_STOP

Such changes require a new contract version (v1.2+).

16.4 Version Boundary Guarantee

v1.1 is intentionally minimal, conservative, and strictly fail-closed.

All future behavior expansions — including but not limited to:

STRATEGY evaluation in BLOCK states

Extended reason taxonomy

Observability, tracing, or audit semantics

Orchestrator-driven reinterpretation

MUST be designed and introduced in v1.2 or later,
with a new contract, new tests, and an explicit version bump.

16.5 Final Declaration

This contract is frozen.

Implementation may evolve,
refactoring is permitted,
performance optimizations are allowed,

but behavior is constitutionally fixed.

END OF v1.1 FREEZE