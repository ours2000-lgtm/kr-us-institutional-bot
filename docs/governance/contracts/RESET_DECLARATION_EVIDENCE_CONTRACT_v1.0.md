# RESET_DECLARATION_EVIDENCE_CONTRACT_v1.0

Status: LOCK
Doc-ID: RESET-DECLARATION-CONTRACT-v1.0
Doc-Version: v1.0
Created-At-UTC: 2026-02-12T00:00:00Z
Last-Updated-UTC: 2026-02-12T00:00:00Z
Authority-Tier: T3
Scope: Chain Reset Governance Entry Contract

Parent-Specs:
  - GOVERNANCE_HEADER_SPEC_v1.0
  - RESET_POLICY_FSM_v1.0
  - FSM_VALIDATOR_CONSTITUTION_v1.0

Integrity-Anchors:
  Document-SHA256: __FILL_ON_LOCK__
  Signatures:
    - tier: T3
      signer_id: __FILL__
      signature: __FILL__
      signed_at_utc: __FILL__

--------------------------------------------------------------------

## 0. Purpose

RESET_DECLARATION Evidence defines the ONLY authorized entry point for chain reset.

No chain head replacement SHALL occur without a valid RESET_DECLARATION artifact.

--------------------------------------------------------------------

## 1. Contract Scope

RESET_DECLARATION governs:

• Evidence chain reset  
• Genesis re-anchor declaration  
• Governance approval binding  
• Chain continuity audit trail  

--------------------------------------------------------------------

## 2. RESET_DECLARATION Artifact Structure

### 2.1 REQUIRED Top-Level Fields

```json
{
  "artifact_type": "RESET_DECLARATION",
  "artifact_version": "RESET_DECLARATION_v1",
  "created_at_utc": "RFC3339",
  "reset_case_id": "string",
  "reason": "string",
  "old_head_hash": "string|null",
  "new_genesis_hash": "string",
  "approved_by": [ApprovalEntry],
  "chain": ChainBinding
}
3. Field Definitions
3.1 reset_case_id
Unique reset workflow identifier.

Rules:

MUST match Reset FSM case ID

MUST NOT be reused

MUST be globally unique

3.2 reason
Human-readable justification.

Required Content:

• Failure summary
• Risk classification
• Forensics reference

3.3 old_head_hash
string | null
Rules:

MUST equal previous chain head

NULL allowed ONLY for system-first GENESIS

3.4 new_genesis_hash
string
Rules:

MUST equal chain.this_hash of declaration evidence

MUST become next chain head

4. Approval Bundle Binding
4.1 approved_by
{
  "tier": "T1|T2|T3",
  "actor_id": "string",
  "signature": "string",
  "signed_at_utc": "timestamp"
}
4.2 Approval Requirements
Minimum policy:

• T2 + T3 approval required
• Approver IDs MUST be distinct
• Approval MUST reference same reset_case_id

5. Chain Binding Rules
5.1 Chain Object
"chain": {
  "prev_hash": "string|null",
  "this_hash": "string"
}
5.2 Binding Invariants
I1 Declaration-First
Reset execution SHALL NOT occur unless:

RESET_DECLARATION exists AND verified
I2 Hash Continuity
old_head_hash MUST equal chain.prev_hash
I3 GENESIS Rule
old_head_hash == null allowed ONLY for system-first genesis
I4 Evidence Chain Binding
RESET_DECLARATION evidence SHALL obey standard chain rules:

• R1 Missing hash forbidden
• R2 Broken link forbidden
• R3 Tamper detection mandatory
• R4 Genesis uniqueness enforced

6. Separation of Duties
Execution authority SHALL be separated from approval authority.

Future extension:

executed_by MUST NOT be in approved_by.actor_id
7. FSM Integration
RESET_DECLARATION SHALL only be produced when FSM state:

APPROVED → EXECUTED
Mandatory conditions:

• Cool-off satisfied
• Approval bundle verified
• Chain validation PASS

8. Cool-Off Governance
Default policy:

Minimum waiting period: 24 hours
Emergency override:

Requires ≥2 T3 approvals
9. Failure Handling
Condition	Policy
Missing declaration	HARD FAIL
Approval mismatch	HARD FAIL
Chain mismatch	CORRUPT
Duplicate Genesis	MULTIPLE_GENESIS
CORRUPT declarations:

• Ignored in normal chain
• Retained for forensic audit

10. Chain Health Integration
Health Scoring Rules:

Valid RESET_DECLARATION → No penalty or minor warning
Unauthorized head change → Grade F
11. Time Drift Governance
TIME_DRIFT SHALL NOT independently trigger reset.

TIME_DRIFT MAY:

• Increase approval threshold
• Trigger additional review

12. Audit & Forensics Requirements
RESET_DECLARATION MUST include:

• Approval signatures
• Hash chain references
• Reason documentation

13. Amendment Rules
LOCKED Specification.

Changes require:

• Amendment Procedure
• T3 Governance Approval
• Hash Anchor Update

END OF CONTRACT