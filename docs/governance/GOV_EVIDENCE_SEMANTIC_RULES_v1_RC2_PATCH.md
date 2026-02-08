# GOV_EVIDENCE_SEMANTIC_RULES_v1_RC2_PATCH.md
Status: RC2 PATCH (NORMATIVE DELTA)
Revision: v1.0-RC2-PATCH
Authority Tier: GOVERNANCE / SEMANTIC RULESET
Parent Baseline: GOV_EVIDENCE_SEMANTIC_RULES_v1.md
Default Semantics: FAIL-CLOSED

This RC2 patch aligns signature field naming with the Evidence Core Schema vocabulary and makes Evidence linkage field names explicit for replay- and audit-safe validation.

This patch SHALL NOT introduce new decision semantics beyond clarifying the binding required by the Parent Baseline.

---

## 1. Field Vocabulary Alignment (Signature)

### 1.1 Canonical Signature Field Names

All Semantic Rules that reference signature material SHALL use the canonical field names defined by the Evidence Core Schema:

- signature.sig_alg
- signature.signer_id
- signature.key_ref
- signature.value

Alias or equivalent naming SHALL NOT be accepted for canonical validation.

---

## 2. Evidence Linkage Field Naming (Explicit Anchors)

### 2.1 Ratification Evidence Linkage

Where Governance Ratification Evidence links to underlying Evidence bundles, the following fields SHALL be treated as canonical linkage anchors:

- payload.evidence_refs (array): references to Evidence records required for ratification replay
- payload.evidence_pack_ref (string): optional reference to an evidence pack artifact (if used)

Any Semantic Rule that requires evidence linkage SHALL interpret linkage exclusively through these fields when present.

---

## 3. GSR Clarifications (Targeted)

### 3.1 GSR-030 / GSR-031 Linkage Clarification

GSR-030 and GSR-031 SHALL evaluate linkage completeness using:

- payload.evidence_refs
- payload.evidence_pack_ref (if applicable)

If required evidence linkage cannot be established, validators SHALL treat the Evidence as INVALID and SHALL apply FAIL-CLOSED handling for canonical decisions.

---

### 3.2 GSR-051 Signature Verification Capability (Vocabulary Binding)

GSR-051 SHALL require that Evidence carries sufficient signature material for independent verification under the Cryptographic Policy Annex.

At minimum, Evidence SHALL include:

- signature.sig_alg
- signature.signer_id
- signature.key_ref
- signature.value

If signature verification fails or cannot be performed, validators SHALL treat such Evidence as INVALID and SHALL apply FAIL-CLOSED handling for any canonical decision.

---

## 4. Replay Enforcement (Audit-Grade)

Replay mismatch SHALL be treated as Semantic Validation failure.

Replay mismatch SHALL generate explicit GOVERNANCE_VIOLATION Evidence.

---

## 5. Registry Drift Enforcement (Canonical Decision Blocking)

Registry drift SHALL be treated as SEMANTIC FAIL-CLOSED for canonical decisions.

When registry enforcement is enabled, registry mismatch SHALL generate GOVERNANCE_VIOLATION Evidence.

Registry mechanisms SHALL NOT introduce new decision semantics; they SHALL only encode artifacts and anchors required by the active Semantic Ruleset.

---

END OF RC2 PATCH
