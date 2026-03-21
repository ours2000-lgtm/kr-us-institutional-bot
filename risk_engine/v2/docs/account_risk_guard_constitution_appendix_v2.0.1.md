0. 목적과 지위 (Purpose & Authority)

본 문서는 AccountRiskGuard의 설계·행동·권한을 정의하는
**운영 헌법 부록(Constitution Appendix)**이다.

실계좌(Live) 기준 최상위 리스크 보호 규범

코드·모델·로그·알림의 단일 진실 원천(Single Source of Truth)

V2.0.1에서 동결(FROZEN) 되며,
이후 변경은 V2.1+ 확장 부록으로만 허용된다.

1. AccountRiskGuard의 역할

AccountRiskGuard는 주문 이전(pre-trade) 단계에서
계좌 단위 리스크를 평가하여 다음 중 하나의 결정을 내린다.

ALLOW

REDUCE

BLOCK

HARD_STOP

이 결정은 Policy / Core / Order-level Guard보다 항상 우선한다.

2. Action 의미 정의 (Immutable)
2.1 Action Semantics
Action	의미
ALLOW	정상 허용
REDUCE	주문 사이즈 축소 / 보수적 실행
BLOCK	신규 주문 차단 (계좌는 유지)
HARD_STOP	계좌 Kill Switch, 신규 주문 절대 금지

HARD_STOP 상태에서는 사람 승인 없이는 어떤 자동 로직도 해제 불가

3. Circuit Breaker Level (Account / Strategy / Symbol)
3.1 Circuit Level 의미
Level	의미
0	정상
1	REDUCE 중심 보수화
2	신규 진입 BLOCK, 청산만 허용
3	HARD_STOP (Kill Switch)
3.2 Fail-Closed 규칙

snapshot_level >= LEVEL_2 또는

system_health == CRITICAL

👉 최소 circuit_level = 1 보장

4. Reason Code ↔ Circuit Level 하한 규칙

다음 reason_code는 최소 circuit_level 하한을 강제한다.

reason_code	최소 circuit_level
ACCOUNT_KILL_SWITCH	2
TECHNICAL_FAILURE	2
DAILY_LOSS_LIMIT_EXCEEDED	1
MAX_EXPOSURE_EXCEEDED	1
RATE_LIMIT_EXCEEDED	1

이 규칙은 전역 불변 규칙이다.

5. Reset Policy (HARD_STOP 해제 규칙)
5.1 기본 원칙

reset_policy가 누락되거나 unknown일 경우
→ MANUAL_ONLY + HARD_STOP 유지

5.2 Reset Policy Type
type	의미
MANUAL_ONLY	사람 승인 필수
NEXT_SESSION	다음 거래 세션 이후 자동 가능
HEALTH_CHECK	헬스체크 통과 후 가능
5.3 원칙

TECHNICAL_FAILURE는 헬스체크 기반으로만 해제 가능

DAILY_LOSS_LIMIT_EXCEEDED는
“다음 거래일 + 조건 충족” 전까지 유지 가능

6. Throttle / Rate-Limit 규칙
6.1 기록 원칙

실제 주문 차단이 발생하면
→ throttle.enabled = true 항상 기록

BLOCK / HARD_STOP에서도 throttle 메타는 남긴다.

6.2 Throttle 정책 구분

Soft Throttle: 지연 / REDUCE

Hard Throttle: BLOCK

7. Snapshot / Health Fail-Closed 원칙
7.1 Snapshot Quality Level
Level	의미
LEVEL_0	정상
LEVEL_1	약간 stale
LEVEL_2	부분 누락
LEVEL_3	불완전 / 불일치
7.2 기본 행동 매핑
상태	기본 행동
LEVEL_1	REDUCE + Throttle
LEVEL_2	SAFE_REDUCE
LEVEL_3	SAFE_BLOCK 또는 HARD_STOP
8. Human Intervention (사람 개입)
8.1 필수 개입 조건

다음 상황에서는 사람 승인 없이는 재개 불가:

HARD_STOP

ACCOUNT_KILL_SWITCH

TECHNICAL_FAILURE

8.2 개입 원칙

장중에는 가드 해제 불가 (옵션)

승인 주체·채널·타임아웃은 메타로 기록

9. AccountRiskState — 단일 진실 원칙

AggregationEngine이 생성한 AccountRiskState는
다음 호출의 AccountRiskGuard 입력이 된다.

중간 모듈은 계좌 리스크 상태를 재계산하거나 복제하지 않는다.

10. Decision Trace & Summary Line (필수)
10.1 decision_trace 필수 노드

다음 노드는 항상 존재해야 한다.

account_guard

policy

core

post_core

스킵된 경우에도:

{ "skipped": true, "reason": "..." }


를 반드시 기록한다.

10.2 summary_line 최소 포함 요소

