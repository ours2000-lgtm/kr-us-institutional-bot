# CRYPTOGRAPHIC_POLICY_ANNEX_v1_RC2_PATCH.md
Status: RC2 PATCH (NORMATIVE DELTA)
Revision: v1.0-RC2-PATCH
Authority Tier: CANONICAL ANNEX (CRYPTO POLICY)
Parent Baseline: CRYPTOGRAPHIC_POLICY_ANNEX_v1.md
Default Semantics: FAIL-CLOSED

This RC2 patch clarifies the minimum signature guarantee for v1 Evidence and defines a forward-compatible extension hook for multi-signature governance.

This patch SHALL NOT weaken any guarantees established by the Parent Baseline.

---

## 1. Scope

This patch applies to Evidence records that are:
- used for LOCK decisions, OR
- used for governance/canonical decision pathways.

---

## 2. Minimum Signature Guarantee (v1)

### 2.1 Requirement

Evidence used for LOCK or governance decisions SHALL include at least one independently verifiable digital signature.

In v1, such Evidence SHALL include exactly one signature object named `signature`.

### 2.2 Signature Object Canonical Fields

The `signature` object SHALL include sufficient material for independent verification under this Annex.

At minimum, `signature` SHALL include:

- sig_alg (string): signature algorithm identifier
- signer_id (string): signer identity (authority / emitter / role identifier)
- key_ref (string): reference to a verification key or certificate chain
- value (string): the signature value

If any of the above are missing, unparsable, or inconsistent with Annex requirements, verifiers SHALL treat such Evidence as INVALID and SHALL apply FAIL-CLOSED behavior for any canonical decision.

---

## 3. Verification Capability Clause

A signature SHALL be considered "verifiable" only if an independent verifier can validate it using:

- the algorithm identifier (sig_alg),
- the key reference (key_ref),
- the trust anchor procedures and allowed cryptographic sets bound by this Annex,
- and the signature value (value).

Mere presence of a signature field SHALL NOT be sufficient; verification capability SHALL be the requirement.

---

## 4. Forward-Compatible Multi-Signature Hook

Multi-signature governance MAY be introduced in future Annex revisions via an additional `signatures[]` structure.

### 4.1 Non-Weakening Constraint

The introduction of `signatures[]` SHALL NOT weaken the minimum guarantee provided by `signature` in v1.

The `signature` object SHALL remain the minimum cryptographic guarantee unless explicitly superseded by a Constitutional Amendment that upgrades the major version.

### 4.2 Governance Control

Any introduction of `signatures[]`, N-of-M policies, or multi-authority requirements SHALL be governed exclusively by the Amendment Procedure.

---

## 5. Algorithm Set Governance

This patch does not enumerate approved algorithm sets.

Approved hash and signature algorithm sets SHALL be governed by the active Cryptographic Policy Annex (and any ratified updates thereto) and SHALL remain crypto-agile under Amendment control.

---

END OF RC2 PATCH
