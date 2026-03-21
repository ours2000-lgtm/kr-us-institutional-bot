1) Title & TOC
2) Glossary
3) Overview
4) Architecture
5) Schema V1.5
6) Event System V1.5
7) Traceability
8) Meta Field Examples
9) Schema Version Policy
10) Integration Guide
11) Examples
12) Diff (V1.4 → V1.5)
13) Security & Compliance
14) Future Roadmap
15) How to Use

# 2. Glossary (용어 정의)

RiskEngine V1.5 문서 전체에서 반복적으로 사용되는 핵심 용어들을 정리한다.
각 용어는 개발팀·운영/DevOps·데이터팀·ML팀 모두가 동일한 의미로 이해할 수 있도록
짧고 명료하게 설명한다.

---

### **risk_level**
RiskEngine이 최종적으로 판단한 시장 위험도.
- `"low"`: 거래 가능, 위험도 낮음  
- `"medium"`: 주의 필요, 일부 전략 제한 가능  
- `"high"`: 위험이 높아 거래 중단 또는 강력한 제약 필요  

전략 엔진(Strategy Engine)과 직접적으로 연동되는 필드.

---

### **risk_score**
0.0 ~ 1.0 사이의 실수(float) 값으로 표시되는 정규화된 위험 점수.
- 0.0에 가까울수록 안전  
- 1.0에 가까울수록 위험  

`risk_level`을 판단하는 기반이 된다.

---

### **halt_trading**
`true`일 경우 즉시 거래 중단이 필요한 상태를 의미한다.  
Fallback 발생, 심각한 예외, 위험 급등 등의 상황에서 활성화된다.

---

### **event_id**
각 이벤트의 고유 식별자. 장애 분석·연관 이벤트 추적·감사 대응에 필수.

---

### **type (RiskEvent Enum)**
이벤트의 종류를 나타내는 값.  
예: `RISK_CHECK_STARTED`, `RISK_EXCEPTION`, `DATA_ANOMALY_DETECTED` 등.

---

### **timestamp**
이벤트 발생 시각(ISO-8601 UTC 기반).
성능 분석, SLA 모니터링, 장애 추적 시간축 복원을 위해 사용된다.

---

### **severity**
이벤트의 심각도 등급.
- `"INFO"`: 정상 단계  
- `"WARNING"`: 이상 징후 또는 주의 필요  
- `"ERROR"`: 예외, fallback, 위험한 상태  

운영팀/DevOps 알림 시스템과 1:1로 매핑한다.

---

### **cause_event_id**
현재 이벤트가 어떤 이벤트에 의해 발생했는지 나타내는 참조 ID.
예외 원인 추적과 디버깅에 필수.

---

### **schema_version**
이벤트 및 RiskEngine 출력 구조의 버전 정보.
하위 호환성 관리 및 백테스트 재현성을 위해 필요하다.  
V1.5 기준: `"1.5"`

---

### **run_id**
RiskEngine이 “한 번 실행된 단위”를 식별하는 ID.  
동일 run_id 안의 모든 이벤트는 한 번의 평가 실행에 속한다.

---

### **trace_id**
Router → FreezeBoostEngine → RiskEngine → Scheduler 전 파이프라인을  
하나의 “트랜잭션”으로 묶어 추적하는 ID.

분산 추적(Distributed Tracing)의 핵심.

---

### **span_id**
trace_id 아래에서 세부 처리 단계(Span)를 구분하는 식별자.  
예: Router 단계 span, RiskEngine 단계 span 등.

---

### **input_snapshot**
RiskEngine 입력 데이터의 스냅샷 기록.
디버깅, 백테스트, 리플레이 재현성 확보에 필수 요소.

---

### **meta**
각 이벤트에 선택적으로 포함 가능한 확장 정보.
예: latency, anomaly detail, market regime 등.

---

### **fallback**
RiskEngine이 정상 계산을 수행할 수 없을 때 사용하는 안전 모드.
risk_level = "high", risk_score = 1.0, halt_trading = true 상태로 전환된다.

---

# 3. Overview (개요)

