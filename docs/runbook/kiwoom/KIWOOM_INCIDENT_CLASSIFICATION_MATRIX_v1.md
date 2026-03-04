📄 KIWOOM_INCIDENT_CLASSIFICATION_MATRIX_v1.md

Version: v1.1 (Post-Review Draft)

2. Incident Severity Levels (Updated)
Level	의미	자동매매 영향
SEV-0	정상	없음
SEV-1	경미 오류	자동 재시도 및 모니터링
SEV-2	반복 오류	전략 일시 중지 검토
SEV-3	거래 차단	즉시 자동매매 중단
SEV-4	인증/보안 실패	전체 시스템 정지
SEV-1 Handling Rule

SEV-1은 자동 재시도 및 모니터링만 수행하며,
운영자 수동 개입은 필요하지 않다.

단, 동일 유형 오류가 SEV-2 조건에 도달하면 즉시 Escalation한다.

3. Error Code Classification (공통 시간 기준 추가)
Time Evaluation Rule

본 문서의
“N분 내 M회 이상” 조건은

시스템 로그 타임스탬프 기준

UTC+9

밀리초 단위

로 판단한다.

운영자의 체감 시간은 참고용으로만 사용한다.

4. Escalation Rule (Updated)

SEV-2 이상: 로그 보존 + 캡처 필수

SEV-3 이상: 자동매매 일시 정지

SEV-4: 시스템 전면 중단 + 운영 책임자 통보

SEV-4 Technical Containment Procedure

SEV-4 발생 시 즉시:

키움 관련 계정에 대한 신규 주문 및 로그인 요청 차단

해당 서버의 외부 네트워크 차단 여부 검토

계정 잠금 또는 비밀번호 변경 절차 수행 (운영 책임자 승인 하에)

5. FAIL-CLOSED Binding (Updated)

다음 조건 충족 시 자동매매는 BLOCK 상태로 전환된다:

SEV-3 이상 발생

동일 오류 3회 이상 반복

인증 관련 오류 감지

SEV-4 발생 즉시 전면 FAIL-CLOSED

6. Evidence Requirement (Updated)

SEV-2 이상 INCIDENT 발생 시:

오류 코드

발생 시각

TR 코드

screen_no

계좌 번호 (마스킹)

직전 5개 이벤트 로그

Log Format Standard

기본 저장 형식: JSON Lines (.jsonl)

각 라인은 단일 INCIDENT 이벤트를 표현한다.

필요 시 배치 분석을 위해 CSV로 2차 변환할 수 있다.

저장 경로:
logs/kiwoom/incidents/