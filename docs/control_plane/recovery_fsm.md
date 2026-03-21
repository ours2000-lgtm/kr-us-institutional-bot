# path: docs/control_plane/recovery_fsm.md

# Recovery FSM Specification (V40 FINAL)

---

## 1. 목적

Recovery FSM은 다음을 보장한다:

- 브로커 연결 장애 및 복구 과정에서 **계좌 상태 오염 방지**
- 복구 중 신규 진입 차단 (fail-safe)
- snapshot 기반 상태 재구성 (source-of-truth)
- 시스템이 **fail-closed**로 동작하도록 강제

---

## 2. 상태 정의

| 상태 | 설명 |
|------|------|
| CONNECTED | 정상 연결 상태 (로그인 + 실시간 등록 완료) |
| DISCONNECTED | 연결 끊김 감지, 즉시 위험 상태 |
| RECONNECTING | 자동 재연결 시도 중 |
| RECOVERING | 재로그인 성공, snapshot/reconciliation 진행 중 |
| READY_PENDING | 복구 직후 안정화 대기 구간 |
| READY | 정상 거래 가능 상태 |
| EXIT_ONLY | 신규 진입 금지, 청산만 허용 |
| BLOCKED | 심각한 오류로 전체 거래 차단 |

---

## 3. 핵심 철학

> 로그인 성공은 세션 복구일 뿐, 상태 무결성 복구가 아니다.

- 복구는 반드시 **snapshot + reconciliation 검증 통과 후** 완료
- RECOVERING 동안은 **절대 신규 진입 금지**
- 시스템은 항상 **fail-closed 우선**

---

## 4. 상태 전이

### 4.1 상태 전이표

| From | Event | To | 조건 |
|------|-------|----|------|
| CONNECTED | disconnect_detected | DISCONNECTED | 연결 끊김 감지 즉시 |
| DISCONNECTED | reconnect_start | RECONNECTING | 자동 재연결 시작 |
| RECONNECTING | login_success | RECOVERING | 로그인 성공 |
| RECONNECTING | reconnect_failed | BLOCKED | 재연결 실패 정책 충족 시 |
| RECOVERING | snapshot_ok | READY_PENDING | snapshot replace + reconciliation 통과 |
| RECOVERING | snapshot_failed | BLOCKED | snapshot 실패 |
| RECOVERING | mismatch_critical | BLOCKED | 수량/평균가 등 치명적 불일치 |
| READY_PENDING | cooldown_elapsed | READY | N초 경과 + 추가 이상 없음 |
| READY | risk_exit_only_triggered | EXIT_ONLY | 계좌/전략/운영 리스크 트리거 |
| EXIT_ONLY | risk_cleared | READY | 해제 조건 충족 시 |
| ANY | critical_error | BLOCKED | 치명적 오류 즉시 |
| ANY | manual_block | BLOCKED | 운영자 수동 차단 |

---

### 4.2 전이 원칙

- 정의되지 않은 상태 전이는 모두 금지 (fail-closed)
- 상태는 반드시 **허용된 전이만 가능**
- BLOCKED는 모든 상태보다 우선하는 보호 상태
- 상태 전이는 반드시 **이벤트 기반으로만 발생**

---

### 4.3 복구 전이 강제 규칙
