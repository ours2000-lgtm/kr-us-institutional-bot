# EVIDENCE_JSON_SPEC_v1_1_AMENDMENT_SCOPE.md

Status: AMENDMENT SCOPE DEFINITION
Target Amendment Version: REV.1.1
Parent Specification: EVIDENCE_JSON_SPEC_v1.md REV.1.0-FINAL

---

## 1. Purpose of REV.1.1 Amendment

REV.1.1 SHALL introduce strengthening, operational expansion, and governance telemetry enhancements to the Evidence contract while preserving REV.1.0 constitutional guarantees.

REV.1.1 SHALL NOT weaken any safety, immutability, provenance, or FAIL-CLOSED requirements established in REV.1.0-FINAL.

---

## 2. Amendment Design Principles

REV.1.1 SHALL:

* Strengthen cryptographic governance
* Expand validator audit traceability
* Improve operational recovery telemetry
* Enhance retention and security classification governance
* Strengthen provenance graph integrity

REV.1.1 SHALL remain backward compatible with REV.1.0 Evidence objects.

---

## 3. Cryptographic Governance Expansion

REV.1.1 SHALL introduce:

### 3.1 AllowedHashAlgorithms Governance Set

Defines accepted hashing algorithms, including but not limited to:

* SHA-256
* SHA-512
* BLAKE3

Algorithm acceptance SHALL be governed by Cryptographic Policy Annex.

---

### 3.2 Signature Governance Enhancements

REV.1.1 SHALL define:

* Minimum signature algorithm strength requirements
* auditor_certificate_ref support for PKI trust anchoring
* Cryptographic policy linkage requirements

---

## 4. Validation Telemetry Expansion

REV.1.1 SHALL introduce:

### 4.1 validation_details

Structured validator execution trace data supporting:

* Step-level validation outcomes
* Failure cause classification
* Validator diagnostic telemetry

---

## 5. Provenance Graph Strengthening

REV.1.1 SHALL extend Evidence relationship modeling with:

### 5.1 relationship_strength

Example classifications:

* STRONG
* WEAK
* INDIRECT

---

### 5.2 Provenance Cycle Enforcement

Evidence parent or linked relationship chains SHALL enforce Directed Acyclic Graph integrity.

Validators SHALL detect and reject cycle formations.

---

## 6. Payload Externalization Integrity

REV.1.1 SHALL introduce:

* payload_hash for externalized payload integrity verification
* External payload referencing governance rules

---

## 7. Recovery Telemetry Expansion

REV.1.1 SHALL introduce:

* recovery_attempted boolean telemetry
* Standardized recovery_action_class enumeration

Examples include:

* RESET
* RETRY
* ISOLATE
* ALERT

---

## 8. Retention Governance Extension

REV.1.1 SHALL introduce:

* retention_policy_ref linking to Canonical Operations Contract
* Enhanced retention lifecycle metadata

---

## 9. Security Classification Governance

REV.1.1 SHALL enhance:

* classification_level enforcement integration
* Multi-tier security classification interoperability
* Access governance integration with platform enforcement layers

---

## 10. LIVE Environment Safety Hardening

REV.1.1 SHALL introduce:

* Mandatory safety verification sets for LIVE Evidence generation
* Enhanced validation enforcement requirements for production Evidence

---

## 11. Amendment Impact and Compatibility Requirements

REV.1.1 SHALL:

* Preserve REV.1.0 Evidence compatibility
* Maintain FAIL-CLOSED guarantees
* Avoid modification of REV.1.0 mandatory Evidence semantics

---

## 12. Amendment Evaluation Criteria

REV.1.1 SHALL be considered constitutionally valid only if:

* Safety guarantees remain intact
* Evidence immutability remains unchanged
* Provenance reconstruction remains possible
* Validator backward compatibility remains functional

---

## 13. Future Amendment Evolution Path

REV.1.1 SHALL establish governance patterns enabling:

* REV.1.x operational telemetry enhancements
* REV.2.x architectural Evidence model evolution

---

END OF AMENDMENT SCOPE
