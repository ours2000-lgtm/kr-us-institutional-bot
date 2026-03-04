# KOA_PASSWORD_SAVE_RUNBOOK_v1
Operational Runbook
Version: v1.0

---

## 목적

Kiwoom OpenAPI 계좌 비밀번호를
정상적으로 등록하고 (44) 오류를 방지하기 위한 실무 절차 문서.

---

## STEP 1 – 영웅문 로그인

- 모의투자 또는 실계좌 로그인
- 보안모듈 정상 구동 확인

---

## STEP 2 – 계좌비밀번호 저장

메뉴:
상단 메뉴 → 계좌비밀번호 관리

또는 트레이 아이콘 우클릭 → 계좌비밀번호 저장

작업:
1) 계좌 선택
2) 비밀번호 입력
3) 전체 계좌 등록 확인
4) 저장

> NOTE (Mock Trading):
> 모의투자의 경우 기본 조회/거래 비밀번호는 통상 "0000"이다.
> 단, 모의계좌 신규 발급 직후에는 반드시 1회 계좌비밀번호 등록 절차를 수행해야 한다.
> 등록되지 않은 상태에서는 TR 조회 시 (44) 오류가 발생할 수 있다.

---

## STEP 3 – KOA Studio 검증

1) KOAStudioSA 실행
2) 파일 → Open API 접속
3) 접속 후 해지 1회 수행
4) 재접속

> INCIDENT CRITERIA:
> 본 단계에서 에러 팝업 또는 (44) 오류가 반복 발생할 경우,
> 화면 캡처를 확보하고 INCIDENT로 분류한다.
> 동일 세션에서 2회 이상 반복 시 운영팀 확인 대상으로 지정한다.

---

## STEP 4 – Autologin.dat 리셋 (필요 시)

경로:
C:\OpenAPI\system\Autologin.dat

절차:
1) 파일 백업
2) 삭제
3) STEP 2 다시 수행

> NOTE:
> Autologin.dat 삭제 후 최초 1회 OpenAPI 로그인 시
> 시스템이 자동으로 Autologin.dat를 재생성한다.
> 재생성 이후 반드시 STEP 2의 계좌비밀번호 등록 절차를 다시 수행한다.

---

## STEP 5 – TR 테스트 코드 규격

항상 아래 규격 사용:

SetInputValue("비밀번호", "")
SetInputValue("비밀번호입력매체구분", "00")

비밀번호 하드코딩 금지.

---

END OF DOCUMENT