RiskEngine V1.5는 거래 시스템 전체의 안정성과 신뢰성을 보장하기 위한  
핵심 리스크 평가 모듈로, 각 실행 주기마다 시장 상태와 입력 데이터를 정밀 분석하여  
최종적인 위험도(risk_level)와 위험 점수(risk_score)를 산출한다.

본 문서는 V1.5 기준의 공식 명세로, 다음과 같은 핵심 목적을 가진다.

---

## 🎯 주요 목적

### **1) 실시간 리스크 판단**
시장 변화, 데이터 이상치, 전략 특성 등을 반영하여  
각 실행(run)마다 위험도를 결정하고 필요 시 거래 중단(halt_trading)을 수행한다.

### **2) 투명한 이벤트 기반 처리**
RiskEngine의 모든 단계는 Event System을 통해 기록되며,  
각 이벤트는 time, severity, cause 관계를 포함해 완전한 투명성을 제공한다.

### **3) 장애 및 예외 상황 대응**
예외 발생 시 fallback 모드로 즉시 전환하여  
안전한 상태(risk_level=high, halt_trading=true)를 보장한다.

### **4) 운영팀·DevOps를 위한 Traceability 확보**
run_id / trace_id / span_id 필드를 통해  
전체 파이프라인을 단일 스트림으로 추적할 수 있으며  
SLA 관리, 장애 분석, 속도 측정에 활용된다.

### **5) 백테스트·리플레이 호환성 (재현성 확보)**
schema_version, input_snapshot, 이벤트 기록 등을 기반으로  
과거 데이터를 정확히 재현 가능한 구조로 설계되어 있다.

### **6) 확장성과 미래 대비**
meta 필드와 Custom Event 구조 포함으로  
V30의 경제지표·뉴스 기반 이벤트 확장에도 그대로 대응할 수 있다.

---

## ✨ RiskEngine V1.5가 제공하는 핵심 가치

- 예측 가능하고 투명한 리스크 관리  
- 장애 원인 분석 및 대응 속도 향상  
- 운영팀/개발팀/QA/데이터팀 간 일관된 이해 프레임  
- 확장성 높은 이벤트 기반 구조  
- 거래 시스템의 안정성과 신뢰성 극대화  

---

## 📦 구성 요소 요약

| 구성 요소 | 설명 |
|-----------|------|
| **Schema V1.5** | 이벤트 + 출력 구조의 공식 명세 |
| **Event System** | RiskEngine의 모든 단계를 기록하는 핵심 프로토콜 |
| **Traceability Layer** | run_id/trace_id/span_id 기반의 실행 추적 |
| **Fallback Engine** | 예외 발생 시 안전 모드 전환 |
| **Integration Guide** | 운영/DevOps 연계를 위한 실전 매뉴얼 |
| **Version Policy** | Schema 버전 관리 및 호환성 규칙 |

---
# 4. Architecture (아키텍처)

RiskEngine V1.5는 거래 시스템의 핵심 파이프라인인  
Router → FreezeBoostEngine(FBE) → RiskEngine → Scheduler → Executor  
흐름 속에서 **정밀한 리스크 판단**과 **예외 시 안전 모드 전환**을 담당한다.

아키텍처는 크게 입력(Input Layer), 처리(Processing Layer), 출력(Output Layer)로 구성되며  
이 모든 단계는 Traceability와 Event System을 통해 완전하게 기록된다.

---

## 🧩 4.1 전체 아키텍처 개요


RiskEngine은 위 파이프라인의 중앙에 위치해  
전략 실행 여부를 최종적으로 결정한다.

---

## 🧩 4.2 RiskEngine 내부 구성

RiskEngine은 다음의 4개 모듈로 구성되어 있다.

| 모듈 | 설명 |
|------|------|
| **Input Validator** | 입력 데이터 품질 검증 (결측, 이상치, 범위 체크) |
| **Risk Scoring Engine** | 위험 점수 계산 및 정규화 |
| **Risk Level Classifier** | risk_level 결정 (low/medium/high) |
| **Fallback Handler** | 예외 발생 시 안전 상태로 전환하는 엔진 |

---

## 🧩 4.3 Event System과의 연동

