Raw Market Data
      ↓
FactorEngine
      ↓
FactorSnapshot
      ↓
PolicyEngine (Decision Only)
      ↓
PolicyContext
      ↓
RiskOrchestratorV2Plus (Execution Constitution)
      ↓
 ┌───────────────┬────────────────────┐
 │ pre-core gate │ CoreEngine (V1.11) │
 └───────────────┴────────────────────┘
      ↓
post-core override / fail-safe
      ↓
V2 Risk Result

FactorSnapshot:
  rolling_volatility: float
  rolling_liquidity: float
  data_quality: ok | insufficient | invalid
  window_size: int
  raw_snapshot: dict

PolicyContext:
  regime: string
  policy_name: string
  risk_level_cap: low | medium | high | critical
  overrides:
    force_halt: bool
    exposure_cap: float
    risk_level_cap: string
  thresholds: dict
  reason_codes: list[string]
  trigger_values: dict
  policy_version: string   # ⚠️ runtime 시 Orchestrator가 반드시 주입

SAFE_CORE_RESULT_SCHEMA:
  risk_level: low
  risk_score: 0.0
  exposure: 0.0
  halted: true
  meta:
    regime: null
    policy_name: null
    force_halt: true
    exposure_cap: 0.0
    risk_level_cap: null
    reason_codes: []
    trigger_values: {}
    policy_version: null
    halt_reason: policy_force_halt
    halt_regime: null
    halt_policy_name: null

data_quality != ok  → invalid_data

rolling_liquidity < min_liquidity → illiquid

0 <= spike_volatility < crash_volatility

rv >= crash_volatility → crash
rv >= spike_volatility → spike
else                  → normal

risk_level_cap: high
force_halt: false
exposure_cap: 1.0

policy_name: P_INVALID_DATA
risk_level_cap: low
force_halt: true
exposure_cap: 0.0

policy_name: P_ILLIQUID
risk_level_cap: low
force_halt: true
exposure_cap: 0.0

policy_name: P_CRASH
risk_level_cap: low
force_halt: true
exposure_cap: 0.0

policy_name: P_SPIKE
risk_level_cap: medium
force_halt: false
exposure_cap: 0.5

policy_name: P_NORMAL
risk_level_cap: high
force_halt: false
exposure_cap: 1.0

1. validate_data_quality
2. evaluate_liquidity
3. evaluate_volatility
4. determine_regime
5. load_policy
6. assemble_context

1. FactorEngine.run()
2. PolicyEngine.decide_policy()
3. policy_version 주입 (Orchestrator 책임)
4. pre-core gate
   - force_halt == True → Core 호출 ❌
5. Core 호출 OR safe_core_result
6. post-core override
   - exposure clamp
   - risk_level_cap tag-only
7. 결과 반환

V2_PRE_CORE_GATE_HIT
V2_CORE_CALLED
V2_CORE_EXCEPTION_FALLBACK
V2_AGGREGATION_EXCEPTION
V2_ORCHESTRATION_COMPLETED














