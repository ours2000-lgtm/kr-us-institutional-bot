# POSITION_MANAGER_V2_SPEC

Version: v2.0  
Status: DESIGN LOCK

---

# 1. Scope

PositionManager는 Fill(체결) 이벤트를 기반으로 포지션 상태를 유지하는 상태 엔진이다.

PositionManager는 다음 상태를 관리한다.

- 보유 수량 (qty)
- 평균 단가 (avg_price)
- 마지막 업데이트 시각 (last_update)

PositionManager는 체결 기반 상태의 **Single Source of Truth (SSOT)** 로 동작한다.

모든 포지션 상태 변경은 체결 이벤트를 통해서만 발생한다.

---

# 2. Non Goals

PositionManager는 다음 책임을 가지지 않는다.

- 전략 판단
- 주문 생성
- 리스크 판단
- 세금 계산
- 브로커 잔고 조회
- Lot 기반 회계 (FIFO/LIFO)

본 버전(v2)은 다음 범위를 가진다.

Long-only  
Average price model

---

# 3. Position Key Model (v2)

## 3.1 Goal

Position Key Model의 목적은 모든 Fill 이벤트를 **단일 규칙으로 포지션 상태에 매핑**하는 것이다.

브로커별 포맷이 아니라 **시스템 공통 식별 키**를 사용한다.

PositionKey는 포지션 상태 식별자이며, 주문 추적 ID(intent_id, broker_order_id)와는 별개의 개념이다.

---

# 3.2 Field Set

PositionKey는 다음 필드를 포함한다.

account_id  
symbol  
exchange  
currency  
instrument_type  

예시

account_id = ACC12345  
symbol = 005930  
exchange = KRX  
currency = KRW  
instrument_type = EQUITY  

v2 범위에서는 대부분 다음 조합을 사용한다.

EQUITY + 현물

하지만 향후 확장을 위해 필드를 유지한다.

---

# 3.3 Internal Representation

내부 표현은 immutable dataclass를 사용한다.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PositionKey:
    account_id: str
    symbol: str
    exchange: str
    currency: str
    instrument_type: str