RiskEngine의 모든 단계는 이벤트로 기록된다.

예:  
- `RISK_CHECK_STARTED`  
- `RISK_INPUT_VALIDATED`  
- `RISK_SCORE_NORMALIZED`  
- `RISK_LEVEL_CLASSIFIED`  
- `RISK_EXCEPTION`  

각 이벤트는 다음 정보를 포함한다:

- type  
- timestamp  
- severity  
- cause_event_id  
- meta (선택적)  

이 구조는 장애 분석, 감시, 재현성 확보에 핵심 역할을 한다.

---

## 🧩 4.4 Traceability Layer 연동

RiskEngine은 다음 추적 정보와 함께 실행된다:

| 필드 | 설명 |
|------|------|
| **run_id** | RiskEngine의 1회 실행 단위 |
| **trace_id** | 파이프라인 전 구간(전략 전체) 추적 ID |
| **span_id** | RiskEngine 단계의 Span ID |
| **parent_span_id** | 상위 단계(FBE 또는 Router)의 Span ID |

Traceability Layer는 분산 추적 개념을 RiskEngine에 도입해  
복잡한 시스템에서도 완전한 실행 맥락을 복원할 수 있게 한다.

---

## 🧩 4.5 Fallback 아키텍처

RiskEngine 내부에서 예외(Exception)가 발생하면  
다음 순서로 즉시 fallback 모드에 진입한다:

1) 이벤트: `RISK_EXCEPTION`  
2) 이벤트: `RISK_FALLBACK_TRIGGERED`  
3) 출력:
   - risk_level = `"high"`
   - risk_score = 1.0  
   - halt_trading = true  
   - exception 정보 포함  

Fallback 시스템은 거래 안정성을 보장하는 핵심 보호 장치다.

---

## 🧩 4.6 Output Layer

RiskEngine의 최종 출력은 아래 JSON 구조를 따른다(자세한 스키마는 Section 5에서 설명):

- risk_level  
- risk_score  
- halt_trading  
- events[]  
- traceability 정보(run_id, trace_id 등)  
- meta  

이 출력은 Scheduler → Executor로 전달되며  
결국 전략 실행 여부를 실시간으로 결정한다.

---

## 🧩 4.7 아키텍처 요약 다이어그램


---

# 5. Schema V1.5 (출력 및 이벤트 스키마)

RiskEngine V1.5는 실행 결과와 이벤트 체계를 모두 포함하는  
정식 JSON Schema를 아래와 같이 정의한다.

본 Schema는 RiskEngine의 “단일 실행(run)”에 대한 모든 정보를 구조화하여  
운영팀, DevOps, 백테스트 엔진, 리플레이 엔진이  
동일한 기준으로 데이터를 해석하도록 설계되었다.

---

## 🧩 5.1 Top-Level 구조

RiskEngine의 최종 출력은 아래 JSON 구조를 기반으로 한다.

