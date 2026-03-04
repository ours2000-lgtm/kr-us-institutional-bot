# US_DERIVATION_CHECKLIST_v1.md

Status: ACTIVE (v1.0)  
Owner: OPS  
Review Cycle: Annual or upon Annex A revision  
Next Review Date: 2027-01-31  

---

## 0. Purpose & Scope

본 문서는 **KR Canonical OPS Contract v1.0의 Annex A(A1~A5)** 조항을  
**US 환경에서 FAIL-CLOSED로 준수하는지 검증하기 위한 실행 체크리스트(runbook)**이다.

- 본 문서는 **Annex A를 수정하지 않는다**
- Annex A는 Canonical(법전) 기준이며, 본 문서는 **US 파생 환경에서의 적용·검증 절차**만을 정의한다
- Annex A A6(CI/빌드/운영 Enforcement 조건)는 본 문서의 리허설 시나리오로 반영된다

Canonical Reference:  
- `../canonical/KR_Canonical_OPS_Contract_v1.0.md#annex-a`

---

## 1. KR → US 치환표

### 1.1 MarketProfile 치환

| 항목 | KR | US |
|----|----|----|
| market_tag | KR | US |
| market | KR | US |
| tz | Asia/Seoul | America/New_York |
| holiday_calendar | KR_CAL | US_FUT_CAL |
| risk.profile | kr-default | us-default |
| latency_profile_version | kr-latency-v1 | us-latency-v1 |
| max_clock_drift_ms | 100 | 50 |

**Notes**
- LOCK 대상 필드는 Annex A A1/A2/A5를 따른다
- 본 표는 **치환 허용 필드만** 다룬다
- `us-latency-v1`은 US 마켓용 soft/hard latency 번들이며, Annex A A5 기준을 번들 단위로 관리한다
- Stale 계산은 UTC 기준이며, DST는 Annex A A2.3에 따라 무시된다
- `max_clock_drift_ms`는 Annex A A2.3을 US 환경에서 더 엄격히 적용한 값이다

---

### 1.2 Engine Identity 치환

| 항목 | KR | US |
|----|----|----|
| engine_id | KR-V9-PLUS | US-V9-PLUS |
| schema_version | 1.0 | 1.0 |
| run_id | UUID | UUID |

**Notes**
- `schema_version`은 Annex A A1.3(Semantic Versioning) LOCK 대상이다
- `run_id`는 Annex A 직접 LOCK 필드는 아니나,  
  **Evidence 추적·리허설 재현·운영 감사에서 필수 키**로 취급된다
- `run_id` 중복 또는 재사용 시 **FAIL-CLOSED 또는 부팅 거부**가 발생할 수 있다

---

### 1.3 Path & Artifact 규칙

| 항목 | KR | US |
|----|----|----|
| runtime | `{ROOT}/runtime/KR/{engine_id}/` | `{ROOT}/runtime/US/{engine_id}/` |
| logs | `{ROOT}/logs/KR/{engine_id}/` | `{ROOT}/logs/US/{engine_id}/` |
| evidence | `{ROOT}/logs/KR/{engine_id}/evidence/` | `{ROOT}/logs/US/{engine_id}/evidence/` |
| PID_JSON | kr_engine.json | us_engine.json |
| STOP_FLAG | kr_stop.flag | us_stop.flag |

**Rules**
- PID_JSON 내부 `market_tag`, `engine_id` 값은 경로상의 `{market_tag}/{engine_id}`와 일치해야 한다
- 불일치 시 Annex A A3.2에 따라 **FAIL-CLOSED**
- Evidence 디렉터리는 Annex A A3 Path 규칙과 동일한 구조를 따른다
- Cross-market write 방지를 위해 **OS-level 권한 분리**가 적용되어야 한다

---

### 1.4 Entry Point & CLI / ENV

