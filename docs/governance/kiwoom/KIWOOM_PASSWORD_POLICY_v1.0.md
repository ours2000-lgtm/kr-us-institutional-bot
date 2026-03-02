doc_id: KIWOOM_PASSWORD_POLICY_v1.0
status: FREEZE
semver: v1.0.0
bundle: OBS_SECURITY_FREEZE_BUNDLE
locked_at: 2026-03-02 KST
change_policy: "Any change requires v1.0.1+ via governance amendment"

# KIWOOM PASSWORD POLICY v1.0

## 1. Official Rule

SetInputValue("비밀번호", "") 만 허용.
비밀번호는 KOA 입력창에서만 등록.

비밀번호입력매체구분 기본값: "00"

허용 집합: {"00","01","02"}

---

## 2. 모의투자

기본 비밀번호: 0000
신규 발급 후 1회 등록 필수.

---

## 3. 금지 사항

SetInputValue("비밀번호", "1234") 사용 금지.
코드에서 비밀번호 전달 금지.

---

## 4. CI Enforcement

정적 분석으로 비밀번호 리터럴 전달 차단.