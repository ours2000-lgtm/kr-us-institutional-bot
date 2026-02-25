GOVERNANCE_PR_CHECKLIST.md (v1.0)
[집행 원칙] 본 문서는 판단이 아닌 집행(Enforcement) 문서입니다. 모든 체크 항목은 [x] YES로 표시되어야 하며, YES/NO 혼용 표기 또는 미기입 항목이 있을 시 PR은 즉시 자동 반려(Fail-Closed)됩니다. ---

0. PR Metadata (시스템/봇 연동용)
CI/CD 파서가 읽어가는 필수 메타데이터 블록입니다.

PR Number: #

Change Type: [Type A / Type B / Type C / Type D]

Proposal ID: [PROPOSAL-ID] (Type A/B 필수, 파일명 일치 확인)

CIA Evidence Link: [Link] (Type A 필수, SHA256 확인)

Evidence Freshness: YYYY-MM-DD (기준: 제출 시점 기준 ≤ 90 days)

Reproduction Tolerance: ±ε % (재현 시 허용 오차 범위 명시)

1. 개정 유형 판정 (Classification)
WHAT_COUNTS_AS_AMENDMENT.md의 Case Study와 일치해야 하며, 모호할 경우 상위 타입으로 승격합니다.

Q1. 직접 수정: 이 변경이 헌법, 절차법, 권한 구조, CIA 임계치를 직접 수정하는가?

[ ] YES / [ ] NO

Q2. 실질 행위: 직접 수정은 아니나, 결과적으로 시스템의 행위/권한 분포/민감도를 변경하는가?

[ ] YES / [ ] NO

[판정 규칙]: 위 질문 중 하나라도 YES이면 반드시 Type A 또는 B 경로를 타야 합니다.

[ ] Type C/D 재검토: Fast-track 제출 시, Behavior-first 원칙에 따라 A/B 승격 대상이 아님을 재검토했는가? [ ] YES

2. 필수 문서 및 경로 검증 (Documentation & Path)
[ ] Path-Type Mapping: /constitution/**, /procedures/** 수정 시 Change Type이 A/B로 선언되었는가? [ ] YES

[ ] 파일명 일치: Proposal/Evidence 파일명이 PROPOSAL-ID와 완벽히 일치하는가? [ ] YES

[ ] Cross-reference: PR 본문 ↔ Proposal ↔ CIA Evidence 간 모든 링크가 유효한가? [ ] YES

3. 기술적 무결성 및 수식 검증 (Technical Integrity)
[ ] 무결성 해시: 모든 Raw Data, 로그, Evidence 문서 자체에 대한 SHA256 해시가 명시되었는가? [ ] YES

[ ] Residual Margin 필드 검증: 아래 네 가지 수치가 모두 명시되었으며 헌법 최소치를 충족하는가? [ ] YES

Current Margin:

Delta:

Residual Margin: (계산식: Current - Delta)

Min Threshold: (헌법 정의값)

[ ] 재현 조건: 제3자가 동일 결과를 얻기 위한 명령어, 도구 버전, 허용 오차가 명시되었는가? [ ] YES

4. 절차 및 쿨다운 검증 (Procedure)
[ ] 정족수/기간: 해당 Type에 요구되는 투표 요건이 AMENDMENT_PROPOSAL에 정확히 반영되었는가? [ ] YES

[ ] Cooling-off 준수: 가결 후 적용 대기 기간이 최소 요건을 충족하며, 이전 개정 스케줄과 중복되지 않는가? [ ] YES

🤖 CI/CD 검증 범위 (Bot Validation Scope)
위반 시 PR은 즉시 Fail-Closed 처리됩니다.

Path-Type 일치: 경로와 선언된 Type 불일치 감지 시 실패.

Schema/Field 검증: 수식 필드, SHA256, Freshness 날짜(90일 기준) 누락 시 실패.

Keyword Trigger: THRESHOLD, VOTING_PERIOD, QUORUM, COOLING_OFF, RESIDUAL_MARGIN 등 핵심 변수 수정 시 Type B 강제 여부 체크.

⚠️ 반려 후 처리 안내 (Post-Reject Handling)
본 PR이 반려 또는 자동 Close 된 경우:

WHAT_COUNTS_AS_AMENDMENT.md 기준에 따라 타입을 재평가하십시오.

이전 PR 링크 또는 Revert Commit Hash를 History에 명시하여 추적성(Traceability)을 확보하십시오.

이전 Auto-Close 링크가 없는 동일/유사 변경의 단순 재제출은 즉시 반려됩니다.