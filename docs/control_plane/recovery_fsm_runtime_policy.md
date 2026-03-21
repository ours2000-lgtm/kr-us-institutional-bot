# Recovery FSM & PositionManager Runtime Policy (FINAL v1.1)

## 1. 목적

이 문서는 다음을 정의한다:

* RecoveryFSM 상태 전이 규칙
* 상태별 주문/체결 처리 정책
* PositionManager의 recovery 연동 동작
* Runtime 보호 정책 (계좌 보호 핵심 로직)

---

## 2. 상태 정의

| 상태            | 설명                    |
| ------------- | --------------------- |
| CONNECTED     | 연결 및 로그인 완료 (거래 보장 X) |
| DISCONNECTED  | 연결 끊김 감지              |
| RECONNECTING  | 재연결 시도 중              |
| RECOVERING    | 계좌/포지션 복구 및 검증 중      |
| READY_PENDING | 복구 완료 후 안정화 대기 (쿨다운)  |
| READY         | 정상 거래 가능 상태           |
| EXIT_ONLY     | 신규 진입 금지, 청산만 허용      |
| BLOCKED       | 치명적 오류 상태 (수동 개입 필요)  |

---

## 3. 상태 전이

| From          | Event                    | To            | 조건       |
| ------------- | ------------------------ | ------------- | -------- |
| CONNECTED     | disconnect_detected      | DISCONNECTED  | 즉시       |
| DISCONNECTED  | reconnect_start          | RECONNECTING  | 자동       |
| RECONNECTING  | login_success            | RECOVERING    | 로그인 성공   |
| RECOVERING    | snapshot_ok              | READY_PENDING | 검증 통과    |
| RECOVERING    | snapshot_failed          | BLOCKED       | 스냅샷 실패   |
| RECOVERING    | mismatch_critical        | BLOCKED       | 치명적 불일치  |
| READY_PENDING | cooldown_elapsed         | READY         | 일정 시간 경과 |
| READY         | risk_exit_only_triggered | EXIT_ONLY     | 리스크 트리거  |
| EXIT_ONLY     | risk_cleared             | READY         | 리스크 해제   |
| ANY           | critical_error           | BLOCKED       | 즉시       |

---

## 4. 이벤트 상수

```python
EVENT_DISCONNECT_DETECTED = "disconnect_detected"
EVENT_RECONNECT_START = "reconnect_start"
EVENT_LOGIN_SUCCESS = "login_success"
EVENT_SNAPSHOT_OK = "snapshot_ok"
EVENT_SNAPSHOT_FAILED = "snapshot_failed"
EVENT_MISMATCH_CRITICAL = "mismatch_critical"
EVENT_COOLDOWN_ELAPSED = "cooldown_elapsed"
EVENT_RISK_EXIT_ONLY_TRIGGERED = "risk_exit_only_triggered"
EVENT_RISK_CLEARED = "risk_cleared"
EVENT_CRITICAL_ERROR = "critical_error"
EVENT_MANUAL_BLOCK = "manual_block"
```

---

## 5. 상태별 정책 (핵심)

| 상태            | BUY 주문 | SELL 주문 | BUY fill | SELL fill   |
| ------------- | ------ | ------- | -------- | ----------- |
| CONNECTED     | ❌      | ❌       | ❌        | ❌           |
| DISCONNECTED  | ❌      | ❌       | ❌        | ❌           |
| RECONNECTING  | ❌      | ❌       | ❌        | ❌           |
| RECOVERING    | ❌      | ❌       | ❌        | ✅ (포지션 감소만) |
| READY_PENDING | ❌      | ❌       | ❌        | ✅           |
| READY         | ✅      | ✅       | ✅        | ✅           |
| EXIT_ONLY     | ❌      | ✅       | ❌        | ✅           |
| BLOCKED       | ❌      | ❌       | ❌        | ❌           |

---

### 📌 보충 설명 (중요)

```text
READY_PENDING에서는 신규 BUY/SELL 주문 모두 차단한다.
다만, 이미 발생한 late SELL fill은 포지션 정합성 유지를 위해 반영한다.
```

👉 즉:

* 주문(order) = 차단
* 체결(fill) = 일부 허용

---

## 6. PositionManager 정책

### 핵심 규칙

#### BUY fill 허용 조건

```text
state == READY 인 경우에만 허용
```

---

#### BUY fill 차단 상태

```text
RECOVERING
READY_PENDING
EXIT_ONLY
BLOCKED
```

---

#### SELL fill 허용 조건

```text
기존 포지션 감소 방향일 때만 허용
```

---

#### SELL fill 차단 조건

```text
포지션 없음
초과 수량 SELL
```

---

## 7. Recovery 동작

### snapshot replace

* broker snapshot = source-of-truth
* 내부 포지션 전체 교체

---

### late fill 처리

| 상태            | 처리       |
| ------------- | -------- |
| RECOVERING    | SELL만 반영 |
| READY_PENDING | SELL만 반영 |
| READY         | 정상 반영    |

---

## 8. Lock 정책

* 내부 상태는 `_positions`로 보호
* 외부 접근은 snapshot API만 허용

```text
get_position() → deprecated
snapshot() → 권장
```

---

## 9. 위험 차단 철학 (핵심)

### FAIL-CLOSED

* 애매하면 막는다
* recovery 중 신규 진입 금지
* 상태 확정 전 거래 금지

---

## 10. 테스트 검증 범위

### FSM

* invalid transition 차단
* invalid event 차단
* ANY → BLOCKED 보장

---

### PositionManager

* RECOVERING에서 BUY 차단
* READY_PENDING에서 BUY 차단
* READY에서 BUY 허용
* SELL은 포지션 감소 방향만 허용

---

### Runtime Flow

```text
RECOVERING → READY_PENDING → READY

BUY: ❌ → ❌ → ✅
SELL: ✅ → ✅ → ✅
```

---

## 11. 설계 메모 (중요)

현재 정책 기준:

```text
BUY fill 허용 상태 = {READY}
BUY fill 차단 상태 = {RECOVERING, READY_PENDING, EXIT_ONLY, BLOCKED}
```

👉 따라서 구현 레벨에서는:

```text
_is_recovering() 보다
_is_buy_fill_blocked_state() 개념이 더 정확하다
```

---

## 12. 결론

이 시스템은 다음을 보장한다:

* 계좌 손상 방지 (fail-closed)
* 복구 중 진입 차단
* 상태 기반 거래 제어
* 테스트 기반 정책 검증 완료

---

END OF DOCUMENT
