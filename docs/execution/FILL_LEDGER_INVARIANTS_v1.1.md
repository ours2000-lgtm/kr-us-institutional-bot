# FILL_LEDGER_INVARIANTS_v1.1

## 1. Purpose

본 문서는 Chejan 기반 체결 이벤트 처리에서
**Fill Ledger를 단일 진실 원천(SSOT)**으로 정의하고,
재현성(Determinism), 무결성(Integrity), 순서 보존(Ordering)을 보장하기 위한 불변식을 규정한다.

---

## 2. Definitions

* **Fill Event**: CONFIRMED 상태로 분류된 체결 이벤트
* **Ledger**: append-only JSONL 기반 체결 기록 저장소
* **Index (idx)**: idempotency key 중복 방지를 위한 캐시
* **Restore**: ledger를 기반으로 position 상태를 재구성하는 과정
* **Replay**: ledger 이벤트를 순차적으로 적용하는 과정

---

## 3. SSOT Principle

> Ledger는 체결 이벤트의 단일 진실 원천이며,
> 모든 position 상태는 ledger replay 결과로만 정의된다.

---

## 4. Invariants

### Invariant 1 — Confirmed Only

CONFIRMED 상태의 fill만 ledger에 append된다.

---

### Invariant 2 — Ledger → Position

Position 상태는 ledger에 기록된 fill만을 기반으로 계산된다.

---

### Invariant 3 — Idempotency

동일 idempotency key를 가지는 fill은 한 번만 반영된다.

---

### Invariant 4 — Index is Cache

Index(idx)는 중복 방지를 위한 캐시이며,
복원(restore)의 SSOT는 항상 ledger이다.

---

### Invariant 5 — Restore Determinism

동일한 ledger 데이터와 동일한 적용 순서가 주어지면,
복원된 position 상태는 항상 동일해야 한다.

---

### Invariant 6 — Ordering Preservation

Ledger는 append-only ordered event log이며,
restore 및 replay는 ledger 기록 순서를 반드시 보존해야 한다.

---

## 5. Ordering Rule

Ledger 적용 순서는 다음 기준을 따른다:

> JSONL 파일의 append 순서(파일 기록 순서)가 절대 기준이다.

* restore 시 재정렬 금지
* timestamp 기준 재정렬 금지
* ingestion 순서를 변경하는 모든 처리 금지

---

## 6. Ordering Edge Cases

* 동일 `order_no`와 `fill_time`을 가진 여러 레코드는
  **ingestion 순서 그대로 적용하며 재정렬하지 않는다.**

* partial fill이 동일 timestamp로 여러 번 들어오는 경우에도
  **ledger append 순서를 그대로 유지한다.**

* 여러 ledger 파일을 restore할 경우:

  * 파일은 **날짜 오름차순**으로 처리한다.
  * 각 파일 내부는 **append 순서 유지**한다.

---

## 7. Restore Rule

Restore는 다음 절차를 따른다:

1. ledger 파일을 처음부터 끝까지 순차적으로 읽는다.
2. 각 레코드를 기록 순서대로 replay한다.
3. position 상태를 누적 계산한다.

---

## 8. Deterministic Replay

Restore는 다음 조건을 만족해야 한다:

* 동일 ledger 입력 → 동일 position 결과
* side-effect 없음
* 외부 상태 의존 없음
* floating precision drift 없음 (Decimal 사용 권장)

---

## 9. Idempotency Rule

Idempotency key는 다음 필드 조합으로 생성된다:

account_id | symbol | order_no | side | fill_time | fill_qty | fill_price

### 규칙

* 동일 key → duplicate → 무시
* 신규 key → ledger append → position 반영

### 생성 규칙

* key 생성 함수는 **순수 함수(pure function)** 여야 한다
* 모든 입력 값은 **normalize된 canonical 값**을 사용해야 한다
* raw payload 값 직접 사용 금지
* key 생성 규칙이 변경되면:
  → **schema_version 반드시 증가**

---

## 10. Ledger Schema

각 ledger 레코드는 다음 필드를 포함한다:

### 필수 필드

* `schema_version`
* `idempotency_key`
* `account_id`
* `symbol`
* `order_no`
* `side`
* `fill_qty`
* `fill_price`
* `fill_time`

### 권장 필드

* `exchange`
* `currency`
* `instrument_type`
* `source` (chejan / restore 등)
* `ingested_at`

### 감사/디버깅 필드 (선택)

* `raw_payload_hash`
* `source_system`
* `chejan_seq_no`

### 주의

> 메타 필드는 SSOT 재현 및 position 계산에는 영향을 주지 않는다.

---

## 11. Restore Failure Policy

### 기본 모드: STRICT (권장)

다음 조건 발생 시:

* 레코드 파싱 실패
* 필수 필드 누락
* schema 불일치

→ **restore 즉시 중단**
→ **에러 로그 + 알람 발생**
→ **트레이딩 시작 차단**

---

### 예외 모드: LENIENT (수동 전용)

* invalid 레코드 skip
* 에러 로그 기록

> LENIENT 모드는 운영 기본이 아니며,
> 디버깅 또는 수동 복구 시에만 사용한다.

---

## 12. Position Model Consistency

> engine position, reconciliation position, risk engine position 계산은
> 동일한 ledger replay semantics를 공유해야 한다.

가능하면:

> 동일한 `position_from_ledger()` 구현을 사용한다.

---

## 13. Pipeline Rule

체결 처리 파이프라인:

Chejan
→ State Classification (PENDING / CONFIRMED / IGNORED)
→ CONFIRMED만 통과
→ Idempotency Check
→ Ledger Append
→ Position Update

---

## 14. Critical Safety Rule

다음 조건은 반드시 만족해야 한다:

* ledger 없이 position 계산 금지
* CONFIRMED 외 이벤트 반영 금지
* 중복 fill 반영 금지
* 순서 변경 금지

---

## 15. One-line SSOT

> Ledger는 append-only ordered event log이며,
> CONFIRMED fill만 기록되고,
> 동일 key는 한 번만 반영되며,
> restore는 기록 순서를 유지한 deterministic replay로 수행된다.

---