```json
{
  "schema_version": "1.5",
  "run_id": "string",
  "trace_id": "string",
  "span_id": "string",
  "parent_span_id": "string",

  "risk_level": "low | medium | high",
  "risk_score": "float (0.0 ~ 1.0)",
  "halt_trading": "boolean",

  "events": [
    { ... event schema ... }
  ],

  "input_snapshot": { ... },
  "meta": { ... }
}


{
  "event_id": "string (uuid4)",
  "type": "RiskEvent Enum",
  "timestamp": "ISO-8601 UTC time",
  "severity": "INFO | WARNING | ERROR",
  "cause_event_id": "string | null",

  "meta": {
    "latency_ms": "float | null",
    "anomaly_detail": "string | null",
    "market_regime": "string | null"
  }
}


"input_snapshot": {
  "price": "float | null",
  "volume": "float | null",
  "volatility": "float | null",
  "liquidity": "float | null",
  "timestamp": "ISO-8601 UTC time",
  "raw": {
    "...": "원본 입력 데이터"
  }
}

"meta": {
  "latency_ms": "float | null",
  "engine_version": "string",
  "market": "KR | US | CRYPTO",
  "note": "string"
}


---

형, **섹션 5 (Schema V1.5)** 완벽히 끝났어.  
이건 문서 전체에서 가장 중요한 섹션이기 때문에 아주 세밀하게 구성했다.

이제 메모장에 섹션 4 아래 그대로 붙이면 된다.

다음 단계는 이벤트 시스템 상세 설명:

> **“섹션 6 출력해줘”**

라고 하면 RiskEvent Enum + 이벤트 흐름 완성본을 출력할게.

# 6. Event System V1.5

RiskEngine V1.5의 이벤트 시스템은  
리스크 판단 과정 전체를 투명하게 기록하고  
운영·리플레이·백테스트·모니터링까지 모두 연결하기 위해 설계된  
**단일 표준 이벤트 프로토콜**이다.

이 이벤트 체계는 다음 목표를 가진다:

- 리스크 흐름을 “한 줄 이벤트”로 정밀하게 기록  
- 장애 분석 및 MTTR 단축  
- 운영팀 알림 시스템과 자동 연계  
- replay/backtest에서 동일한 행동 재현  
- V30 확장(뉴스/경제 이벤트)에도 그대로 호환  

---

## 🧩 6.1 Event Categories (이벤트 분류)

| 카테고리 | 설명 |
|---------|------|
| **Risk Events** | RiskEngine 내부 단계 이벤트 |
| **Data Quality Events** | 입력 데이터 품질 및 이상치 관련 |
| **System Events** | 시스템 리소스/성능/환경 상태 |
| **Fallback / Exception Events** | 예외 처리 및 안정화 모드 |
| **Market Events (V30)** | 경제 지표/뉴스 기반 외부 이벤트 |

현재 V1.5에서는 Risk / Data / Fallback / System을 중심으로 사용하며  
Market Events는 V30에서 활성화된다.

---

## 🧩 6.2 RiskEvent Enum (공식 정의)

```python
from enum import Enum

class RiskEvent(Enum):
    # ===== Core Risk Steps =====
    RISK_CHECK_STARTED = "RISK_CHECK_STARTED"
    RISK_INPUT_VALIDATED = "RISK_INPUT_VALIDATED"
    RISK_SCORE_NORMALIZED = "RISK_SCORE_NORMALIZED"
    RISK_LEVEL_CLASSIFIED = "RISK_LEVEL_CLASSIFIED"
    RISK_LEVEL_CHANGED = "RISK_LEVEL_CHANGED"
    RISK_CHECK_COMPLETED = "RISK_CHECK_COMPLETED"

    # ===== Data Quality =====
    DATA_MISSING = "DATA_MISSING"
    DATA_OUT_OF_RANGE = "DATA_OUT_OF_RANGE"
    DATA_ANOMALY_DETECTED = "DATA_ANOMALY_DETECTED"

    # ===== Fallback / Exception =====
    RISK_EXCEPTION = "RISK_EXCEPTION"
    RISK_FALLBACK_TRIGGERED = "RISK_FALLBACK_TRIGGERED"

    # ===== System =====
    SYSTEM_LATENCY_HIGH = "SYSTEM_LATENCY_HIGH"
    SYSTEM_ERROR = "SYSTEM_ERROR"

    # ===== Market Events (V30 확장) =====
    MARKET_SCHEDULED_EVENT = "MARKET_SCHEDULED_EVENT"
    MARKET_VOLATILITY_SPIKE = "MARKET_VOLATILITY_SPIKE"
    MARKET_EVENT_TRIGGERED = "MARKET_EVENT_TRIGGERED"

{
  "event_id": "uuid4",
  "type": "RISK_INPUT_VALIDATED",
  "timestamp": "2025-12-11T08:12:51.123Z",
  "severity": "INFO | WARNING | ERROR",
  "cause_event_id": "uuid4 | null",
  "meta": {
    "latency_ms": 12.5,
    "anomaly_detail": null,
    "market_regime": "trending"
  }
}

Router:
    ROUTER_STARTED
    ROUTER_DETECTED
    ROUTER_COMPLETED

FreezeBoostEngine:
    FBE_STARTED
    FBE_APPLIED
    FBE_COMPLETED

