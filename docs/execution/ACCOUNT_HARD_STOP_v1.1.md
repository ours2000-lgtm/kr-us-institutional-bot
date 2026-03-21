# ACCOUNT_HARD_STOP_v1.1

## 1. Purpose

본 문서는 자동매매 시스템에서 계좌 단위 손실 확대를 방지하기 위해  
**Account-Level Hard Stop** 규칙을 정의한다.

Hard Stop은 전략 품질, 체결 품질, 시장 급변과 무관하게  
계좌가 일정 위험 상태에 도달하면 **모든 신규 주문을 강제 차단**하는  
최종 보호 장치이다.

---

## 2. Core Principle

> 계좌 보호는 전략 수익성보다 우선한다.

---

## 3. Design Principles

### 3.1 Fail-Closed
판단이 불확실하면 허용이 아니라 차단한다.

### 3.2 Latched Stop
한 번 Hard Stop이 발동되면 자동으로 해제되지 않는다.

### 3.3 Account-First
종목별 보호보다 계좌 전체 보호가 우선한다.

### 3.4 Deterministic
동일한 입력 상태는 항상 동일한 Hard Stop 결정을 생성해야 한다.

---

## 4. Scope and Unit Policy

본 버전(v1.1)에서 Hard Stop은 **절대 금액 기준 손실 한도**를 사용한다.

- `daily_realized_loss_limit_amount` 는 **KRW 기준 절대 금액**이다.
- 비율 기준 한도(예: Equity 대비 %)는 본 버전에서 지원하지 않는다.
- 퍼센트 기반 한도는 v2 확장 범위로 남긴다.

---

## 5. PnL Scope

본 Hard Stop은 **실현 손익(realized PnL)** 만을 기준으로 판단한다.

- 미실현 손익(unrealized PnL)은 본 버전에서 의도적으로 제외한다.
- 이는 ledger 기반 체결 SSOT 중심 설계를 유지하기 위함이다.
- unrealized 기반 리스크 관리는 별도 Risk Layer 또는 v2에서 다룬다.

---

## 6. Inputs

Hard Stop 판단에 사용하는 최소 입력은 다음과 같다.

- `daily_realized_pnl`
- `consecutive_losses`
- `orders_sent_today`
- `hard_stop_latched`

---

## 7. Trigger Rules

다음 조건 중 하나라도 만족하면 Hard Stop을 발동한다.

### Rule A — Daily Realized Loss Limit
`daily_realized_pnl <= -daily_realized_loss_limit_amount`

### Rule B — Max Consecutive Losses
`consecutive_losses >= max_consecutive_losses`

### Rule C — Max Orders Per Day
`orders_sent_today >= max_orders_per_day`

---

## 8. Initial Recommended Limits

초기 운영 기준 추천값:

- `daily_realized_loss_limit_amount = 100000`
- `max_consecutive_losses = 3`
- `max_orders_per_day = 20`

실운영 시 전략 특성에 맞게 조정 가능하다.

---

## 9. Consecutive Loss Definition

`consecutive_losses` 는 **트레이드 단위** 기준으로 계산한다.

트레이드는 다음과 같이 정의한다:

- 동일 symbol에서 **진입 → 완전 청산**까지를 1 트레이드로 본다.
- 해당 트레이드의 **최종 realized PnL이 음수**이면 `1 loss` 로 계산한다.
- 부분 청산(partial exit)은 독립적인 loss로 계산하지 않는다.
- 완전 청산 전까지는 동일 트레이드의 일부 상태로 간주한다.

---

## 10. Orders Sent Today Definition

`orders_sent_today` 는 **실제 계좌 리스크를 증가시키는 주문만** 포함한다.

### 포함
- 신규 진입 주문
- 포지션 증가 주문

### 제외
- 취소 주문 (Cancel)
- 정정 주문 (Modify/Correction)
- Reduce-only 청산 주문
- 리스크 축소만을 목적으로 하는 주문

초기 구현이 단순할 경우, 일단 모든 주문을 카운트하되  
향후 v1.2에서 위 정책으로 정교화할 수 있다.  
다만 운영 문서 기준 SSOT는 본 정의를 따른다.

---

## 11. State Model

### NORMAL
주문 가능 상태

### HARD_STOP_TRIGGERED
이번 평가에서 차단 조건을 충족한 상태

### HARD_STOP_LATCHED
차단이 고정된 상태

