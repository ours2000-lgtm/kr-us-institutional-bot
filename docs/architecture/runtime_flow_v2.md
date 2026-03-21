# 📄 docs/architecture/runtime_flow_v2.md

# KR_US_INSTITUTIONAL_BOT

## Runtime Flow Architecture v2 (Execution-Accurate)

---

# 🧭 1. 목적

이 문서는 **현재 실제 코드 기준으로 동작하는 런타임 흐름**을 정의한다.

* 전략 → 주문 → 체결 → 포지션 → 리컨실 → 리스크 차단
* Fail-Closed 경계 명확화
* 향후 Block Latch / Async 분리 위치 명시

---

# 🔥 2. 전체 실행 흐름 (핵심)

```
[Market Data]
    ↓
KiwoomRealRouter (tick ingress)
    ↓
StrategyEngine.on_tick()
    ↓
ExecutionController.execute()
    ↓
RiskManager.evaluate()   ← (PRE-TRADE GATE)
    ↓
OrderFactory.create()
    ↓
KiwoomAdapter.send_order()
    ↓
────────────────────────────────────
        (시장 / 거래소 영역)
────────────────────────────────────
    ↓
Chejan Event (체결 발생)
    ↓
KiwoomAdapter._on_receive_chejan()
    ↓
FillNormalizer.normalize()
    ↓
FillEventStore.append()   ← (LEDGER FIRST - SSOT)
    ↓
PositionManager.apply_fill()
    ↓
RiskManager.on_fill()     ← (POST-FILL RISK UPDATE)
    ↓
RuntimeReconciliationRunner.run()
    ↓
BrokerSnapshotAdapter.fetch_snapshot()
    ↓
ReconciliationEngine.compare()
    ↓
RiskManager.on_reconciliation_result()
    ↓
(⚠️ FUTURE) BLOCK LATCH TRIGGER
```

---

# 🧱 3. 핵심 구성 요소 역할

## 3.1 Strategy Layer

* StrategyEngine
* TestStrategy (또는 실전 전략)

👉 역할:

* tick 기반 시그널 생성
* 주문 의사결정 입력

---

## 3.2 Execution Layer

### ExecutionController

* 전략 → 주문 변환
* RiskManager와 통합

### OrderFactory

* Order 객체 생성

### KiwoomAdapter

* 실제 주문 전송
* 체결 이벤트 수신

---

## 3.3 State / Engine Layer

### FillNormalizer

* Chejan → 표준 FillEvent 변환

### FillEventStore (🔥 중요)

* 체결 ledger (SSOT)
* 모든 상태의 기준

### PositionManager

* 포지션 상태 관리

---

## 3.4 Risk Layer (핵심 제어)

### PRE-TRADE

```
RiskManager.evaluate()
```

* 주문 차단 여부 판단

---

### POST-FILL

```
RiskManager.on_fill()
```

* 체결 기반 리스크 업데이트

---

### RECONCILIATION

```
RiskManager.on_reconciliation_result()
```

* 계좌 불일치 감지
* 향후 Block Trigger 위치

---

## 3.5 Reconciliation Layer

### RuntimeReconciliationRunner

* 체결 이후 TR 기반 계좌 조회

### BrokerSnapshotAdapter

* 실제 계좌 snapshot

### ReconciliationEngine

* 내부 vs 브로커 상태 비교

---

# 🧭 4. Fail-Closed 경계 (중요)

## 🔴 Gate 1: Pre-Trade Risk

```
RiskManager.evaluate()
```

👉 주문 자체 차단

---

## 🔴 Gate 2: Ledger First

```
FillEventStore.append()
```

👉 체결은 반드시 기록 후 처리

---

## 🔴 Gate 3: Reconciliation

```
ReconciliationEngine.compare()
```

👉 불일치 탐지

---

## 🔴 Gate 4: (Future) Block Latch

```
self.trading_blocked = True
```

👉 시스템 전체 거래 정지

---

# ⚠️ 5. 현재 구조적 한계 (Known Risks)

## 5.1 Chejan 내부 TR Blocking

```
Chejan → Reconciliation → TR → EventLoop Block
```

문제:

* 체결 몰림 시 병목
* 이벤트 루프 충돌 가능

상태:

* 테스트 OK
* 고빈도 위험

---

## 5.2 Block Latch 미구현

현재:

* mismatch 감지 가능
* 하지만 지속 차단 없음

위험:

* 다음 tick에서 다시 주문

---

## 5.3 Retry / Timeout Escalation 없음

현재:

* timeout 발생 시 실패

향후:

```
1회 실패 → WARN
N회 실패 → BLOCK
```

---

# 🚀 6. 향후 확장 포인트

## 6.1 Block Latch (최우선)

```
if self.trading_blocked:
    reject_all_orders
```

---

## 6.2 Async Reconciliation

* QTimer 기반
  또는
* Worker thread

---

## 6.3 Multi-Asset 확장

* US Adapter
* Crypto Adapter

---

## 6.4 Governance 연동

* Validator → Execution Gate 연결

---

# 🧠 7. 핵심 설계 철학

## ✔ Ledger First

→ 모든 상태는 체결 기록 기반

## ✔ Fail-Closed

→ 의심되면 차단

## ✔ SSOT (Single Source of Truth)

→ FillEventStore

## ✔ Risk > Strategy

→ 전략보다 리스크 우선

---

# 🧭 8. 한 줄 정의

이 시스템은:

👉 "자동매매 시스템"이 아니라
👉 "계좌 무결성을 유지하는 실행 통제 시스템"이다

---