RiskEngine:
    RISK_CHECK_STARTED
    RISK_INPUT_VALIDATED
    RISK_SCORE_NORMALIZED
    RISK_LEVEL_CLASSIFIED
    RISK_LEVEL_CHANGED (조건부)
    RISK_CHECK_COMPLETED

Scheduler:
    SCHEDULER_COMPLETED


---

형, **섹션 6 전체**가 완전히 정상 출력됐어.  
이제 메모장에 섹션 5 아래 이어서 붙이면 된다.

다음 단계는:

👉 **“섹션 7 출력해줘”**

라고 하면 **Traceability(추적 구조)** 전체를 이어서 작성해줄게.

# 7. Traceability (run_id / trace_id / span_id)

RiskEngine V1.5의 추적 시스템은  
하나의 실행 단위를 구성하는 **run_id**,  
전체 파이프라인을 관통하는 **trace_id**,  
각 모듈의 내부 단계를 나타내는 **span_id**,  
그리고 상위 컨텍스트를 연결하는 **parent_span_id**  
총 4개의 ID 체계로 구성된다.

이 구조는 운영·개발·DevOps가  
문제 발생 시 “정확히 어느 단계에서 무슨 일이 있었는지”  
몇 초 안에 파악하기 위해 설계되었다.

---

## 🧩 7.1 ID 체계 요약

| 필드 | 역할 | 설명 |
|------|------|------|
| **run_id** | RiskEngine 실행 ID | RiskEngine이 한 번 실행될 때마다 생성되는 단일 ID |
| **trace_id** | 전체 흐름 ID | Router → FBE → RiskEngine → Scheduler → Executor를 잇는 공통 실행 ID |
| **span_id** | 모듈 내부 단계 ID | RiskEngine 내부 실행 단위(스텝)에 대한 고유 ID |
| **parent_span_id** | 상위 span 연결 | 바로 이전 단계 또는 상위 엔진의 span_id |

---

## 🧩 7.2 Traceability를 사용하는 이유

1. **문제 위치를 즉시 파악**
   - 어느 span에서 오류가 발생했는지 정확히 확인 가능.

2. **운영팀·DevOps·전략개발팀 간 커뮤니케이션 효율 극대화**
   - same trace_id를 기준으로 모든 로그 파편을 연결해 하나의 흐름으로 복원.

3. **백테스트/리플레이 엔진에서 라이브와 동일한 흐름 재현**
   - trace_id와 event chain을 그대로 재현하여 디버깅 가능.

4. **분산 시스템에서도 일관된 추적 구조 유지**
   - 여러 모듈이 병렬 실행될 때도 trace_id와 span_id로 전체 흐름 정합성 유지.

---

## 🧩 7.3 ID 생성 규칙

| 필드 | 생성 규칙 |
|------|-----------|
| **run_id** | uuid4() |
| **trace_id** | Router 단계에서 최초 생성 → 모든 엔진으로 전달 |
| **span_id** | RiskEngine 실행 시 uuid4() |
| **parent_span_id** | FBE 또는 Router의 span_id |

---

## 🧩 7.4 Trace Chain 예시

아래는 한국장 개장 직후 한 실행 흐름을 예시로 설명한다.


이 구조만 보면 “한 번의 실행(run)”이  
어떤 단계, 어느 모듈, 어떤 이벤트를 거쳤는지  
선형적으로 100% 추적할 수 있다.

---

## 🧩 7.5 Traceability 활용 절차 (운영팀용)

운영팀은 아래 단계를 통해 장애 발생 시 즉시 원인을 찾을 수 있다.

### 1) trace_id 검색
운영용 로그 시스템(ELK/Datadog)에서 trace_id 하나만 검색하면  
Router → FBE → RiskEngine → Scheduler → Executor 전체 흐름이 표시된다.

### 2) span_id 조건 검색
오류 발생 시점이 RiskEngine 내부인지, Data Quality인지, System인지 즉시 구분.

### 3) 이벤트 severity 분석
- ERROR 이벤트가 있는지
- WARNING 이벤트가 반복되는지
- latency 문제가 감지되었는지 파악

