# POSITION_PNL_SEPARATION_v1.0

## 1. Purpose

본 문서는 체결 기반 자동매매 시스템에서
**Position 상태와 손익(PnL) 계산 책임을 분리**하여
구조적 안정성, 확장성, 재현성을 확보하기 위한 설계를 정의한다.

---

## 2. Design Principle

> Position은 “보유 상태”만 책임지고,
> PnL은 “손익 계산 상태”만 책임진다.

---

## 3. Responsibility Separation

### 3.1 Position (State of Holding)

Position은 오직 보유 상태만 표현한다.

#### 필드

* `qty`: 보유 수량 (>= 0, long-only)
* `avg_price`: 평균 단가
* `last_update`: 마지막 업데이트 시간

#### 책임

* 체결(fill)에 따라 수량과 평균 단가 갱신
* 손익 계산 로직 포함 금지

---

### 3.2 PnLState (State of Profit & Loss)

PnLState는 손익 관련 상태만 표현한다.

#### 필드 (v1 최소)

* `realized_pnl`: 실현 손익

#### 확장 필드 (v1.1 이후)

* `unrealized_pnl`
* `mark_price`
* `fees`
* `taxes`
* `net_realized_pnl`

#### 책임

* SELL fill 발생 시 realized 계산
* mark price 기반 unrealized 계산 (향후)
* 수수료/세금 반영 (향후)

---

## 4. Fill Processing Rule

### 4.1 BUY Fill

* Position:

  * qty 증가
  * avg_price 갱신

* PnL:

  * 변화 없음

---

### 4.2 SELL Fill

* Position:

  * qty 감소

* PnL:

  * realized_pnl 증가/감소

---

## 5. Processing Flow

Fill 처리 흐름:

FillEvent
→ Position 업데이트
→ PnLState 업데이트

---

## 6. Determinism Rule

> 동일 ledger replay 시,
> Position과 PnLState는 항상 동일한 결과를 생성해야 한다.

---

## 7. Separation Invariant

### Invariant P1

Position은 손익 정보를 포함하지 않는다.

---

### Invariant P2

PnLState는 Position 상태 없이 독립적으로 계산되지 않는다.
(항상 Position 상태를 기반으로 계산됨)

---

### Invariant P3

Position과 PnLState는 동일한 fill 순서를 공유해야 한다.

---

## 8. Snapshot Structure

외부 노출용 snapshot은 다음 구조를 따른다:

```json
{
  "position": {
    "qty": ...,
    "avg_price": ...
  },
  "pnl": {
    "realized": ...
  }
}
```

---

## 9. Extension Path

### v1 (현재)

* Position.qty
* Position.avg_price
* PnL.realized

---

### v1.1

* unrealized_pnl
* mark_price 기반 평가손익

---

### v1.2

* fees
* taxes
* net_realized

---

## 10. Design Rationale

이 구조는 다음을 보장한다:

* Position 계산 단순화
* 손익 계산 확장성 확보
* Reconciliation 분리 가능
* Risk Engine 독립성 확보

---

## 11. One-line SSOT

> Position은 보유 상태만, PnL은 손익만 담당하며,
> 동일한 fill replay에 대해 두 상태는 항상 동일한 결과를 생성한다.

---
