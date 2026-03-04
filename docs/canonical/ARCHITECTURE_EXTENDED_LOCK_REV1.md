📜 ARCHITECTURE_EXTENDED_LOCK_REV1.md

(최종 Canonical LOCK 완성본)

KR_US_INSTITUTIONAL_BOT
Extended Architecture — REV.1-LOCK
1. Scope

본 문서는 KR_US_INSTITUTIONAL_BOT 시스템의 구조적 진실(Structural Truth) 을 정의한다.

본 문서는 다음을 LOCK 한다:

Runtime Trading Stack 과 Governance Validator 역할 분리

Evidence Chain 기반 Audit-Grade 재현성

Fail-Closed 시스템 보장

V31 → V100 확장 시 불변 결합점 정의

구조 변경은 Amendment 절차 없이는 허용되지 않는다.

2. System Overview

KR_US_INSTITUTIONAL_BOT 는 5개 레이어 구조를 따른다.

3. Operator / OPS Layer
Runbooks / Checklists
docs/derivation/**

CLI Tools
validator_cli
rehearsal launcher

Viewer / Dashboard (Future)
Evidence Explorer
Risk Decision Feed

4. Locked Governance Layer
docs/canonical/**
docs/spec/**
docs/schemas/v1/**

Contract Rule
result.schema_set_ref MUST equal "docs/schemas/v1"

5. Runtime Trading Stack
Market Adapters

Kiwoom

US Broker APIs

Crypto Exchanges

Session / Regime

SessionDetector

Holiday / Timezone

Volatility classifier

Strategy Layer

Strategy Engine

Signal Builder

Portfolio Selector

RiskEngine (Fail-Closed Core)

Fail 발생 조건:

HARD_STOP
UNKNOWN
DEGRADED

Execution Layer

OMS

Router

Fill reconciliation

Observability
logs/**
snapshots/**
metrics/**
runtime traces/**

6. Governance Validation Pipeline
validate_bundle(bundle)
        ↓
write_validation_evidence(...)
        ↓
Evidence Artifact JSON

Validation Stages

Stage 1 — Schema Validation
(tools.governance_validator.schema_stage)

Stage 2 — Semantic Validation
(tools.governance_validator.semantic_stage)

Stage 3 — Cryptographic Annex
(tools.governance_validator.crypto_stage)

Stage 4 — Replay / Transition
(tools.governance_validator.replay_stage)

Stage → Evidence Mapping Rule

If Stage N fails:

summary.failed_stage MUST equal:
"SCHEMA" | "SEMANTIC" | "CRYPTO" | "REPLAY"

summary.fail_closed MUST be true

7. Evidence Artifact Contract
7.1 Top-Level Fields
evidence_type: str
evidence_version: str
created_at_utc: str
meta: object
inputs: object
summary: object
result: object
chain: object

7.2 Field Constraints
evidence_type
"GOV_VALIDATION_EVIDENCE"

evidence_version
"EVIDENCE_v1"

Schema Mapping Rule
EVIDENCE_v1 MUST map 1:1 to:
docs/schemas/v1/evidence_v1.json

created_at_utc
ISO 8601
UTC Z-normalized

meta
meta.created_at_utc: str
meta.node_id: str (optional)
meta.git_commit: str (optional)

inputs
bundle_path: POSIX string
bundle_sha256: 64-char hex SHA-256

summary
decision:
ALLOW | FAIL_CLOSED | DENY | UNKNOWN

fail_closed: bool

failed_stage:
"NONE" | "SCHEMA" | "SEMANTIC" | "CRYPTO" | "REPLAY"

violations_count: int >= 0

result

Serialized ValidationResult.

result.schema_set_ref MUST equal "docs/schemas/v1"

chain
prev_hash:
"GENESIS" OR 64-character hex string

this_hash:
64-character hex string

7.3 Hash Rule — LOCK
Canonicalization Contract

During hashing:

chain.this_hash MUST be null (Python None)

Canonical JSON Rules
ensure_ascii = false
sort_keys = true
separators = (",", ":")
UTF-8 encoding

Formal Definition
hash_input = canonical_json(payload with chain.this_hash = null)
chain.this_hash = sha256(hash_input).hexdigest()

LOCK Declaration
null vs "" is contract-significant.
Change requires Amendment + tests update.

8. Runtime → Governance Binding
Strategy
   ↓
RiskEngine
   ↓
Decision + reason_code
   ↓
TraceBundle Emission
   ↓
validate_bundle
   ↓
write_validation_evidence
   ↓
Evidence Artifact

TraceBundle Definition

TraceBundle MUST be:

JSON object containing at minimum:

decision
reason_code
invariant flags
all inputs required to reconstruct ValidationResult


TraceBundles are stored under:

runtime traces/**
tests/fixtures/traces/**

Mandatory Evidence Emission Rule — LOCK

Evidence MUST be emitted for BOTH:

ALLOW
BLOCK


Absence of evidence implies:

FAIL-CLOSED

Scope

Applies to:

LIVE trading sessions


Non-live environments MAY opt out but cannot be audit evidence.

9. Responsibility Separation

Runtime Stack:

Trading Decisions


Governance Validator:

Compliance validation
Evidence generation
Audit reproducibility

10. CI Enforcement — LOCK
ANY contract violation MUST fail CI

Amendment Rule

Evidence contract 변경 시:

Governance Amendment 필요

Contract tests 동시 수정 필요

Examples:

tests/test_evidence_writer*.py
tests/test_governance_validator.py

11. Evolution Roadmap
V31-V40

Evidence Chain LOCK

Runtime Trace emitter 연결

reason_code 표준화

V50-V80

Multi-signature verification

Key rotation governance

Evidence index system

V100

Full audit reproducibility

Evidence-driven operations

Exchange-grade governance

12. Governance LOCK Declaration

본 문서는 다음을 LOCK 한다:

Evidence Artifact Contract

Hash Chain Rule

Runtime Binding Point

Evidence Emission Fail-Closed Policy

구조 변경은 Amendment 절차 없이는 금지된다.

END OF DOCUMENT

REV.1-LOCK