실제 운영에서는 `HARD_STOP_LATCHED` 상태가 핵심이다.

---

## 12. State Transition Rule

상태 전이는 다음 규칙을 따른다.

- `NORMAL` 상태에서 Rule A/B/C 중 하나라도 만족하면 즉시 `HARD_STOP_TRIGGERED` 로 전이된다.
- `HARD_STOP_TRIGGERED` 는 동일 평가 내에서 즉시 `HARD_STOP_LATCHED` 로 고정된다.
- `HARD_STOP_LATCHED` 상태에서는 어떠한 입력 변화에도 자동으로 `NORMAL` 로 복귀하지 않는다.
- `NORMAL` 복귀는 오직 Reset Policy에 의해 수동 또는 거래일 경계에서만 허용된다.

---

## 13. Latch Rule

Hard Stop이 발동되면:

- 신규 BUY 차단
- 신규 SELL 차단
- 재진입 차단

초기 버전에서는 **모든 신규 주문 차단**을 기본 정책으로 한다.

향후 확장 버전에서는 다음 예외를 둘 수 있다:

- reduce-only 청산 주문 허용
- 강제 리스크 축소 주문 허용

하지만 본 버전(v1.1)의 기본 정책은 **전면 차단**이다.

---

## 14. Reset Policy

### Same-Day
당일 Hard Stop은 당일 종료까지 유지한다.

### Next Trading Day
다음 거래일 시작 시 수동 또는 정책 기반 초기화를 허용할 수 있다.

초기 정책 권장:

> 당일 종료까지 유지, 다음 거래일에만 초기화 가능

---

## 15. Evaluation Timing

Hard Stop 평가는 최소 두 시점에서 수행한다.

### 15.1 BEFORE_SEND
주문 전송 직전

### 15.2 AFTER_FILL
체결 반영 직후

이중 평가를 통해:

- 손실 직후 다음 주문 차단
- 주문 전 마지막 차단
- 체결 기반 손실 반영 직후 즉시 래치

를 보장한다.

---

## 16. Logging Requirements

Hard Stop 발동 또는 평가 시 반드시 다음 정보를 남긴다.

### 기본 필드
- `account_id`
- `reason`
- `daily_realized_pnl`
- `consecutive_losses`
- `orders_sent_today`
- `latched`

### 추가 권장 필드
- `evaluation_point` (`BEFORE_SEND` / `AFTER_FILL`)
- `reason_detail`

### reason 예시
- `DAILY_LOSS_LIMIT_EXCEEDED`
- `MAX_CONSECUTIVE_LOSSES_EXCEEDED`
- `MAX_ORDERS_PER_DAY_EXCEEDED`
- `ALREADY_LATCHED`

### reason_detail 예시
- `pnl=-105000, limit=-100000`
- `consecutive_losses=3, max=3`
- `orders=21, max_orders=20`

---

## 17. Invariants

### Invariant H1
Hard Stop이 latched 상태이면 신규 주문은 항상 차단된다.

### Invariant H2
동일한 입력 상태는 동일한 Hard Stop 결정을 생성해야 한다.

### Invariant H3
Hard Stop은 자동 해제되지 않는다.

### Invariant H4
Hard Stop 판단은 주문 전송 전에 반드시 수행되어야 한다.

### Invariant H5 — Idempotent Decision
동일한 입력 상태에서 Hard Stop 평가를 여러 번 호출하더라도  
결과(`allowed`, `latched`, `reason`)는 항상 동일해야 한다.

### Invariant H6 — Monotonic Latch
`hard_stop_latched` 가 한 번 `true` 가 된 이후에는,  
같은 거래일 동안 시스템 내부 로직에 의해 `false` 로 되돌아갈 수 없다.

---

## 18. Operational Notes

- 본 문서는 계좌 레벨 보호를 정의하며, 종목 단위 보호(SymbolCooldown 등)보다 우선한다.
- Hard Stop은 전략 품질을 보완하는 장치가 아니라, 전략 실패 시 계좌 생존을 보장하는 장치이다.
- Hard Stop은 Reconciliation과 별개이며, 손실 기반 보호와 상태 무결성 보호는 서로 다른 축이다.

---

## 19. One-line SSOT

> Account Hard Stop은 당일 실현손실, 연속 손실, 주문 횟수 한도 중 하나라도 초과하면 즉시 발동하며, 발동 후에는 수동 해제 또는 거래일 초기화 전까지 모든 신규 주문을 차단한다.