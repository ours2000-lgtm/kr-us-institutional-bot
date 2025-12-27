Governance Constitution
1. Preamble
This document defines the fundamental governance principles of the KR/US Institutional Automated Trading System.

This repository represents the design and governance layer, not a runtime execution environment.

All system design, implementation, and operational decisions MUST align with the principles defined in this constitution.

This constitution exists to:

Prevent silent risk accumulation

Enforce accountability and traceability

Preserve long-term system integrity over short-term performance

2. Core Principles
2.1 Fail-Closed by Default
Any undefined, degraded, or uncertain state MUST result in execution being blocked, not permitted.

2.2 Risk-First Architecture
Risk management is not a component but the governing axis of the system.
Profitability MUST never override risk constraints.

2.3 No Silent Execution
All actions, decisions, and state transitions MUST be observable, traceable, and auditable.

2.4 Explicit Responsibility
Every decision MUST have a clearly attributable owner, whether human or system-defined.

2.5 Design Before Automation
Automation MUST follow explicit design contracts and governance approval.

---

## 3. Governance Scope

This constitution governs all artifacts and decisions that belong to the
**design and governance layer** of the KR/US Institutional Automated Trading System.

### 3.1 In-Scope

This constitution applies to, but is not limited to:

- System architecture and design contracts
- Risk models, constraints, and evaluation logic
- Observability definitions (logging, tracing, alerting)
- Governance processes, proposals, and approvals
- Any document or specification that directly or indirectly influences execution behavior

### 3.2 Out-of-Scope

This constitution does NOT directly govern:

- Runtime execution code and launchers
- Infrastructure provisioning and deployment tooling
- Secrets, credentials, or environment-specific configurations
- External services, brokers, or exchanges

These elements may exist elsewhere but MUST NOT violate the principles
defined in this constitution.

### 3.3 Supremacy

In the event of conflict between this constitution and any other
document, specification, or implementation detail, **this constitution takes precedence**.

Any exception MUST be explicitly documented, justified, and approved
through the defined governance process.