summary_line에는 반드시 포함되어야 한다:

action

주요 reason_code

circuit_level

blocked 여부

policy_name

11. 변경 규칙 (Governance)

본 문서는 V2.0.1 FINAL로 동결

수정/추가는 V2.1+ Appendix로만 허용

코드가 문서를 위반할 경우, 코드가 잘못된 것

12. Meta Governance Principles (메타 거버넌스 원칙) — FINAL
12.1 Versioning Principle (버전 관리 원칙)

본 헌법 부록, 이에 기반한 모델(AccountRiskDecision, AccountRiskState),
그리고 이를 직렬화한 JSON/로그 포맷은 공통 version 필드를 반드시 포함한다.

버전 변경 규칙은 다음을 따른다.

MAJOR/MINOR 버전 변경은 의미적 계약(semantic contract)의 변경을 의미한다.

하위 호환성을 깨는 변경이 없는 한, PATCH 수준의 변경만 허용한다.

MAJOR 또는 MINOR 버전이 증가할 경우:

해당 버전을 대상으로 하는 전용 테스트 스위트

해당 버전을 기준으로 한 샘플 로그/fixture 세트
를 반드시 유지한다.

MAJOR/MINOR 버전 변경 시, 이전 버전과의 호환성 여부 및 마이그레이션 경로를
본 부록 또는 별도 문서에 명시해야 한다.

버전은 단순 식별자가 아니라,
의사결정·감사·재현 가능성의 기준점으로 취급된다.

12.2 Top-Down Single Source of Truth Rule (상향식 변경 금지 규율)

AccountRiskGuard 시스템의 변경은 항상 다음 방향만 허용된다.

Constitution Appendix
→ Model Definition (Pydantic / TypedDict)
→ Code Implementation
→ JSON / Log / Event Format

즉,

헌법 문서가 변경되지 않은 상태에서 모델을 변경할 수 없으며

모델이 변경되지 않은 상태에서 코드/로그 포맷을 변경할 수 없다.

이 규율은 **단일 진실 원천(Single Source of Truth)**을 유지하기 위한 절대 원칙이다.

단, 12.3(긴급 예외 조항)에 해당하는 경우에는 일시적으로 이 원칙을 위반할 수 있으며,
해당 변경은 반드시 사후에 헌법 부록과 모델 정의에 반영되어야 한다.

12.3 Emergency Exception Clause (긴급 예외 조항)

다음과 같은 심각한 운영 사고 또는 치명적 버그 대응 상황에서는
예외적으로 코드 또는 로그 포맷이 헌법 문서보다 먼저 수정될 수 있다.

실계좌 자산 보호를 위한 즉각적 조치가 필요한 경우

시스템 장애로 정상적인 변경 절차를 따를 수 없는 경우

단, 이 경우에도 다음 원칙은 반드시 지켜져야 한다.

임시 변경은 **예외(Emergency Exception)**로 명확히 식별되어야 한다.

가능한 한 빠른 시점에:

헌법 부록

모델 정의
를 **역방향으로 정합(sync)**시키는 것을 의무로 한다.

임시 조치는 영구 설계로 간주되지 않는다.

12.4 Enforcement by Code & Test Principle (코드·테스트에 의한 헌법 집행)

AccountRiskDecision 및 AccountRiskState 모델은
본 헌법 부록의 규칙을 **코드 레벨에서 자동으로 검증(enforce)**해야 한다.

이를 위해:

각 모델은 model_version 필드를 필수로 포함한다.

런타임 검증 단계에서:

모델 버전과 헌법 부록 버전의 정합성을 확인한다.

fail-closed 규칙
(예: reason_code → 최소 circuit_level, snapshot/health 기반 보수화)
은 validator 또는 model-level check로 구현한다.

모든 헌법 수준 규칙은 최소 하나 이상의 자동 테스트(단위/통합 테스트)에 의해 검증되어야 한다.
테스트 없이 코드에만 존재하는 규칙은 헌법 규칙으로 간주하지 않는다.

12.5 Final Authority Statement (최종 권위 선언)

본 헌법 부록과 상충되는 동작을 하는 코드, 모델, 로그가 존재할 경우
문서가 옳고, 구현이 잘못된 것이다.

AccountRiskGuard는
“빠르게 거래하기 위한 시스템”이 아니라
**“계좌를 절대 망가뜨리지 않기 위한 시스템”**이다.

자동화는 언제나 보수적으로 실패해야 하며,
그 기준은 본 헌법 부록에 의해 정의된다.

📌 선언 (Declaration)

이 문서는
AccountRiskGuard의 최종 운영 헌법 부록으로 공포된다.

“계좌는 보호되어야 하며,
자동화는 항상 보수적으로 실패해야 한다.”

— AccountRiskGuard Constitution, V2.0.1