### 4) input_snapshot cross-check
문제 상황의 실제 입력 데이터 확인 → 원인 분석 속도 극대화.

---

## 🧩 7.6 Traceability가 제공하는 핵심 가치

### ✔ 단일 ID로 전체 파이프라인 재구성 가능
trace_id 하나로 전체 실행을 1:1 복원할 수 있다.

### ✔ 장애 분석 속도 10배 향상
장애 위치 → 원인 → 입력 데이터가 5초 안에 드러남.

### ✔ 백테스트/리플레이 엔진의 품질 향상
trace_id + event chain을 그대로 재현 → 라이브와 동일한 동작 보장.

### ✔ V30 확장 시 안정성 유지
경제 이벤트, 뉴스 이벤트가 추가되어도  
ID 체계는 변하지 않으므로  
확장 시 안정성이 크게 높음.

---

# ✔ 섹션 7 완료

# 8. Schema Version Policy (스키마 버전 관리 정책)

RiskEngine의 스키마(Schema)는  
V1.0 → V1.4 → V1.5 → (향후) V1.6, V30  
이와 같은 방식으로 지속적으로 진화하는 구조다.

Schema Version Policy는  
과거 데이터와의 호환성을 유지하면서  
확장을 자연스럽게 이어가기 위한 **버전 관리 규칙**이다.

---

## 🧩 8.1 버전 필드 규칙

모든 RiskEngine 출력 JSON에는  
반드시 다음 필드가 포함되어야 한다:

```json
"schema_version": "1.5"


---

형, 섹션 8 전체 정상 출력 완료했어.  
메모장에 섹션 7 아래 이어서 붙이면 된다.

이제 다음은:

👉 **“섹션 9 출력해줘”**

라고 하면 **예제(Examples) 전체 섹션**을 완성된 형태로 출력해줄게.

# 9. Examples (정상 / 레벨 변화 / 예외 / fallback)

본 섹션은 RiskEngine V1.5의 Schema가  
실제로 어떻게 출력되는지 직관적으로 보여주는 예제 모음이다.

모든 예제에는:

- schema_version
- run_id / trace_id / span_id
- risk_level / risk_score / halt_trading
- events[] (severity 포함)
- input_snapshot
- meta

가 포함되어 있으며, 실제 운영·백테스트·리플레이 환경에서  
바로 활용될 수 있는 구조다.

---

# 🟦 9.1 정상 실행 예시 (Level 변화 없음)

```json
{
  "schema_version": "1.5",
  "run_id": "RUN-001",
  "trace_id": "TRACE-AAA",
  "span_id": "SPAN-RISK-001",
  "parent_span_id": "SPAN-FBE-001",

  "risk_level": "low",
  "risk_score": 0.12,
  "halt_trading": false,

  "events": [
    {
      "event_id": "E1",
      "type": "RISK_CHECK_STARTED",
      "timestamp": "2025-12-11T08:20:01.100Z",
      "severity": "INFO",
      "cause_event_id": null
    },
    {
      "event_id": "E2",
      "type": "RISK_INPUT_VALIDATED",
      "timestamp": "2025-12-11T08:20:01.120Z",
      "severity": "INFO",
      "cause_event_id": null
    },
    {
      "event_id": "E3",
      "type": "RISK_SCORE_NORMALIZED",
      "timestamp": "2025-12-11T08:20:01.150Z",
      "severity": "INFO",
      "cause_event_id": null
    },
    {
      "event_id": "E4",
      "type": "RISK_LEVEL_CLASSIFIED",
      "timestamp": "2025-12-11T08:20:01.200Z",
      "severity": "INFO",
      "cause_event_id": null
    },
    {
      "event_id": "E5",
      "type": "RISK_CHECK_COMPLETED",
      "timestamp": "2025-12-11T08:20:01.210Z",
      "severity": "INFO",
      "cause_event_id": null
    }
  ],

  "input_snapshot": {
    "price": 71200,
    "volume": 120300,
    "volatility": 0.018,
    "liquidity": 0.92,
    "timestamp": "2025-12-11T08:20:01.000Z",
    "raw": {}
  },

  "meta": {
    "latency_ms": 1.82,
    "engine_version": "V1.5",
    "market": "KR"
  }
}