**Example**
```bash
python run_us_v9_plus.py \
  --market US \
  --config ./config/us_profile.json \
  --pid_json ./runtime/US/US-V9-PLUS/us_engine.json \
  --no-order true
ENV Example

MARKET_TAG=US
NO_ORDER_MODE=true
Rules

CLI --market == ENV[MARKET_TAG] == PID_JSON.market_tag 삼중 일치 필수

ENV[MARKET_TAG] 미정의 시 기본값 없음 → FAIL-CLOSED

NO-ORDER 모드에서는 실 브로커 네트워크 호출이 반드시 차단되어야 하며,
위반 시 FAIL-CLOSED

2. Dry-run / FAIL-CLOSED 리허설
2.1 정적 검증 (CI)
 PID_JSON 스키마 검사 (필수 필드 존재 + 타입 일치)

 market_tag=US, engine_id=US-V9-PLUS, schema_version=1.0 확인

 ISO8601 + offset timestamp 형식 검증 (예: 2026-01-25T12:34:56Z)

 경로 패턴 위반 시 CI 빌드 실패 (Annex A A6)

2.2 Time Synchronization & Drift
 NTP/PTP 상태 = synchronized

 Local clock drift ≤ MarketProfile.max_clock_drift_ms

 MarketProfile.tz와 OS timezone 일치

Rules

NTP/PTP 상태가 unsynchronized 또는 unknown인 경우
Annex A A2.3에 따라 FAIL-CLOSED

2.3 Identity FAIL-CLOSED
시나리오	기대 결과
market_tag 불일치	FAIL-CLOSED
engine_id 불일치	FAIL-CLOSED
schema_version mismatch	부팅 거부
run_id 중복	FAIL-CLOSED
2.4 Lifecycle / Zombie / Resource Hard-Limit
 INIT → RUN → STOPPING → STOPPED 상태 전이 로그 확인

 STOP_FLAG 감지 후 N초 이내 종료

 종료 지연 시 SIGKILL + ExitCode 기록

 Orphan / Zombie 프로세스 탐지 및 강제 종료 검증

 Memory > 90% → FAIL-CLOSED

 CPU > max_cpu (30초 지속) → DEGRADED 또는 FAIL-CLOSED

 Disk usage ≥ 95% → Order Gate 차단

2.5 Network Latency (Annex A A5)
시나리오	기대 결과
RTT < soft_warn	정상
soft_warn 초과	경고 + Evidence
hard_fail 초과	FAIL-CLOSED
Notes

soft_warn_ms / hard_fail_ms는 latency_profile_version 내 정의값 사용

임계값은 코드에 하드코딩되어서는 안 된다

각 시나리오는 scenario_id를 Evidence에 기록한다

2.6 Order Gate (Kill-Switch)
 MarketProfile / PID_JSON / CLI market 삼중 일치 검증

 Mock Order market_tag 변조(KR) → 송출 차단

 Sequence mismatch / duplicate order 감지 → FAIL-CLOSED

Rules

Order Gate 테스트는 매 릴리스 CI에서 자동 실행

실패 시 배포 차단

3. Evidence Requirements
Required Fields
market_tag

engine_id

schema_version

run_id

sequence_no

timestamp_utc

event_type / phase

latency_profile_version

scenario_id

event_type 예시

INIT

BOOT

LATENCY_SOFT_WARN

LATENCY_HARD_FAIL

ORDER_GATE_BLOCK

ZOMBIE_KILL

Integrity
Evidence 파일 전체에 대한 sha256_checksum
또는 각 이벤트별 event_hash 포함

Atomic write 적용 (.tmp → rename)

Storage
{ROOT}/logs/US/US-V9-PLUS/evidence/*.json

ci_, rehearsal_, live_ 태그는 Annex A A6 단계와 직접 매핑된다

Sequence Policy
sequence_no는 run_id 내부에서 0부터 단조 증가

감사 식별자는 (run_id, sequence_no) 조합을 사용한다

4. Notes
본 문서는 Annex A A1~A5에 직접 매핑되는 US 파생 실행 런북이다

Annex A A6의 CI/빌드 Enforcement 조건은 본 문서의 리허설 시나리오로 반영된다

Canonical 변경이 필요한 경우 Annex A 개정 절차(v2.0+)를 따른다

운영 중 발견된 갭은 **US_DERIVATION_CHECKLIST_v{n+1}**로만 반영하며,
Annex A 내용은 직접 수정하지 않는다