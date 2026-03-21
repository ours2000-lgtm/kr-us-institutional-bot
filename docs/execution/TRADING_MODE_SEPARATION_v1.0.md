# TRADING_MODE_SEPARATION_v1.0

## 1. Purpose

본 문서는 자동매매 시스템에서
**모의(paper) 모드와 실전(live) 모드를 명확히 분리**하여
오작동으로 인한 실전 주문 실행을 방지하기 위한 설계를 정의한다.

---

## 2. Core Principle

> 코드 경로는 동일하게 유지하되,
> 주문 실행 권한은 mode에 의해 엄격히 제어된다.

---

## 3. Trading Mode

### 3.1 Modes

* `paper` (default)
* `live`

---

### 3.2 Default Rule

> 시스템 기본 모드는 반드시 `paper`이어야 한다.

* 명시적 설정 없으면 자동으로 `paper`
* `live`는 명시적으로만 활성화 가능

---

## 4. Execution Control

### 4.1 Order Flow

Strategy
→ Execution Controller
→ Risk Check
→ **Trading Mode Gate**
→ Broker Adapter

---

### 4.2 Mode Gate Rule

#### PAPER

* 실제 주문 전송 금지
* mock execution 또는 로그만 기록
* ledger / position / pnl은 정상 반영

---

#### LIVE

* 실제 주문 전송 허용
* 단, 아래 조건 모두 만족 시에만 허용

---

## 5. Live Safety Gates (필수)

### Gate 1 — Mode Check

```text
mode == "live"
```

---

### Gate 2 — Explicit Enable Flag

```text
LIVE_TRADING_ENABLED == True
```

---

### Gate 3 — Account Validation

* 실전 계좌 확인
* 모의 계좌일 경우 차단

---

### Gate 4 — Environment Check

* production 환경 여부 확인
* dev/test 환경에서는 live 차단

---

### Rule

> 위 모든 Gate를 통과해야만 실전 주문 전송이 허용된다.

---

## 6. Fail-Closed Rule

> 어떤 조건이라도 불확실하거나 누락되면
> 반드시 주문은 차단된다.

---

## 7. Logging Requirement

모든 로그에는 반드시 다음이 포함되어야 한다:

* `mode=paper|live`
* `account_type=paper|live`

---

## 8. Ledger Separation

ledger 경로는 mode별로 분리한다:

```text
logs/fills/paper/YYYY-MM/DD.jsonl
logs/fills/live/YYYY-MM/DD.jsonl
```

---

## 9. Snapshot Separation

snapshot에도 mode를 명시한다:

```json
{
  "mode": "paper",
  "position": {...},
  "pnl": {...}
}
```

---

## 10. One-line SSOT

> 실전 주문은 `mode=live`이면서 모든 safety gate를 통과한 경우에만 허용되며, 그 외 모든 경우에는 fail-closed로 차단된다.

---
