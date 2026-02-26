# POLICY COMPOSITION CONTRACT v0.5
Status: LOCK (MVP)
Effective Version: v0.5
Applies To: CompositePolicyDecision / run_consistency_pipeline

---

## 0. 용어 정의 (Glossary)

- **Grade**: `{"PASS","WARN","BLOCK"}` 중 하나. 글로벌 순서: `PASS < WARN < BLOCK`.
- **Decision**: `{"ALLOW","BLOCK"}` 중 하나. 실행 허용 여부만 표현한다.
- **PolicySpec**: 정책 정의 스펙. 최소 `ref, version, enabled, priority`를 포함하며, 필요 시 `expected_ref/expected_version`을 포함할 수 있다.
- **CompositionMeta**: 합성 메타데이터 컨테이너. `ordered_policy_refs/versions`, `disabled_*` 등 합성 과정의 “감사/설명 가능한 흔적”을 담는다.
- **CompositePolicyDecision**: `final(최종 PolicyDecision)`, `components(정책별 결과)`, `meta(합성 메타)`를 포함하는 합성 결과 루트 오브젝트.

---

## 1. 목적

v0.5는 단일 정책 체계(v0.4)를 확장하여,
다중 정책 합성(Policy Composition)을 공식적으로 지원한다.

이 문서는:

- 합성 규칙 (fail-closed)
- grade ordering 계약
- marker reason code 규칙
- disabled policy 메타 기록 규칙
- Evidence hash 안정성 보장 범위
- v0.4 ↔ v0.5 호환성

을 SSOT로 정의한다.

---

## 2. Grade Ordering (Global Invariant)

Grade는 다음 순서를 따른다:

`PASS < WARN < BLOCK`

정의:

- `final.grade = max(component.grade)`
- `BLOCK`이 하나라도 존재하면 `final.decision = BLOCK`
- `WARN`은 `PASS`보다 상위

이 규칙은 모든 정책 합성에 대해 불변이다.

---

## 3. Fail-Closed Composition Rule

합성 규칙 (v0.5-mvp):

- 각 enabled 정책은 독립적으로 평가된다.
- 하나라도 `decision == "BLOCK"`이면 → 최종 `decision = "BLOCK"`
- 그렇지 않으면 → 최종 `decision = "ALLOW"`

이 규칙은 **mode와 무관하게** 적용된다.  
(mode는 개별 정책 내부 동작에만 영향)

---

## 4. Marker Reason Code Rule

합성 단계는 반드시 상위 marker reason code를 포함해야 한다.

- 최종 BLOCK → `P0-COMPOSITE-BLOCK`
- 최종 ALLOW → `P2-COMPOSITE-ALLOW`

규칙:

- marker는 `reason_codes` 리스트의 **첫 번째 요소**여야 한다.
- marker는 리스트에 **정확히 한 번만** 등장해야 한다.
- 이후 개별 정책의 `reason_codes`가 병합된다.
- 중복 제거는 stable_unique 규칙으로 수행하되, **marker의 유일성/선두 위치는 불변**이어야 한다.

이 marker는 **Evidence core**에 포함된다.

---

## 5. Disabled Policy Contract

`PolicySpec.enabled = False`인 정책은:

- 평가되지 않는다.
- `components` 리스트에 포함되지 않는다.
- `meta.disabled_policy_refs`에 기록된다.
- `meta.disabled_policy_versions`에 기록된다.
- (선택) `meta.disabled_policy_priorities`에 기록될 수 있다.

Disabled 정책 정보는:

- Evidence `rich_context`에만 기록된다.
- Evidence core hash에는 포함되지 않는다.

---

## 6. Deterministic Ordering Rule

정책 정렬은 다음 기준을 따른다:

1. `enabled=True` 우선
2. `priority` 오름차순
3. `ref` 오름차순
4. `version` 오름차순

이 정렬 순서는:

