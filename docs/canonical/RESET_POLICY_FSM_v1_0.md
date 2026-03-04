0) Purpose

Reset은 체인의 “정체성”을 바꾸는 고위험 행위다.
따라서 Reset은 **행동(action)**이 아니라 **허용 전이(transition)**로만 정의하며,
FSM을 거치지 않은 Reset은 구조적으로 불가능해야 한다.

이 문서는 다음만 정의한다:

상태(State) / 이벤트(Event) / 전이(Transition)

가드(Guard) / 불변성(Invariants)

전이별 필수 후처리(Post-Transition Hooks) 포인트

이 문서는 다음을 정의하지 않는다:

실제 오케스트레이션 구현

저장소/WORM/서명 키 관리 구현

UI/리포트 포맷

1) Core Concepts

reset_case_id: Reset 절차 단위의 불변 식별자(UUID).

동일 케이스는 재활성화하지 않는다. 재시도는 항상 새 reset_case_id.

reset_candidate: 체인 검증 결과가 “리셋 후보”임을 표시하는 플래그.

중요: 자동 실행이 아니라 후보 플래그일 뿐이다.

separation of duties: 승인자와 실행자는 분리되어야 한다(기본 정책).

2) States
S0 IDLE

정상 상태. 리셋 케이스가 활성화되어 있지 않다.

S1 PROPOSED

reset_case_id가 생성되고, 원인/근거가 첨부된 “제안” 상태.
아직 리뷰/승인 없음.

S2 UNDER_REVIEW

검토 진행 상태. 승인 요건/증거 수집/리스크 평가 수행.

S3A APPROVED

승인 완료. 쿨오프 및 실행 준비 단계로 진입 가능.

S3R REJECTED

리셋이 부적절/불필요하다고 판단되어 거부됨.

S4E EXECUTED

리셋 실행 완료. 새 GENESIS/새 chain_head가 활성화된 상태.

S4B ABORTED

제안/리뷰/승인 이후라도 중단된 상태(조건 미충족 발견, 준비 실패 등).

3) Events

EV_PROPOSE(reset_case)

EV_START_REVIEW(review_assignment)

EV_APPROVE(approval_bundle)

EV_REJECT(reject_reason)

EV_ABORT(abort_reason)

EV_EXECUTE(execution_plan)

EV_FINALIZE(finalization_report) (EXECUTED 후 자동 finalize용)

4) Allowed Transitions
기본 경로

IDLE --EV_PROPOSE--> PROPOSED

PROPOSED --EV_START_REVIEW--> UNDER_REVIEW

UNDER_REVIEW --EV_APPROVE--> APPROVED

APPROVED --EV_EXECUTE--> EXECUTED

EXECUTED --EV_FINALIZE(auto)--> IDLE(new_chain_head)

종료/중단 경로

UNDER_REVIEW --EV_REJECT--> REJECTED

PROPOSED --EV_ABORT--> ABORTED

UNDER_REVIEW --EV_ABORT--> ABORTED

APPROVED --EV_ABORT--> ABORTED

재제안(항상 새 케이스)

REJECTED --EV_PROPOSE(new reset_case_id)--> PROPOSED

ABORTED --EV_PROPOSE(new reset_case_id)--> PROPOSED

5) Guards (Hard Conditions)
G1 Proposal Guard (자동 후보 ≠ 자동 실행)

EV_PROPOSE는 아래를 반드시 포함해야 한다:

reset_case_id (UUID)

validator_snapshot (status/errors/warnings/stats + health_score/grade + reset_candidate flag)

proposal_actor_id + role/tier

ticket_id 또는 incident_id

proposal_reason

추가 규칙:

Validator는 reset_candidate=True인 스냅샷을 생성할 수 있으나,
이는 “자동 실행”이 아니라 “자동 후보 플래그”일 뿐이며,
상태 전이는 반드시 EV_PROPOSE로 명시적으로 시작되어야 한다.

G2 Review Start Guard

EV_START_REVIEW는 아래를 반드시 포함:

review_id

reviewer/approver 후보(역할/티어 포함)

G3 Approve Guard (Separation of Duties + Cool-off + Drift 강화)

EV_APPROVE는 아래를 반드시 만족:

승인 번들(approval_bundle):

approver_id, role/tier, signature, approved_at_utc, ticket_id