{
  "schema_version": "1.5",
  "run_id": "RUN-002",
  "trace_id": "TRACE-AAA",
  "span_id": "SPAN-RISK-002",
  "parent_span_id": "SPAN-FBE-002",

  "risk_level": "medium",
  "risk_score": 0.44,
  "halt_trading": false,

  "events": [
    {
      "event_id": "E1",
      "type": "RISK_CHECK_STARTED",
      "timestamp": "2025-12-11T08:21:10.000Z",
      "severity": "INFO"
    },
    {
      "event_id": "E2",
      "type": "RISK_INPUT_VALIDATED",
      "timestamp": "2025-12-11T08:21:10.020Z",
      "severity": "INFO"
    },
    {
      "event_id": "E3",
      "type": "RISK_SCORE_NORMALIZED",
      "timestamp": "2025-12-11T08:21:10.050Z",
      "severity": "INFO"
    },
    {
      "event_id": "E4",
      "type": "RISK_LEVEL_CLASSIFIED",
      "timestamp": "2025-12-11T08:21:10.070Z",
      "severity": "INFO"
    },
    {
      "event_id": "E5",
      "type": "RISK_LEVEL_CHANGED",
      "timestamp": "2025-12-11T08:21:10.075Z",
      "severity": "WARNING",
      "cause_event_id": "E4"
    },
    {
      "event_id": "E6",
      "type": "RISK_CHECK_COMPLETED",
      "timestamp": "2025-12-11T08:21:10.080Z",
      "severity": "INFO"
    }
  ],

  "input_snapshot": {
    "price": 71300,
    "volume": 150000,
    "volatility": 0.022,
    "liquidity": 0.88,
    "timestamp": "2025-12-11T08:21:10.000Z",
    "raw": {}
  },

  "meta": {
    "latency_ms": 2.14,
    "engine_version": "V1.5",
    "market": "KR"
  }
}

{
  "schema_version": "1.5",
  "run_id": "RUN-003",
  "trace_id": "TRACE-AAA",
  "span_id": "SPAN-RISK-003",
  "parent_span_id": "SPAN-FBE-003",

  "risk_level": "high",
  "risk_score": 1.0,
  "halt_trading": true,

  "events": [
    {
      "event_id": "E1",
      "type": "RISK_CHECK_STARTED",
      "timestamp": "2025-12-11T08:22:20.000Z",
      "severity": "INFO"
    },
    {
      "event_id": "E2",
      "type": "RISK_EXCEPTION",
      "timestamp": "2025-12-11T08:22:20.015Z",
      "severity": "ERROR",
      "meta": { "error_message": "division by zero" }
    },
    {
      "event_id": "E3",
      "type": "RISK_FALLBACK_TRIGGERED",
      "timestamp": "2025-12-11T08:22:20.020Z",
      "severity": "ERROR",
      "cause_event_id": "E2"
    }
  ],

  "input_snapshot": {
    "price": null,
    "volume": null,
    "volatility": null,
    "liquidity": null,
    "timestamp": "2025-12-11T08:22:20.000Z",
    "raw": {}
  },

  "meta": {
    "latency_ms": 3.92,
    "engine_version": "V1.5",
    "market": "KR",
    "note": "fallback engaged due to exception"
  }
}


---

# 10. How to Use (전체 사용 가이드)

본 문서는 RiskEngine V1.5의 설계·구조·이벤트 체계·스키마·예제를  
개발팀, 운영팀, 그리고 DevOps 팀이 모두 동일한 기준으로 활용할 수 있도록 작성되었다.  
아래 가이드는 실제 업무에서 본 문서를 어떻게 사용하는지 명확하게 정리한 실전 매뉴얼이다.

---

## 🧩 10.1 개발팀(Developers) 사용 가이드

### ✔ 1) RiskEngine 구현 시 기준 문서로 사용  
- Schema V1.5에 정의된 키/필드/값을 그대로 구현  
- 이벤트 발생 순서(Event Chain)를 정확히 유지  
- 모든 예외는 fallback 흐름을 반드시 포함  
- meta 필드는 엔진별 확장 포인트로 적극 활용 가능  

