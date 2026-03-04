📜 TRACE ROW GOVERNANCE — THRESHOLD PROFILES ANNEX v1.1

Status: ACTIVE
Type: Normative Annex
Owner: Governance Council

Normatively referenced by:

Governance Risk Engine Annex

TRACE_ROW_RISK_POLICY_PROFILE_SPEC

Governance Health Dashboard Spec

Governance Simulation Spec

1. PURPOSE

This annex defines deterministic threshold profiles used to map RiskScore values (0–100) into RiskLevel bands, including adaptive adjustment logic, invariants, auditability, and governance controls.

2. CORE DEFINITIONS
2.1 RiskScore Range

0 ≤ RiskScore ≤ 100

Values MUST be clamped prior to threshold evaluation.

2.2 RiskLevel Enumeration

GREEN
AMBER
RED
BLACK

3. DEFAULT THRESHOLD PROFILE
RiskLevel	Range
GREEN	0–30
AMBER	31–60
RED	61–80
BLACK	81–100

threshold_profile_id = DEFAULT_STANDARD

4. ENVIRONMENT PROFILES
PROD_STRICT

GREEN 0–25
AMBER 26–50
RED 51–70
BLACK 71–100

STAGE_BALANCED

GREEN 0–30
AMBER 31–60
RED 61–80
BLACK 81–100

DEV_RELAXED

GREEN 0–40
AMBER 41–70
RED 71–90
BLACK 91–100

5. ADAPTIVE ADJUSTMENT MODEL (FORMALIZED)
5.1 Adaptive Boundary Function

Adaptive boundaries MUST be computed using:

B_effective = B_base − f(C, I)


Where:

B_base = base boundary
C = criticality factor
I = incident rate factor

5.2 Criticality Function
Criticality	f(C)
LOW	0
MEDIUM	k1
HIGH	k2

k1, k2 MUST be defined in policy_profile.

5.3 Incident Rate Function
f(I) = min( I / threshold_incident_rate * k3 , max_shift )


Parameters MUST be defined in policy_profile.

5.4 Combined Adjustment
f(C,I) = f(C) + f(I)

6. ADAPTIVE INVARIANTS

Implementations MUST guarantee:

GREEN < AMBER < RED < BLACK

Bands MUST NOT overlap

PROD environment MUST NOT widen GREEN band

Adjustments MUST be monotonic

7. POLICY PARAMETERIZATION

Adaptive coefficients MUST be defined in policy_profile.

Annex defines only allowed structure and bounds.

8. DASHBOARD VISUALIZATION STANDARD

Dashboard MUST display:

threshold_profile_id
effective boundaries
adaptive indicator

8.1 Color Palette

GREEN #2ECC71
AMBER #F1C40F
RED #E74C3C
BLACK #2C3E50

8.2 Adaptive Indicator

UI MUST display icon/badge when adaptive logic applied.

9. AUDIT REQUIREMENTS

Audit MUST record:

threshold_profile_id
effective_threshold_values
reason_code
policy_profile_id

10. EXPORT REQUIREMENTS

All exports MUST include:

threshold_profile_id
threshold_profile_version
effective_threshold_values
reason_code

11. GOVERNANCE CONTROL

Changes MUST include:

approval_record_id
change_log_ref

11.1 Rollback Requirement

Each change MUST define:

previous_profile_version
rollback_plan

11.2 Approval Workflow

Proposal → Review → Approval → Deployment

12. FAILURE BEHAVIOR
12.1 Grace Period

System MAY use last valid profile during grace period (default 5 minutes).

12.2 Fallback Profile

Fallback profile MUST be defined in policy_profile.

13. SECURITY

Only governance roles MAY modify threshold profiles.

13.1 Integrity Verification

Profiles MUST support hash/signature validation.

Integrity failure MUST trigger governance incident.

14. SIMULATION

Simulation MUST record:

simulation=true

15. DASHBOARD CONTRACT

Dashboard MUST NOT compute thresholds locally.

16. CROSS-ARTIFACT CONSISTENCY

Risk Engine is single source of truth.

17. FUTURE EXTENSIONS

ML-proposed thresholds MUST require governance approval.

Time-varying thresholds MUST be deterministic and auditable.

🧾 END OF SPEC