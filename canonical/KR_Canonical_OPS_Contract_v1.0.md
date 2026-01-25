# Annex A — KR Canonical OPS Contract v1.0

> **Status:** LOCKED (Canonical)
>
> 본 Annex는 KR Canonical OPS Contract v1.0의 **요구사항 베이스라인**이며,
> 명시된 LOCK 해제 또는 개정 절차 없이는 변경될 수 없다.

---

## A0. Scope & Priority

* 본 Annex는 **Launcher / Stopper / Engine Runtime Contract**의 공통 규약을 정의한다.
* KR Canonical은 모든 파생 마켓(US, CRYPTO 등)에 대해 **최우선 기준**이다.
* 파생 마켓 구현이 본 Annex와 충돌할 경우, **파생 구현을 수정**해야 하며,
  Canonical 변경이 필요할 경우 **v2.0 이상 개정 절차**를 선행해야 한다.

---

## A1. Identity Locks (필수 식별 계약)

### A1.1 `market_tag` (LOCK)

* PID_JSON 루트에 `market_tag`는 **필수**이다.
* 허용 enum: `KR | US | CRYPTO | <future>`
* **새 enum 추가는 Annex 개정 없이는 불가**하다.

**검증 규칙 (FAIL-CLOSED):**

* 엔진 부팅 직후 1회 검증
* 주문 직전 또는 세션 오픈 시 1회 재검증
* `MarketProfile.market != PID_JSON.market_tag` → 즉시 FAIL-CLOSED

런처는 PID_JSON 생성 시 `market_tag`를 기록해야 하며,
로그 첫 줄에도 `market=KR` 형태로 **선언적으로 출력**해야 한다.

---

### A1.2 `engine_id` (LOCK)

* PID_JSON, Launcher log, Engine log에 **반드시 포함**되어야 한다.
* 엔진 로그의 **첫 부팅 라인**에 `engine_id`와 `market_tag`를 MUST 출력.

**Evidence 인덱스 최소 키:**

* `(engine_id, market_tag, schema_version, timestamp_utc)`

---

### A1.3 `schema_version` (LOCK)

* PID_JSON 루트에 `schema_version`은 **필수**이다.
* Semantic Versioning 원칙을 따른다.

**검증 규칙:**

* Major mismatch → FAIL-CLOSED
* Minor mismatch 허용 여부는 별도 정책으로 정의

---

### A1.4 `run_id` (LOCK)

* PID_JSON에 `run_id` 필드를 **필수**로 포함한다.
* 값은 UUID 또는 부팅 시각 기반 고유 식별자여야 한다.

**목적:**

* 동일 `engine_id`의 재시작 간 로그/증빙 혼선 방지
* Evidence Catalog에서 **실행 단위 필터링** 보장

---

## A2. Time Contract Lock

### A2.1 Timestamp Format

* 모든 계약용 timestamp는 **ISO8601 + offset** 형식으로 기록한다.

  * 예: `2026-01-25T12:34:56+00:00`
  * `Z`는 `+00:00`과 동치로 허용

* offset 누락 시 → **FAIL-CLOSED**

---

### A2.2 Human-readable Time

* KST/ET 등 로컬 시각 표기는 **사람용 로그에만 허용**한다.
* PID_JSON 및 Evidence 필드에는 UTC(+offset)만 허용한다.

---

### A2.3 Stale Calculation

* `stale = now_utc - started_utc` 기준으로만 계산한다.
* DST, 로컬 타임존 변경은 stale 계산에 영향을 주지 않는다.
* 서버 시스템 시간 오차는 **별도 모니터링 책임**으로 둔다.

---

## A3. Artifact Lifecycle Lock

### A3.1 Directory Isolation

모든 런타임 아티팩트는 아래 구조를 따른다:

```
{ROOT}/runtime/{env}/{market_tag}/{engine_id}/...
{ROOT}/logs/{env}/{market_tag}/{engine_id}/...
```

* `{env}`는 `prod | stg` 등으로 확장 가능
* 경로상의 `market_tag`, `engine_id`는 PID_JSON 값과 **반드시 일치**해야 한다.

불일치 시 → FAIL-CLOSED

---

### A3.2 No Cross-write Rule

* 엔진은 **자기 market/engine 디렉터리 외 쓰기 금지**
* CI 단계에서 경로 패턴 lint 수행
* 위반 시 → **빌드 실패**

---

## A4. Heartbeat Contract

### A4.1 Heartbeat Fields (LOCK)

PID_JSON 필수 필드:

* `last_heartbeat_utc`
* `current_state` : `INIT | RUN | STOPPING | STOPPED`
* `heartbeat_interval_ms`

권장:

* `heartbeat_interval_ms <= 60000`

---

### A4.2 Drift Handling

* Heartbeat drift 발생 시 단계적 처리 가능:

  * 1단계: WARN (Evidence 기록)
  * 2단계: FAIL-CLOSED (정책에 따라)

예: N회 연속 또는 M초 이상 지속 시 승격

---

### A4.3 Last Exit Metadata (LOCK)

* 종료 직전 PID_JSON에 다음 필드를 기록한다:

  * `last_exit_code`
  * `exit_reason`

목적:

* 로그 전수 조사 없이 종료 원인 즉시 식별

---

## A5. Latency Handling (특히 US)

### A5.1 Interface Invariance

* `SessionProvider` / `BrokerAdapter` 인터페이스는 마켓 간 **불변**이다.
* Health 상태는 공통 enum 사용:

  * `OK | DEGRADED | FAILED`

---

### A5.2 Profile-based Thresholds

* latency 임계값은 **MarketProfile 파라미터**로만 정의한다.
* 코드 경로는 enum 상태만을 기준으로 동작한다.

---

### A5.3 Latency Context (LOCK)

* `max_latency_hard_fail_ms` 판단 기준은:

  * **엔진 송신 시각 ↔ 브로커 수신 시각** 차이

목적:

* 엔진 내부 지연 vs 외부 네트워크 지연 구분
* 인프라/브로커 책임 분리 Evidence 확보

---

## A6. Evidence Auto-validation

CI / Smoke Test에서 다음을 자동 검증한다:

* `market_tag`, `engine_id`, `schema_version`, `run_id`가

  * PID_JSON
  * Launcher log
  * Engine log
    에 모두 존재하는지

* 엔진 부팅 시점에 PID_JSON 스냅샷을 Evidence로 저장한다.

  * 예: `{ROOT}/logs/{market_tag}/{engine_id}/evidence/`

---

## A7. Enforcement Level

* A1 ~ A5 위반 시:

  * **실행 금지 (FAIL-CLOSED)** 또는
  * **빌드/배포 차단 (MUST)**

* 본 Annex는 운영·감사·포렌식 기준 문서이며,
  예외는 허용되지 않는다.

---

**END OF ANNEX A (KR Canonical OPS Contract v1.0)**
