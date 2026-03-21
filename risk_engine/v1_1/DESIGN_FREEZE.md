## ACCOUNT v1.1 — DESIGN FREEZE

This freeze ensures long-term behavioral stability and provides a reliable
foundation for multi-layer risk orchestration.

ACCOUNT v1.1 is hereby **officially frozen** as a long-term immutable contract.

In this document, the term **“behavioral change” always implies a breaking change
to the external contract**.

At this stage:
- All ACCOUNT v1.1 tests are GREEN.
- Enum definitions, validator logic, and test expectations are fully aligned.
- ACCOUNT v1.1 serves as the **top-level risk authority** and an upper bound
  for all downstream layers (STRATEGY, ORDER).

### Domain Rationale

ACCOUNT-level decisions represent the final safety boundary of the system.
They must therefore remain **deterministic, explicit, and fully inspectable**.

Downstream layers may add stricter rules but may **never relax or override**
ACCOUNT-level outcomes.

### FAIL_CLOSED Modeling Note

`FAIL_CLOSED` is modeled as an **explicit enum value** in both
`SystemHealthGrade` and `SnapshotQualityGrade`.

This reflects the authoritative nature of ACCOUNT-level decisions and ensures
strict FAIL-CLOSED behavior is enforced via the type system.

Example of a behavioral (breaking) change:
- Changing FAIL_CLOSED resolution from HARD_STOP to BLOCK

Future versions (v1.2+) may refactor FAIL_CLOSED handling into
policy-level or orchestration logic **if system health modeling evolves**.

#### Change Process (RFC Required)

All proposed changes to ACCOUNT v1.1 behavior MUST be reviewed via a
**dedicated design RFC** before any implementation work begins.

An RFC MUST include:
- Motivation and problem statement
- Proposed behavioral change
- Impact analysis on downstream layers
- Updated truth table and test cases

### Scope of Freeze

The following elements are **frozen** and MUST NOT change in v1.1:

- Public enums and their values
- ACCOUNT truth table and decision outcomes
- Validation rules and authoritative logic
- Input/output contract shapes
- Test expectations and behavioral assertions

The following elements are **not frozen**:

- Internal refactoring without behavioral impact
- Logging, metrics, or instrumentation
- Performance optimizations without semantic change

### Truth Table Invariance

The ACCOUNT v1.1 truth table is immutable.
See **Scope of Freeze** for the definitive list of frozen elements.

Examples of breaking changes:
- Changing ALLOW → BLOCK for an existing grade combination
- Adding a new grade combination without a version bump

### Backward Compatibility

All downstream layers (STRATEGY, ORDER) MUST remain backward-compatible
with ACCOUNT v1.1.

Any incompatibility requires a **coordinated version bump across layers**.

### Versioning Philosophy

- Patch versions (v1.1.x):
  - Internal fixes without behavioral change

- Minor versions (v1.2):
  - Behavioral changes requiring test updates

- Major versions (v2.0):
  - Contract redesign or structural changes

In practice:
Any change that requires downstream code changes MUST be
at least a **minor version bump**.

### Freeze Duration and Exit Criteria

ACCOUNT v1.1 remains frozen until explicitly superseded by ACCOUNT v1.2 or higher.

Unfreeze requires:
- A new version proposal (v1.2+)
- Updated truth table
- Updated test suite
- Approval via the design RFC process
