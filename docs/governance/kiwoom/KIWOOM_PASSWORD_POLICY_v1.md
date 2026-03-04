# KIWOOM_PASSWORD_POLICY_v1
KR_US_INSTITUTIONAL_BOT – Governance Controlled Policy
Version: v1.0
Status: DRAFT (Pre-Lock)

---

## 1. 목적 (Purpose)

본 문서는 Kiwoom OpenAPI(KHOpenAPI) 사용 시
계좌 비밀번호 처리에 대한 단일 진실원천(SSOT)을 정의한다.

본 정책은 보안 정책을 준수하면서
자동매매 시스템의 안정적 운영을 보장하는 것을 목표로 한다.

---

## 2. 공식 원칙 (Official Principle)

1) TR 요청 시:
   - SetInputValue("비밀번호", "")
   - SetInputValue("비밀번호입력매체구분", "00")

2) 계좌 비밀번호는 코드에 전달하지 않는다.
3) 계좌 비밀번호는 오직 KOA/영웅문 UI를 통해 등록·저장한다.
4) 코드 내 하드코딩 금지 (Hardcoding Prohibited).

---

## 3. 운영 표준 플로우 (Standard Operational Flow)

1) 영웅문 로그인 (모의/실계좌)
2) 메뉴 → 계좌비밀번호 관리/저장
3) 계좌 선택 후 비밀번호 입력
4) 전체 계좌 등록/저장 확인
5) OpenAPI 재로그인
6) TR 조회 테스트

정상 동작 시:
- TR 요청에서 비밀번호 공백으로 조회 가능
- 팝업 미발생

---

## 4. (44) 오류 대응 규칙

에러 코드:
(44) 계좌비밀번호 입력창을 통해 조회에 사용한 계좌번호의 비밀번호를 입력하십시오

### 조치 순서 (3축 원칙)

A. 계좌비밀번호 저장 재확인
- KOA Studio 실행
- Open API 접속/해지 1회 수행
- 계좌비밀번호 저장 재등록

B. Autologin.dat 리셋 (최후 수단)
- 경로: C:\OpenAPI\system\Autologin.dat
- 백업 후 삭제
- 계좌비밀번호 재등록

C. 매체구분 튜닝 (비정상 환경)
- 기본: "00"
- 반복 발생 시:
  1) "02"
  2) "01"
- 단, 비밀번호는 코드에 전달하지 않는다.

---

## 5. 완전 무인 자동화 정책

본 시스템은 다음을 허용하지 않는다:

- 계좌비밀번호 코드 전달
- 비밀번호 자동 입력 우회 로직
- 보안 정책 위반 자동화

허용 범위:

- 로그인 이후 세션 유지 자동화
- KOA 저장된 비밀번호에 의존한 TR 실행

---

## 6. 보안 규약

- 비밀번호는 코드/로그/레포지토리에 저장 금지
- 환경 변수로도 저장하지 않음
- 암호화 저장은 Kiwoom 시스템에 위임

---

## 7. 변경 절차

본 문서는 Governance 변경 절차에 따라 수정 가능.
LOCK 이후 변경 시 Amendment 기록 필수.

---

## 8. Implementation Enforcement (Build / CI Blocking Rule)

본 정책은 문서 선언에 그치지 않으며,
레포지토리 레벨에서 기술적으로 강제된다.

### 8.1 비밀번호 전달 차단 규칙

다음 패턴은 금지된다:

SetInputValue("비밀번호", <literal_or_variable>)

허용되는 유일한 형태:

SetInputValue("비밀번호", "")

위반 시:

- 정적 분석 단계에서 실패 처리
- CI 파이프라인 차단
- 빌드/배포 중단

---

### 8.2 매체구분 값 허용 집합

비밀번호입력매체구분 허용 값:

{"00", "01", "02"}

이외 값 사용 시:

- 테스트 실패 처리
- PR 병합 차단

---

### 8.3 Governance Binding

본 조항은 Governance Enforcement Layer에 의해
자동 검증 대상이 된다.

정책 위반 코드는 승인 없이 병합될 수 없다.

---

---

END OF DOCUMENT