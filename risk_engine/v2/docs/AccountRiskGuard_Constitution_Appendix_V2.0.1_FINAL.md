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

📌 선언 (Declaration)

이 문서는
AccountRiskGuard의 최종 운영 헌법 부록으로 공포된다.

“계좌는 보호되어야 하며,
자동화는 항상 보수적으로 실패해야 한다.”

— AccountRiskGuard Constitution, V2.0.1