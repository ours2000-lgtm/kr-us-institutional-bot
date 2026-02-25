Evidence Catalog — Full Table

NON-BINDING v0.x (Baseline)

Registered In: APPENDIX_INDEX.md — Constitutional Evidence Roadmap
Status: Draft / Non-Binding
Scope: Phase 4 (Audit & Verifiability) & Phase 5 (Resilience & Recovery)
Role: Canonical definition of evidence semantics, attributes, and lifecycle
Last Updated: 2026-01-09
Maintainer: Constitutional Evidence WG

Purpose

This document defines the canonical semantics and attributes of evidence used to
support Phase 4 and Phase 5 admission criteria.

Admission logic is defined in A4 / A5.

Logical traceability is defined in RTM v0.x.

This catalog defines what evidence means, how it is validated, and how it evolves.

This catalog does not define admission decisions by itself.

Column Semantics
Column	Meaning
Evidence ID	Stable, unique identifier (E-*). MUST match RTM references exactly.
Criterion ID	Admission criterion supported (P4-* / P5-*).
Evidence Type	Logical class (log, report, proof, trace, manifest).
Input Dependency	Referenced Phase output, Evidence ID, or formal alias.
Output Artifact	Concrete artifact handle (A4-* / A5-*).
Verification Tool	Tool + version + hash used for validation.
Tool Determinism	Deterministic / Guarded / Non-deterministic.
Sync Point / Freshness	Snapshot timing, frequency, and expiry threshold.
Retention	Retention policy label.
State	Current evidence lifecycle state.
Role	Accountable role for maintaining evidence validity.
ID Conventions

Evidence ID: E-<Phase>-<Criterion>-<Index>

Example: E-P4-M1-01

Criterion ID: P4-* / P5-*

Corresponds to Phase 4/5 criteria defined in A4/A5

Artifact Ref:

MUST include phase prefix + descriptor + date/version

Example: A4-LOG-2026-01

Rule: Evidence IDs MUST NOT be reused across phases.

Artifact Alias Mapping Rule

Artifact references are symbolic identifiers, not storage locations.

Artifact aliases MUST be mapped 1:1 to concrete storage URIs or hash-addressed locations
(e.g., Git SHA, S3 URI, on-chain hash) via operational configuration.

Evidence State Definitions
State	Definition
Draft	Structure defined; semantics under refinement; NOT admission-eligible
Verified	Passed automated or formal verification
Attested	Confirmed by human reviewer or external auditor
Stale	Freshness window expired; re-validation required
Deprecated	Superseded but retained for reproducibility

Rule: State transitions MUST be logged with timestamp, actor, and justification.

Tool Determinism Definitions
Level	Meaning
Deterministic	Same input ⇒ identical output hash
Guarded	Controlled variability with explicit guards
Non-deterministic	Output may vary per execution

Admission-critical evidence SHOULD use Deterministic or Guarded tools only.
Non-deterministic tools MUST NOT be the sole basis for admission decisions.

Verification Tool Metadata Standard (minimum):

Tool name

Tool version

Execution environment (OS / container image)

Library hash or image digest

Retention Policy Labels
Label	Minimum Expectation
LONG_TERM	≥ 5 years
REGULATORY_MIN	As required by regulation
ARCHIVE	≥ 10 years or permanent
Negative Evidence (D-series)

D-series criteria represent absence of violation.

Absence MUST still be recorded as explicit PASS evidence.

Null artifacts MAY be used.

Example:

E-P4-D1-NULL — Explicit record of no detected violation

D-series evidence SHOULD use ARCHIVE or stricter retention.

Phase Dependency Rule

Phase 5 evidence MUST reference Phase 4 output artifacts as inputs.

Input dependencies are recorded here, not in RTM.

Evidence Entries — Phase 4 (Audit)
Evidence ID	Criterion ID	Evidence Type	Input Dependency	Output Artifact	Verification Tool	Determinism	Freshness	Retention	State	Role
E-P4-M1-01	P4-M1	Audit Log Snapshot	ALIAS:P4_ALL_EVENTS	A4-LOG-2026-01	LogIntegrityVerifier:v2.1@sha256:…	Deterministic	Event-driven (Immediate)	LONG_TERM	Draft	SecOps
E-P4-M2-01	P4-M2	Evidence Coverage Report	ALIAS:P4_ALL_EVIDENCE	A4-COVERAGE-2026-01	CoverageAnalyzer:v1.3@sha256:…	Deterministic	Daily (≤25h)	LONG_TERM	Draft	Audit
E-P4-M3-01	P4-M3	Reproducibility Attestation	E-P4-M1-01	A4-REPRO-2026-01	ReplayComparator:v1.0@sha256:…	Deterministic	On-demand	LONG_TERM	Draft	Independent Verifier
E-P4-D1-NULL	P4-D1	Null Violation Record	ALIAS:P4_ALL_EVIDENCE	A4-NO-OPAQUE-2026-01	IntegrityScanner:v3.0@sha256:…	Deterministic	Continuous	ARCHIVE	Draft	Security Audit
Evidence Entries — Phase 5 (Resilience)
Evidence ID	Criterion ID	Evidence Type	Input Dependency	Output Artifact	Verification Tool	Determinism	Freshness	Retention	State	Role
E-P5-M1-01	P5-M1	Recovery Replay Trace	A4-LOG-2026-01	A5-RECOVERY-2026-01	RecoveryComparator:v1.2@sha256:…	Deterministic	Event-driven	REGULATORY_MIN	Draft	Reliability
E-P5-M3-01	P5-M3	Invariant Preservation Report	A4-REPRO-2026-01	A5-INVARIANT-2026-01	InvariantValidator:v2.0@sha256:…	Deterministic	On-demand	REGULATORY_MIN	Draft	Reliability
E-P5-D3-01	P5-D3	Evidence Integrity Failure Log	ALIAS:P4P5_ALL_ARTIFACTS	A5-INTEGRITY-FAIL-2026-01	EvidenceHashChecker:v1.1@sha256:…	Deterministic	Continuous	ARCHIVE	Draft	Audit
Governance Notes

Evidence IDs MUST match RTM references exactly.

Evidence Catalog attributes are immutable once defined; extensions require promotion.

Evidence in Draft state is NOT admission-eligible.

Evidence Catalog versions and status are registered in APPENDIX_INDEX.md.

Superseded catalog versions MUST remain referenced for ≥1 minor version.

Evidence exceeding freshness thresholds MUST transition to Stale automatically.

This catalog defines semantics; RTM defines relationships only.