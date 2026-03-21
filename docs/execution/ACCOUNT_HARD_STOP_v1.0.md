# ACCOUNT_HARD_STOP_v1.0

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

## 4. Inputs

Hard Stop 판단에 사용하는 최소 입력은 다음과 같다.

- `daily_realized_pnl`
- `consecutive_losses`
- `orders_sent_today`
- `hard_stop_latched`

---

## 5. Trigger Rules

다음 조건 중 하나라도 만족하면 Hard Stop을 발동한다.

### Rule A — Daily Realized Loss Limit
`daily_realized_pnl <= -daily_realized_loss_limit`

### Rule B — Max Consecutive Losses
`consecutive_losses >= max_consecutive_losses`

### Rule C — Max Orders Per Day
`orders_sent_today >= max_orders_per_day`

---

## 6. Initial Recommended Limits

초기 운영 기준 추천값:

- `daily_realized_loss_limit = 100000`
- `max_consecutive_losses = 3`
- `max_orders_per_day = 20`

실운영 시 전략 특성에 맞게 조정 가능하다.

---

## 7. State Model

### NORMAL
주문 가능 상태

### HARD_STOP_TRIGGERED
이번 평가에서 차단 조건을 충족한 상태

### HARD_STOP_LATCHED
차단이 고정된 상태

실제 운영에서는 `LATCHED` 상태가 핵심이다.

---

## 8. Latch Rule

Hard Stop이 발동되면:

- 신규 BUY 차단
- 신규 SELL 차단
- 재진입 차단

초기 버전에서는 **모든 신규 주문 차단**을 기본 정책으로 한다.

---

## 9. Reset Policy

### Same-Day
당일 Hard Stop은 당일 종료까지 유지한다.

### Next Trading Day
다음 거래일 시작 시 수동 또는 정책 기반 초기화를 허용할 수 있다.

초기 정책 권장:
> 당일 종료까지 유지, 다음 거래일에만 초기화 가능

---

## 10. Evaluation Timing

Hard Stop 평가는 최소 두 시점에서 수행한다.

### 10.1 Before Send
주문 전송 직전

### 10.2 After Fill
체결 반영 직후

---

## 11. Logging Requirements

Hard Stop 발동 시 반드시 다음 정보를 남긴다.

- `account_id`
- `reason`
- `daily_realized_pnl`
- `consecutive_losses`
- `orders_sent_today`
- `latched`

예시 reason:

- `DAILY_LOSS_LIMIT_EXCEEDED`
- `MAX_CONSECUTIVE_LOSSES_EXCEEDED`
- `MAX_ORDERS_PER_DAY_EXCEEDED`
- `ALREADY_LATCHED`

---

## 12. Invariants

### Invariant H1
Hard Stop이 latched 상태이면 신규 주문은 항상 차단된다.

### Invariant H2
동일한 입력 상태는 동일한 Hard Stop 결정을 생성해야 한다.

### Invariant H3
Hard Stop은 자동 해제되지 않는다.

### Invariant H4
Hard Stop 판단은 주문 전송 전에 반드시 수행되어야 한다.

---

## 13. One-line SSOT

> Account Hard Stop은 당일 손실, 연속 손실, 주문 횟수 한도 중 하나라도 초과하면 즉시 발동하며, 발동 후에는 수동 해제 또는 거래일 초기화 전까지 모든 신규 주문을 차단한다.