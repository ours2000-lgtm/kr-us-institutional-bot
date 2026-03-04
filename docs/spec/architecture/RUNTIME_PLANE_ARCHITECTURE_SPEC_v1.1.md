1. 다중 런타임 합의 (Multi‑Runtime Attestation)
새 섹션 28. Multi‑Runtime Attestation
text
For high‑criticality instructions, the Control Plane MAY require Multi‑Runtime Attestation:

- The same instruction and authoritative state snapshot MUST be executed on M diverse Runtime nodes (e.g. different implementations or platforms).
- At least N of M (N ≤ M) MUST produce identical resulting state hashes and execution outcomes.
- If required quorum (N) is not reached, the instruction MUST be treated as failed, execution MUST halt, and integrity_failure evidence MUST be emitted.

Multi‑Runtime Attestation is intended to mitigate implementation‑specific bugs or platform anomalies.
2. 봉인된 상태 기록 (WAL · Dirty State 복구)
8. Execution Atomicity · 10. Dirty State Recovery 보강
text
Runtime MUST utilize Write‑Ahead Logging (WAL) for all state transitions:

- Each WAL entry MUST be linked to transaction_id and execution_id,
- MUST be durably written before applying state changes,
- and MUST be signed or attested by the Runtime identity.

On startup or recovery, Runtime MUST:

- inspect WAL entries,
- reconcile them with Evidence and Ledger records,
- and determine which executions reached commit vs. which must be rolled back,
- ensuring consistency with Last Known Good State (LKGS).
이걸로 “외부 / 내부 상태는 바뀌었는데 Evidence/Ledger 전에 죽었다” 상황을 복구할 수 있다.

3. Runtime Health & Attested Heartbeat
22. Observability 보강
text
Runtime MUST emit periodic attested heartbeats including at least:

- runtime_version,
- resource_utilization summary (CPU, memory, IO, network, storage),
- last_processed_event_hash or last_committed_execution_id,
- health_status (e.g. healthy, degraded, read‑only).

Heartbeats MUST be signed or otherwise attested so the Control Plane can trust their origin, and MUST be recorded as Observability or health Evidence.
4. Execution Evidence 필드 확장
14. Evidence Emission 보강
text
Execution Evidence MUST include:

- execution_id,
- transaction_id,
- runtime_context_id,
- ledger_event_id (once recorded),
- failure_domain_id (for failures).

These identifiers MUST enable bidirectional tracing between Runtime executions, Control Plane transactions, Evidence, Ledger events, and failure domains.
5. Replay Evidence 확장
21. Replay Execution 보강
text
Replay MUST emit replay_evidence including:

- event_replay_id,
- original_event_hash,
- replay_result ∈ {equal, drift, mismatch},
- replay_reason_code (e.g. dependency_drift, anchoring_failure, resource_exhaustion),
- replay_comparison_basis (e.g. decision_outcome_only, full_state, full_context).

Replay mismatch (drift or mismatch) MUST automatically emit integrity_failure evidence and escalation_evidence, and MUST NOT modify production state.
6. Resource Limits 세분화
16. Resource Determinism 보강
text
Runtime MUST enforce logical cost limits (e.g. gas/credits) and explicit resource limits on:

- cpu_limits,
- memory_limits,
- execution_time_limits,
- io_limits,
- network_limits,
- storage_limits,
- concurrency_limits (e.g. max concurrent executions per domain).

Resource breaches in any category MUST:

- terminate or throttle affected executions safely,
- emit Incident Evidence with appropriate failure_reason_code and resource type.
7. Backpressure 이벤트 필드 확장
18. Backpressure 보강
text
Backpressure events MUST include:

- backpressure_reason_code (e.g. queue_saturation, resource_limits_near, upstream_slow),
- mitigation_action (e.g. delay, reject_new, shed_load, request_throttling),
- backpressure_severity ∈ {critical, high, medium, low},
- backpressure_timestamp.

Backpressure events MUST be emitted as Evidence for audit and capacity planning.
8. Execution Isolation 정책 참조
11. Execution Isolation 보강
text
Each execution MUST include:

- isolation_domain_id,
- isolation_policy_ref (identifying the policy governing isolation for that domain).

Any observed violation of isolation_policy_ref (e.g. cross‑domain state or side‑effect leakage) MUST be treated as an integrity failure and MUST emit integrity_failure evidence.
9. Observability Signals 확장
22. Observability 보강
text
Runtime SHOULD emit, at minimum, signals for:

- execution_success_count,
- execution_failure_count (by failure_reason_code),
- execution_latency_distribution,
- execution_retry_count,
- resource_exhaustion_count,
- backpressure_event_count,
- snapshot_mismatch_count,
- rollback_execution_count,
- isolation_breach_detected_count.
10. Failure Domain Evidence 세분화
24. Failure Domains 보강
text
Failure Evidence MUST include:

- failure_domain_id,
- failure_severity ∈ {critical, high, medium, low},
- failure_timestamp,
- containment_action (e.g. isolate_domain, restart_runtime_instance, drain_traffic).

Failures MUST be contained within their failure_domain and MUST NOT corrupt upstream or cross‑domain state.
11. Snapshot Evidence 확장
20. Snapshot Handling 보강
text
Snapshot Evidence MUST include:

- snapshot_id,
- snapshot_hash,
- snapshot_timestamp,
- snapshot_source (e.g. control_plane, registry, runtime),
- covered_range (e.g. state version or event interval),
- snapshot_anchor_id (link to anchoring evidence, where applicable),
- snapshot_validation_result ∈ {valid, mismatch, partial}.

Snapshot mismatches (e.g. snapshot_hash differing from authoritative source or anchor) MUST emit integrity_failure evidence and block usage of the invalid snapshot.