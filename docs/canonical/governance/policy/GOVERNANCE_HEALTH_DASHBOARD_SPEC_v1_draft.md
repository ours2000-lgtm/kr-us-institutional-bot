# 📜 GOVERNANCE_HEALTH_DASHBOARD_SPEC_v1

Layer: CANONICAL_POLICY  
Status: DRAFT  

---

## Purpose

Governance 상태 시각화 지표 모델 정의.

---

## Access Control (Normative)

Dashboard MUST be accessible ONLY to:

- Governance Council
- Authorized Auditors

---

## Dashboard Domains

Governance Risk  
Spec Maturity  
Validation Status  
Authority Trust  
Evidence Integrity  

---

## Core Metrics

### Risk Metrics

RiskScore  
HealthScore  
RiskLevel  

AuthorityDomainScore  
LedgerDomainScore  
DelegationDomainScore  
ApprovalDomainScore  
EvidenceDomainScore  
OperationalDomainScore  

---

## Spec Metrics

total_specs  
draft_specs  
reviewed_specs  
verified_specs  
locked_specs  

---

## Validation Metrics

validation_pass_rate  
failed_spec_count  

---

## Authority Metrics

active_authorities  
revoked_authorities  
key_rotation_events  
delegation_count  

---

## Evidence Metrics

ledger_head_hash  
ledger_integrity_status  
evidence_gap_count  

evidence_set_hash  
last_evidence_timestamp  

---

## Trend Tracking

Dashboard MUST maintain history of last N evaluations.

Metrics SHOULD include:

risk_trend  
health_trend  
validation_trend  

---

## Alert Severity Levels

INFO  
WARNING  
CRITICAL  

---

## Alert Rules

CRITICAL when:

RiskLevel ≥ HIGH  
ledger integrity compromised  
registry mismatch  

---

## Refresh Policy

Dashboard MUST refresh on:

LOCK declaration  
SUPERLOCK approval  
Authority key change  
Risk evaluation  

---

## Data Sources

Risk Model  
Ledger  
Registry  
Validation results  
Delegation state  

---

## Failure Semantics

DASHBOARD_DATA_UNAVAILABLE  
INVALID_METRIC_SOURCE  
STALE_DATA  
ALERT_DISPATCH_FAILED  
TREND_COMPUTE_ERROR  

FAIL_CLOSED display fallback.

---

## Status

DRAFT