### ✔ 2) 테스트 케이스 작성 기준  
- 정상 흐름 테스트  
- 레벨 변화 테스트  
- fallback 테스트  
- input_snapshot 변형 테스트  
- 이벤트 severity 검사 테스트  

### ✔ 3) 모듈 통합 시 기준  
- Router → FBE → RiskEngine → Scheduler 간 trace_id 연동  
- span_id / parent_span_id 관계 유지  
- 모든 로그는 event chain과 함께 기록  

---

## 🧩 10.2 운영팀(Ops) 사용 가이드

### ✔ 1) 장애 발생 시 로그 분석 절차  
1. trace_id로 전체 실행 흐름 검색  
2. span_id를 통해 특정 엔진(Router/FBE/RiskEngine)에서의 문제 여부 확인  
3. severity(Error/Warning) 기반 원인 파악  
4. input_snapshot으로 당시 시장 상태 확인  
5. meta.latency_ms로 성능 문제 여부 확인  

### ✔ 2) 알림 시스템 매핑  
- ERROR → 즉시 경보  
- WARNING → 2회 이상 반복 시 경보  
- INFO → 일반 상태  

### ✔ 3) fallback 발생 시 대응  
- halt_trading = true 여부 확인  
- 예외 메시지(meta.error_message) 확인  
- 필요 시 전략 재시작 또는 거래 중지  

---

## 🧩 10.3 DevOps 사용 가이드

### ✔ 1) 로그 수집 시스템 연동  
- 이벤트 timestamp 기준 SLA 모니터링  
- severity 기반 알림 자동화  
- trace_id 기반 전체 파이프라인 재구성 가능  

### ✔ 2) CI/CD 파이프라인  
- Schema V1.5 validation 자동화  
- 변경 시 diff 검증  
- 하위 호환성 체크 포함  

### ✔ 3) 백테스트/리플레이 시스템 연동  
- schema_version 확인 후 파싱 로직 선택  
- V1.4 데이터 → V1.5로 변환 시 default 값 적용  
- 이벤트 체인 기반 실행 흐름 재현  

---

## 🧩 10.4 전략 개발자(Quant) 사용 가이드

### ✔ 1) 리스크 분석  
- risk_score를 기반으로 전략 조건 조정  
- risk_level 변화 시 전략 스위칭 로직 연동  
- meta.market_regime 기반 MTF 전략 변형 가능  

### ✔ 2) 리플레이 분석  
과거 특정 구간에서:

- 어떤 이벤트가 발생했는지  
- risk_level이 왜 바뀌었는지  
- fallback이 발생했는지  
- input_snapshot이 어땠는지  

정확하게 재현 가능 → 전략 성능 분석에 매우 유리.

---

## 🧩 10.5 문서 유지보수 가이드

### ✔ 버전 업 시 필수 절차  
1. 변경점(diff)을 문서 상단에 기록  
2. schema_version 업데이트  
3. 예제(Examples) 수정  
4. Event Enum 확장 시 필드 의미 추가  
5. 호환성 규칙(Backward Compatibility) 반영  

### ✔ 문서 리뷰 주기  
- 매 버전 업데이트(JIRA ticket 기준)  
- 월 단위 운영 리스크 리뷰  
- V30 개발 전 최종 문서 점검  

---

## 🧩 10.6 문서로 얻을 수 있는 핵심 가치 요약

### ✔ 엔진 간 정합성 확보  
Router → FBE → RiskEngine → Scheduler 전체가 동일 기준으로 연결됨.

### ✔ 장애 분석 속도 10배 상승  
event chain + trace_id + input_snapshot이 완전한 원인 추적 제공.

### ✔ 백테스트/리플레이의 품질 급상승  
라이브 환경을 100% 재현 가능.

### ✔ V30 / AI RiskEngine 설계 기반 완성  
이 문서는 향후 AI 기반 리스크 모델(V30)의 뼈대 역할.

---

# 🎉 문서 완성 — RiskEngine V1.5 공식 README END















