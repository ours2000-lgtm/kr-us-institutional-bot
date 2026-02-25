Phase 5 — Governance Map (1-Page Canonical Text) v2

Status: CANONICAL MAP / NON-BINDING

Subtitle
Admission에 실제로 사용되는 Evidence, Freshness, Deprecation, 상태 판단을
하나의 위계·우선순위·권한 경계로 묶은 헌법적 거버넌스 지도 (Phase 4–5)

Scope & Purpose

This document provides a governance-level map only.

Applies to Phase 4–5 Admission decisions, A4/A5 criteria, RTM, Evidence Catalog

Defines authority boundaries, precedence, and invariants

Does NOT define implementation details, algorithms, SLAs, performance guarantees

This map exists to ensure that all policies and engines remain aligned, auditable,
and reproducible under a single constitutional hierarchy.

I. Constitutional Layer (FROZEN)
Phase 5 Core Policy Bundle

Status: FROZEN / CONSTITUTIONAL

Defines non-overridable invariants that apply to all Phase 4–5 artifacts and decisions.

Core invariants include:

Fail-Closed dominates availability

Revocation is permanent and admission-blocking

Most Restrictive Signal Wins

Auditability and reproducibility are mandatory

No dashboard, override, or operational shortcut may weaken these invariants.

II. Normative Policy Layers (HARDENED / NON-BINDING)
Freshness Policy

Defines the meaning of freshness states, not how they are computed.

GREEN: within freshness window; admission eligible

YELLOW: warning state
→ admission MAY proceed with explicit risk acceptance and enhanced monitoring

RED: freshness violation; admission-ineligible

UNKNOWN: observability or governance gap (not safety)
→ admission-critical scopes SHOULD treat UNKNOWN as conservatively as RED

UNKNOWN conditions are cause-aware (e.g., data gap, observer failure, governance gap).

Deprecation Policy

Defines lifecycle meaning and admission impact.

Deprecated: operationally superseded
→ new admissions discouraged; grace MAY exist if policy allows

Revoked: permanently invalid
→ no grace, no admission, regardless of freshness

Revocation always takes precedence over freshness evaluation.

III. Operational Engine Specifications (REFINED / NON-BINDING)
Freshness Engine

Executes freshness evaluation strictly per policy semantics.

Computes freshness states

Emits WARN / BLOCK signals

Must not reinterpret policy meaning

Thresholds, hysteresis, and tuning are configuration, not policy

Consumes Deprecation / Revocation signals.

Deprecation Engine

Executes lifecycle transitions and revocation propagation.

Emits lifecycle and revocation signals

Revocation signals are authoritative and irreversible

IV. Cross-Layer Interaction & Precedence
Evaluation & Enforcement Order

Revocation

Freshness state

Deprecation state

Admission decision

Revocation signals MUST be evaluated and enforced before freshness results are considered.

Priority Rule — Most Restrictive Wins
Priority	State / Signal
1	Revoked
2	Freshness RED
3	Freshness UNKNOWN
4	Deprecated
5	Freshness YELLOW
6	GREEN

Example: Revoked + GREEN ⇒ BLOCK (Revoked wins)

V. Admission Evaluator

The Admission Evaluator is the final transaction-time decision authority.

Rules:

BLOCK or UNKNOWN MUST prevent admission

Revoked MUST always imply BLOCK

May reject engine outputs

May never weaken Core or Policy semantics

Emergency / Break-glass

Exists only if defined in Core Policy

Requires explicit approver identity and justification

Always audited and retroactively reviewed

Core Policy version MUST be recorded

VI. Audit, Reproducibility & Drift Control (All Layers Apply)

All layers MUST produce immutable (append-only) audit logs

Dual timeline required:

Valid Time (evidence reality)

Transaction Time (decision time)

Logs MUST include:
EvidenceID, State, Source Engine, Policy Version, Transaction Time

Reproducibility

Same events + same configuration ⇒ same outcome

Drift Monitoring

Drift between policy intent and engine behavior
MUST be observable and reportable
(e.g., governance dashboards, alerts, shadow evaluation).

VII. Governance Boundary Summary
Layer	Defines Meaning	Executes Logic	May Override
Core Policy	✅	❌	❌
Policy Layers	✅ (bounded by Core)	❌	❌
Engines	❌	✅	❌
Admission Evaluator	❌	✅	May reject outputs; NEVER weaken Core/Policy
Canonical Status

This document is the canonical governance map for Phase 5.

All Appendix entries, policy texts, and engine specifications
MUST align with this map and MUST NOT contradict its precedence rules.