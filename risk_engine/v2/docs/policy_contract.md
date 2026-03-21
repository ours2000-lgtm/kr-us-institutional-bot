# PolicyEngine Contract (V2.0.0 – Frozen)

본 문서는 Risk Engine V2.0.0 기준의 PolicyEngine 계약(Contract) 문서이다.

- PolicyEngine은 FactorEngine의 출력을 해석하여
  “현재 시장/데이터 상태(Regime)”와
  “적용할 리스크 정책(PolicyContext)”을 결정한다.
- 본 문서는 V2.0.0 기준으로 동결되며,
  이후 버전(V2.1+)에서는 확장만 허용한다.
- PolicyEngine 구현은 반드시 본 계약을 따른다.

---

## 1. PolicyEngine 역할

PolicyEngine은 엔진 전체의 **두뇌** 역할을 수행한다.

결정 책임:
- 현재 상태가 어떤 Regime인지
- 어떤 리스크 정책을 적용할지
- 리스크를 축소/확대/차단할지
- Core 결과를 override할지 여부

PolicyEngine이 없으면:
- Core는 점수 계산기,
- Aggregation은 빈 껍데기에 불과하다.

---

## 2. 입력 (Input)

PolicyEngine은 다음 입력을 받는다.

### 2.1 FactorSnapshot
- `rolling_volatility` (float)
- `rolling_liquidity` (float)
- `data_quality` (`ok | insufficient | invalid`)
- `window_size` (int)
- `raw_snapshot` (dict)

---

## 3. 출력 (PolicyContext)

PolicyEngine은 PolicyContext를 반환한다.

```yaml
PolicyContext:
  regime: string
  policy_name: string
  risk_level_cap: low | medium | high | critical
  overrides:
    force_halt: bool
    exposure_cap: float
    max_position_per_symbol: float (optional)
    cooldown_seconds: int (optional)
  thresholds: dict
  reason_codes: list[string]
  trigger_values: dict

illiquid 조건:
- data_quality == "ok"
- rolling_liquidity < THRESHOLDS.min_liquidity

0 <= spike_volatility < crash_volatility

if rv >= crash_volatility:
    regime = crash
elif rv >= spike_volatility:
    regime = spike
else:
    regime = normal

POLICIES:
  DEFAULTS:
    risk_level_cap: high
    force_halt: false
    exposure_cap: 1.0

  REGIMES:
    invalid_data:
      policy_name: P_INVALID_DATA
      risk_level_cap: low
      force_halt: true
      exposure_cap: 0.0

    illiquid:
      policy_name: P_ILLIQUID
      risk_level_cap: low
      force_halt: true
      exposure_cap: 0.0

    crash:
      policy_name: P_CRASH
      risk_level_cap: low
      force_halt: true
      exposure_cap: 0.0

    spike:
      policy_name: P_SPIKE
      risk_level_cap: medium
      force_halt: false
      exposure_cap: 0.5

    normal:
      policy_name: P_NORMAL
      risk_level_cap: high
      force_halt: false
      exposure_cap: 1.0

THRESHOLDS:
  min_window: 5
  min_liquidity: 100000
  spike_volatility: 0.02
  crash_volatility: 0.05



reason_codes:
  - LOW_LIQUIDITY
  - VOL_SPIKE

trigger_values:
  rolling_liquidity: 80000
  rolling_volatility: 0.034


---

## 🔒 상태 선언



---

## Regime Definitions & Priority

Regime는 아래 우선순위로 평가된다:

1. invalid_data
2. illiquid
3. crash
4. spike
5. normal

- invalid_data: data_quality가 invalid 또는 insufficient인 경우
- illiquid: rolling_liquidity < min_liquidity
- crash: rolling_volatility >= crash_volatility
- spike: rolling_volatility >= spike_volatility
- normal: 위 조건에 해당하지 않는 경우

## Deterministic Policy Pipeline (V2.0)

PolicyEngine은 반드시 아래 순서로 판단한다:

1. validate_data_quality
2. evaluate_liquidity
3. evaluate_volatility
4. determine_regime
5. load_policy
6. assemble_context

- 모든 단계는 예외를 던지지 않는다.
- 어떤 경우에도 PolicyContext를 반환한다.
- 예외/누락/불일치는 invalid_data 정책으로 fail-safe 처리한다.

### Constants
- data_quality:
  - ok
  - insufficient
  - invalid

### Regimes
- normal
- spike
- crash
- illiquid
- invalid_data

### PolicyContext Fields
- regime
- policy_name
- risk_level_cap
- overrides
- thresholds
- reason_codes
- trigger_values
- policy_version

### Reason Codes (Non-exhaustive)
- DATA_INVALID
- DATA_INSUFFICIENT
- LOW_LIQUIDITY
- MISSING_LIQUIDITY
- INVALID_LIQUIDITY_VALUE
- MISSING_VOLATILITY
- INVALID_VOLATILITY_VALUE
- VOL_SPIKE
- VOL_CRASH
- REGIME_UNKNOWN
- POLICY_DEF_MISSING
- THRESHOLD_MISSING_VOLATILITY
- THRESHOLD_RELATION_INVALID
- UNHANDLED_EXCEPTION

Constraint:
- 0 <= spike_volatility < crash_volatility

## Status
- PolicyEngine: V2.0.1 — FROZEN
- Contract: policy_contract.md V2.0.0
- Scope:
  - Deterministic rule-based policy engine
  - Fail-safe, no-exception design
  - Observability-first (reason_codes / trigger_values)

Advanced features (relative liquidity, hysteresis, strategy overrides)
are deferred to V2.1+.






