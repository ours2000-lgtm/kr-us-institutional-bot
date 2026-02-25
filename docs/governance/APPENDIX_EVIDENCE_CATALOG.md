APPENDIX — Evidence Catalog
Evidence Catalog Skeleton (Draft, NON-BINDING v0.x)
Purpose

This catalog enumerates candidate evidence artifacts used to support admission criteria for future phases (Phase 4 and Phase 5).

It provides a traceable mapping between:

Admission Criteria (P4-, P5-)

Required Evidence Types

Emitting Systems

Responsible Owners

Verification Tools

Retention Expectations

Until explicitly promoted, this catalog is informative only and MUST NOT influence binding verdicts.

Column Semantics

Evidence ID: Stable, immutable evidence handle (unique identifier).

Criterion ID: Single admission criterion this evidence supports.

Evidence Type: Logical class of evidence (log, manifest, proof, report, trace).

Source: System or subsystem emitting the evidence.

Owner: Role accountable for maintaining and validating this evidence.

Output Artifact: Concrete file, record, or dataset family.

Verification Tool: Primary mechanism validating integrity and correctness.

Retention: Minimum retention horizon (numeric or policy label).

Retention MAY be expressed as:

Numeric horizons (e.g., ≥ N decisions, ≥ N drills), or

Policy labels (LONG_TERM, REGULATORY_MIN, ARCHIVE_ONLY).

Governance Notes

Absence of required evidence is treated as absence of validity.

All Evidence Artifacts referenced here MUST be stored in an immutable or tamper-evident form.

Mutable evidence does not satisfy any Criterion.

Phase 5 evidence MUST consume or derive from Phase 4 output artifacts.

Deprecated evidence definitions remain archived for reproducibility.

Phase 4 — Audit & Verifiability
Evidence Skeleton (Draft)
Evidence ID	Criterion ID	Evidence Type	Source	Owner	Output Artifact	Verification Tool	Retention
E-P4-M1-01	P4-M1	Immutable Audit Log	Governance Engine	Audit Lead	AuditTrail.log	LogIntegrityVerifier	≥ N decisions
E-P4-M1-02	P4-M1	Merkle Root Snapshot	Audit Subsystem	Audit Lead	AuditMerkleRoot.json	MerkleVerifier	LONG_TERM
E-P4-M2-01	P4-M2	Evidence Corpus	Evidence Store	Compliance Team	EvidenceBundle.tar	EvidenceReconstructor	≥ N decisions
E-P4-M3-01	P4-M3	Reproducibility Report	Independent Verifier	Audit Lead	RecomputeReport.pdf	ResultComparator	≥ N audits
E-P4-M4-01	P4-M4	Rule Manifest	Policy Repository	Governance Maintainer	RulesManifest.yaml	ManifestHashChecker	ARCHIVE_ONLY
Phase 4 — NICE-TO-HAVE
Evidence ID	Criterion ID	Evidence Type	Source	Owner	Output Artifact	Verification Tool	Retention
E-P4-N1-01	P4-N1	Replay Trace	Shadow Engine	Audit Tooling Team	ReplayTrace.log	ReplayComparator	OPTIONAL
E-P4-N2-01	P4-N2	Formal Check Output	SMT Toolchain	Formal Methods Team	SMTReport.json	SolverVerifier	OPTIONAL
E-P4-N3-01	P4-N3	External Mapping Doc	Compliance Layer	Compliance Team	AuditMapping.pdf	DocHashChecker	ARCHIVE_ONLY
Phase 4 — DISQUALIFIERS
Evidence ID	Criterion ID	Evidence Type	Source	Owner	Output Artifact	Verification Tool	Retention
E-P4-D1-01	P4-D1	Opaqueness Report	Independent Verifier	Audit Lead	OpaquePathNotice.txt	ManualReview	ARCHIVE
E-P4-D2-01	P4-D2	Mutation Detection Log	Audit Monitor	Security Team	MutationAlert.log	IntegrityChecker	ARCHIVE
Phase 5 — Resilience & Recovery
Evidence Skeleton (Draft)
Evidence ID	Criterion ID	Evidence Type	Source	Owner	Output Artifact	Verification Tool	Retention
E-P5-M1-01	P5-M1	Recovery Determinism Report	Recovery Engine	Reliability Lead	RecoveryDiff.json	RecoveryComparator	≥ N recoveries
E-P5-M2-01	P5-M2	Fault Injection Trace	Fault Injector	Security Engineering	IsolationTrace.log	FaultContainmentChecker	≥ N drills
E-P5-M3-01	P5-M3	Safe-Harbor Transition Log	Resilience Engine	Reliability Lead	SafeHarbor.log	SafeHarborValidator	≥ N events
E-P5-M4-01	P5-M4	Data Preservation Proof	Evidence Store	Audit Lead	EvidenceSnapshot.hash	SnapshotVerifier	LONG_TERM
E-P5-M5-01	P5-M5	Recovery Rule Manifest	Policy Repository	Governance Maintainer	RecoveryRules.yaml	ManifestHashChecker	ARCHIVE_ONLY
Phase 5 — NICE-TO-HAVE
Evidence ID	Criterion ID	Evidence Type	Source	Owner	Output Artifact	Verification Tool	Retention
E-P5-N1-01	P5-N1	Resilience Replay Report	Shadow Engine	Reliability Tooling Team	ResilienceReplay.log	ReplayComparator	OPTIONAL
E-P5-N2-01	P5-N2	Stress Scenario Matrix	Test Harness	Reliability Lead	StressMatrix.csv	ScenarioValidator	OPTIONAL
Phase 5 — DISQUALIFIERS
Evidence ID	Criterion ID	Evidence Type	Source	Owner	Output Artifact	Verification Tool	Retention
E-P5-D1-01	P5-D1	Non-Determinism Alert	Independent Verifier	Audit Lead	DivergenceNotice.txt	ResultComparator	ARCHIVE
E-P5-D2-01	P5-D2	Invariant Bypass Log	Recovery Engine	Security Team	InvariantBypass.log	InvariantChecker	ARCHIVE
E-P5-D3-01	P5-D3	Evidence Integrity Failure Log	Audit Monitor	Audit Lead	IntegrityFailure.log	EvidenceHashChecker	ARCHIVE
E-P5-D4-01	P5-D4	Hidden Kill-Switch Report	Independent Verifier	Security Team	KillSwitchAlert.txt	ManualReview	ARCHIVE
Status

NON-BINDING — Draft Roadmap (v0.x)

This evidence catalog is exploratory and has no binding force.
It does not modify, weaken, or extend the README v1.0 Conceptual Contract unless explicitly promoted through a constitutional amendment.

Superseded drafts remain archived with hash-locked references for reproducibility.