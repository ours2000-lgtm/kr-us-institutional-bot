VALIDATOR_LOADING_CONTRACT_v1.3

status: draft
owner: Governance Council
last_updated: 2026-02-20

depends_on:

SPEC_DEPENDENCY_GRAPH_v1.2

EVIDENCE_SCHEMA_LIFECYCLE_POLICY_v1.2.1

EVIDENCE_SCHEMA_REGISTRY_DESIGN_v1

1. Purpose

Defines deterministic loading, validation, compatibility resolution,
and integrity enforcement behavior of validators.

2. Authority Model

Validator decisions are authoritative.

Control Plane MUST treat outcomes as final.

3. Validation Priority

Validators MUST evaluate in order:

Integrity

Lifecycle state

Mode permission

Dependency validation

Version compatibility

Failure MUST terminate evaluation.

4. Integrity Verification

Validator MUST verify:

file hash matches registry

registry_root_hash alignment

ledger hash chain

ledger schema compliance

unique event_id

Integrity failure MUST reject.

5. Lifecycle Validation

revoked or quarantined MUST reject.

6. Mode Matrix

production → active
simulation → draft | active | frozen | deprecated
replay → active | frozen | deprecated

7. Dependency Validation

Must follow SPEC_DEPENDENCY_GRAPH_v1.2.

Hard dependency not active/frozen MUST reject.

Circular dependencies MUST reject.

8. Version Binding

Supports:

exact

compatible (^)

major range

Mismatch MUST reject.

9. Compatibility Result

resolve_compat returns:

accept | accept_readonly | migrate_required | reject

10. Active Resolution

resolve_active(schema_name, mode)

11. Version Resolution

resolve_by_version

12. Status Resolution

resolve_status

13. Supported Versions

list_supported

14. Root Hash Sync

expected_registry_root_hash supported.

Mismatch MUST reject.

15. Partial Bundle Detection

transaction_id mismatch MUST reject.

16. Quarantine Handling

Must verify reason_code and incident_ref.

17. Rollback Handling

Must verify target, reason, approvals.

18. Anchoring Verification

Must verify:

anchor_source

anchor_proof_ref

anchor_timestamp

anchor_proof_algorithm

19. Cache Validity

Cache valid only if hash, state, root match.

Mismatch MUST invalidate.

20. Evidence Emission

All outcomes MUST emit evidence including:

validator_contract_version

error_code

evidence_pointer

escalation_profile_id

Replay MUST emit replay evidence.

21. Observability

Should emit:

integrity_failure_count

quarantine_detected_count

rollback_detected_count

anchor_failure_count

cache_invalidation_count

dependency_drift_detected_count

council_override_detected_count

validation_latency

22. Council Override

Must verify approvals and roles.

Override does not bypass integrity rules.

23. Fail Closed

Uncertainty MUST fail.

24. Determinism

Given identical inputs results MUST match.

25. Non Goals

Validator does not modify lifecycle or registry.

26. Governance Authority

Changes require amendment.

27. Execution Sandbox

Validators MUST execute in a restricted side-effect-free environment.

Validators MUST NOT:

modify external state

perform network I/O

use randomness

depend on local clock

Validators MUST operate within resource limits.

Sandbox violations MUST fail validation.

End of Specification