- `components` 순서
- `reason_codes` 병합 순서
- `meta.ordered_policy_refs`
- `meta.ordered_policy_versions`

에 그대로 반영되어야 한다.

---

## 7. Evidence Hash Stability

Evidence core hash는 다음 요소만 포함한다:

- ConsistencyResult
- AggregationResult
- final PolicyDecision (CompositePolicyDecision.final)
- principal
- timestamp_utc

다음은 hash에 포함되지 않는다:

- composition.meta
- composition.components
- rich_context 전체

즉:

Composition 확장은 Evidence 해시 계약을 깨지 않는다.

### 7.1 Hash 입력 영역 예시 (시각적 스냅샷)

core에 포함 (hash 입력):

```json
{
  "consistency": { "...": "..." },
  "aggregation": { "...": "..." },
  "policy": {
    "policy_ref": "COMPOSITE",
    "policy_version": "v0.5",
    "decision": "ALLOW",
    "grade": "PASS",
    "reason_codes": ["P2-COMPOSITE-ALLOW", "P3-..."]
  },
  "principal": {"type": "human", "id": "tester"},
  "timestamp_utc": "2026-02-26T00:00:00Z"
}

rich_context에만 포함 (hash 제외):

{
  "composition": {
    "meta": {
      "ordered_policy_refs": ["PolicyA", "PolicyB"],
      "ordered_policy_versions": ["v0.4", "v0.4"],
      "disabled_policy_refs": ["PolicyC"],
      "disabled_policy_versions": ["v0.3"]
    },
    "components": [
      { "policy_ref": "PolicyA", "...": "..." }
    ]
  },
  "pipeline_snapshot": { "...": "..." }
}
8. Policy Identity

합성된 최종 policy는 다음 identity를 갖는다:

policy_ref = "COMPOSITE"

policy_version = "v0.5"

개별 정책의 ref/version은 meta/components 및 rich_context에만 기록된다.

9. Backward Compatibility (v0.4 ↔ v0.5)

v0.5는:

v0.4 단일 정책 구조와 호환된다.

default policy specs는 v0.4 AnyFailBlockPolicy 하나만 포함할 수 있다.

기존 Evidence hash 재현성 테스트는 유지된다.

9.1 호환 표
항목	v0.4 단일 정책	v0.5 합성 정책
policy_ref	"AnyFailBlockPolicy"	"COMPOSITE"
policy_version	"v0.4"	"v0.5"
decision/grade 의미	동일	동일
reason_codes	기존 규칙	맨 앞에 COMPOSITE marker 추가
Evidence core hash 입력	동일 필드 집합	동일 + COMPOSITE identity, hash 규칙 유지
rich_context	선택적, 구조 제한 없음	composition/meta/components 추가 (hash 제외)
10. Test Contract (Non-normative examples)

이 섹션은 규범(SSOT)을 설명하기 위한 예시이며,
실제 SSOT는 pytest 계약이 보호한다.

10.1 Fail-closed

Given: 컴포넌트 중 하나 decision=BLOCK

Expect:

final.decision=BLOCK

marker: reason_codes[0]="P0-COMPOSITE-BLOCK"

10.2 Grade ordering

Given: 최종적으로 PASS/WARN이 혼합되는 상황 (grade ordering 적용)

Expect:

final.grade=WARN (PASS < WARN)

10.3 Marker

Given: 최종 ALLOW

Expect:

reason_codes[0]="P2-COMPOSITE-ALLOW"

marker는 정확히 한 번만 등장

10.4 Disabled meta

Given: enabled=False 정책 포함

Expect:

meta.disabled_policy_refs와 meta.disabled_policy_versions에 기록

components에는 포함되지 않음

11. 향후 확장 (Non-MVP)

v0.6 이상에서 고려 가능:

weighted composition

quorum-based policy

override policy

priority-based decision dominance

policy groups

이 문서는 v0.5 MVP 범위까지만 LOCK한다.

END OF CONTRACT