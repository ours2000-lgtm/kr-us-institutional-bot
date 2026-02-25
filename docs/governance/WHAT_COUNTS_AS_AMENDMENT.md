# WHAT_COUNTS_AS_AMENDMENT.md (v1.0)

[헌법 종속 선언]
본 문서는 변경 사항을 분류할 뿐이며, **constitution.md v1.x** 및 **AMENDMENT_PROCEDURE.md v1.0**에 정의된 공식 개정 절차를 대체하거나 우회할 권한을 부여하지 않습니다.

---

## 1. 개정 판정 원칙 (Core Principles)

1. **Invariants 우선:** 시스템의 수학적/법적 불변값(Invariants)에 손을 대는 모든 행위는 예외 없이 '개정(Amendment)'으로 간주합니다.
2. **보수적 접근 (Conservative Classification):** 판정이 모호하거나 경계선상에 있을 경우, 반드시 상위 타입(**Type A > Type B > Type C/D**)으로 승격하여 판정합니다.
3. **행위 우선 (Behavior-first) 원칙:** 변경이 텍스트 레벨에서 어떻게 보이든, 결과적으로 시스템의 실제 행위(Behavior), 권한 분포, 혹은 리스크 민감도를 바꾸면 Type A 또는 B로 분류합니다.
4. **즉시 반려 및 정석 재제출:** 본 기준을 위반하여 하위 타입으로 제출된 PR은 즉시 반려됩니다. 재제출 시에는 반드시 **AMENDMENT_PROPOSAL 및 CIA_EVIDENCE 템플릿(Type A 기준)**을 모두 포함하여 정석 경로를 밟아야 합니다.

---

## 2. 분류 매트릭스 (Classification Matrix)

| Type | Label | 대상 (Scope) | 성격 | 필요 절차 |
| :--- | :--- | :--- | :--- | :--- |
| **A** | **Constitutional Core** | Invariants, CIA 임계치, Baseline, 수학적 하한선 | **불변값 수정** | Proposal + Evidence 필수 |
| **B** | **Governance Core** | 투표 정족수(Quorum), 절차 기간, 쿨다운(Cooling-off) | **운영 규칙 변수** | Proposal 필수 |
| **C** | **Textual/Fix** | 오타 수정, 깨진 링크, 의미 불변 가독성 개선 | **형식 수정** | Fast-track (General PR) |
| **D** | **Operational Data** | 기존 로직에 따른 결과 기록, 단순 로그 업데이트 | **단순 기록** | Fast-track (General PR) |

> **⚠️ Type B(운영 규칙) vs Type A(불변값) 구분:**
> Type B는 시스템의 '절차적 엔진'을 조절하는 변수(예: 투표 일수)이며, Type A는 시스템의 '생존 마진'을 결정하는 근본 수치(예: 최소 잔여 마진)입니다.

---

## 3. 실무 사례집 (Case Studies)



1. `MAX_RESIDUAL_MARGIN` 수치 변경 → **Type A** (수학적 하한선 변경)
2. **투표 정족수(Quorum) 비율 변경** → **Type B** (의사결정 엔진 설정값 수정)
3. 신규 성능 지표를 필수 지표로 편입 → **Type A** (판단 체계 변경)
4. 로그 업데이트 시 새로운 가중치(Weight) 산정 방식 포함 → **Type A** (Behavior에 직접 영향)
5. `MIN_VOTE` → `THRESHOLD` 등 핵심 변수명 변경 → **Type A** (의미론적 재설정)
6. **Cooling-off 기간의 중복 적용 또는 예외 처리 로직 추가** → **Type B** (절차법 예외 조항 생성)
7. 단순 오타 및 마크다운 문법 교정 → **Type C**
8. 정기적인 시스템 가동률 통계 로그 기록 추가 → **Type D** (기존 로직에 의한 데이터 적재)

---
**Failure to classify correctly indicates non-conformance with the governance system.**