승인자 수/조합 (정책 파라미터, 최소 하한 LOCK)

기본: T2 ≥ 1 AND T3 ≥ 1

동일인 금지 (separation of duties)

approver_id는 서로 달라야 한다.

쿨오프(LOCK 수치)

기본 쿨오프: 24시간

긴급 플래그(emergency=True) 허용 시:

쿨오프: 1시간

추가 조건: T3 승인 2명 이상

TIME_DRIFT 강화 규칙 (LOCK)

TIME_DRIFT 경고가 존재하면:

승인 요건에 +1 (추가 승인자 1명) 요구

단, TIME_DRIFT는 단독으로 reset_candidate를 생성하지 않는다.

다른 치명적 오류와 함께 나타날 때 “리뷰 강화 플래그”로만 작동.

G4 Execute Guard (승인/선언/환경 일치)

EV_EXECUTE는 아래를 반드시 만족:

현재 상태가 APPROVED

execution_plan 포함:

old_head_hash

target_evidence_dir

new_genesis_params (또는 생성 방식)

승인 번들 검증 통과

승인 이후 환경 변화 감지(선택 강화)

승인 시점의 git_commit / config_fingerprint가 바뀌면

(정책) 재승인 요구 또는 실행 거부

G5 Finalize Guard (EXECUTED → IDLE)

EV_FINALIZE(auto)는 아래를 반드시 만족:

chain_head.json 갱신 검증 통과

RESET_DECLARATION 존재 + 서명 검증 통과

declaration에 old_head_hash ↔ new_genesis_hash 링크 존재

6) Post-Transition Hooks (필수 후처리)

각 전이 직후 반드시 수행/기록되어야 하는 후처리 포인트를 “의무”로 고정한다.

IDLE -> PROPOSED:

PROPOSAL_RECORD 작성 (reset_case_id 포함)

UNDER_REVIEW -> APPROVED:

APPROVAL_BUNDLE 서명 검증 기록

APPROVED -> EXECUTED:

RESET_DECLARATION 생성 및 해시 체인 포함

chain_head 갱신

UNDER_REVIEW -> REJECTED:

DECISION_RECORD + 재발 방지 노트(prevention_note) 포함

* -> ABORTED:

ABORT_RECORD + prevention_note 포함

EXECUTED -> IDLE:

finalize 검증 기록 + new_chain_head 스냅샷 기록

7) RESET_DECLARATION (강화 LOCK)

RESET_DECLARATION은 다음을 반드시 포함해야 한다:

Signed JSON

hash-chain fields 포함 (prev_hash/this_hash 규칙은 Evidence 규격과 동일)

old_head_hash ↔ new_genesis_hash 링크

approval_bundle(또는 approval_bundle 해시 참조)

executed_by (executor_id) + executed_at_utc

reset_case_id

8) Invariants (Non-negotiable)
I1 No Direct Reset

IDLE -> EXECUTED 전이는 영구 금지

구현은 “edge 자체를 금지”해야 한다.

I2 No Execution Without Approval

PROPOSED/UNDER_REVIEW -> EXECUTED 전이는 영구 금지

I3 Declaration-First, Verified

EXECUTED 입장 조건:

RESET_DECLARATION exists == True

RESET_DECLARATION verified == True

I4 Multiple Genesis Policy Split

Validator 레벨:

MULTIPLE_GENESIS 탐지 시 status=FAIL, grade=C/D, reset_candidate=True

FSM 레벨:

자동 실행 금지, 리뷰 강제

I5 Single Active Genesis Principle

동시에 유효한 GENESIS는 1개를 원칙으로 한다.

예외(의도적 reset)는 승인/선언/검증으로만 정당화된다.

9) 권한 모델 (LOCK 최소안)

T1: 자동 후보 생성(validator 관측), 제안 이벤트 생성은 가능(또는 T2 필요로 정책화 가능)

T2: 리뷰 시작 가능, 승인 가능(단, 실행 불가)

T3: 승인 가능 + 실행 가능(단, separation of duties 준수)

기본 분리 규칙:

실행자(executor_id)는 승인자 집합에 포함될 수 없음(기본 권장, 필요시 정책 파라미터로 완화 가능)

적용 결과

“리셋 필요 후보”는 자동으로 올라올 수 있어도,

승인/쿨오프/분리권한/선언검증 없이는 절대 실행되지 않는다.