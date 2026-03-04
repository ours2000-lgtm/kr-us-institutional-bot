# INCIDENT_TO_ALERT_MAPPING_v0.3

## 목적
Governance Incident(Health/Chain/Gate/Policy) → Prometheus Alert Rule/Labels/Runbook/Receiver로 1:1 바인딩한다.
이 문서는 운영 외부 인터페이스의 SSOT이며 v0.3 FREEZE 번들에 포함된다.

## Label Contract (SSOT)
Required labels:
- incident_key: <INCIDENT_...>
- severity: critical|warning|info
- team: governance|runtime|trading
- service: kr_us_bot
- component: chain|gate|health|runtime|policy
- runbook: <relative path or URL>

Optional labels:
- strategy_id: (if applicable)
- env: local|paper|prod

## Mapping Table

| incident_key | component | severity | alert_name | prom_expr | for | runbook |
|---|---|---|---|---|---:|---|
| INCIDENT_CHAIN_VALIDATION_FAIL | chain | critical | ChainValidationFail | chain_validation_fail_total > 0 | 0m | docs/runbooks/CHAIN_VALIDATION_FAIL.md |
| INCIDENT_GATE_DECISION_BLOCK | gate | critical | ControlPlaneGateBlock | control_plane_gate_block_total > 0 | 0m | docs/runbooks/GATE_BLOCK.md |
| INCIDENT_GOV_HEALTH_RED | health | critical | GovernanceHealthRed | governance_health_status{status="RED"} == 1 | 1m | docs/runbooks/GOV_HEALTH_RED.md |
| INCIDENT_GOV_HEALTH_AMBER | health | warning | GovernanceHealthAmber | governance_health_status{status="AMBER"} == 1 | 3m | docs/runbooks/GOV_HEALTH_AMBER.md |
| INCIDENT_RUNTIME_SCHEMA_VIOLATION | runtime | critical | RuntimeSchemaViolation | runtime_schema_violation_total > 0 | 0m | docs/runbooks/RUNTIME_SCHEMA_VIOLATION.md |
| INCIDENT_POLICY_FREEZE_SUGGESTED | policy | warning | PolicyFreezeSuggested | policy_feature_freeze_suggested == 1 | 5m | docs/runbooks/POLICY_FREEZE_SUGGESTED.md |

## Notes
- prom_expr는 metrics 이름이 확정되면 v0.3에서 함께 고정한다.
- metrics가 아직 없으면 "event-to-metric bridge"를 통해 최소 카운터/게이지를 제공해야 한다.