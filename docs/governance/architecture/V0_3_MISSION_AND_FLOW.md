1. v0.3 미션 한 줄 재정리
PLAN→VAL→ROLLOUT 그래프가 단순 reachability가 아니라, VAL 불변식을 만족하는 경로로만 ROLLOUT을 통과시키고, 그 판정을 재현 가능한 Evidence/Record로 남긴다.emergentmind+1
문장 버전 그대로 써도 괜찮아:
PLAN→VAL→ROLLOUT 그래프가 ‘형식상 연결’이 아니라, ‘헌법(불변식)을 만족하는 경로’로만 통과되게 만들고, 그 판단 자체를 Evidence로 남긴다.arxiv​
2. v0.3 전체 흐름 (운영 관점 SSOT)
이 플로우를 SSOT로 고정해두면 될 것 같아.arxiv​
Runtime/Tool: 그래프 스냅샷 생성
nodes[], edges[] + edge metadata(snapshot_id, timestamps, principals 등).arxiv​
ConsistencyChecker v0.3 실행
A. Graph validators (v0.2 유지): DAG, required edges, no duplicates, edge metadata 최소 조건.arxiv​
B. STRICT Reachability: PLAN→…→ROLLOUT 경로 중 “VAL 불변식을 만족하는 VAL을 포함하는 경로”만 유효로 인정.arxiv​
enforce(mode=warn/block/strict)
allowed / blocked 결정.arxiv​
Compliance Record Stub 생성/발행
snapshot_id(or graph_hash) + violations + decision + principal + timestamp_utc + mode.hoop​
on_record 훅으로 Evidence 파이프라인/스토리지로 전송.hoop​
여기까지가 v0.3의 “운영 관점” 단일 진실원으로 보이게 정리된 상태.
3. strict reachability 정의 (헌법 문장)
너가 쓴 정의를 그대로 헌법 톤으로 고정해도 탄탄해.arxiv​
v0.2: “PLAN에서 ROLLOUT까지 경로가 있으면 OK.”arxiv​
v0.3 strict:
경로에 VAL이 반드시 포함되어야 하고,
그 VAL은 VAL invariants(특히 PLAN_TO_VAL exactly one upstream PLAN)를 만족해야 한다.arxiv​
헌법 문장:
Every ROLLOUT MUST be reachable from at least one PLAN via a path that includes a VAL which itself satisfies VAL invariants (including exactly one upstream PLAN_TO_VAL).arxiv​
추가 invariant 한 줄만 더 붙이는 것도 가능:
Any VAL that has zero or more than one upstream PLAN_TO_VAL edge MUST NOT be considered part of a valid PLAN→VAL→ROLLOUT path.arxiv​
이렇게 하면 “orphan/ambiguous VAL은 경로에서 탈락”이 명확해짐.
4. Compliance Record Stub 계약 (v0.3)
Stub를 이렇게 정의하면 v0.4 Evidence로 자연스럽게 승격 가능해 보여.hoop​
4.1 계약 문장
“Every enforce() call MUST produce exactly one ComplianceRecord, regardless of decision (allowed/blocked).”hoop​
“The decision MUST be derivable from (snapshot_id or graph_hash) + violations + mode, once policy semantics are fixed.”hoop​
4.2 필드 최소안 (SSOT)
snapshot_id 또는 graph_hash
violations: [{code, severity, message}]
mode: "warn" | "block" | "strict"
decision: "allowed" | "blocked"
timestamp_utc (ISO8601 UTC)
principal: {type: "human" | "service", id: "..."}
이 정도면 “나중에 EVID-CONSISTENCY-RUN으로 이관” 시에도 정보 손실 없이 매핑 가능.hoop​
추가로 선택 필드 하나 정도만 추천:
policy_ref (있다면, 어떤 정책/규칙에 따라 enforce했는지 추적 가능)hoop​
지금은 optional로 두고, v0.3 후반 aggregation/policy 붙일 때 required로 승격하면 됨.
5. aggregation/policy를 “다음 타자”로 두는 구조
구조적으로는 이렇게 단계화가 깔끔해 보여.arxiv​
v0.3 앞반:
STRICT reachability + ComplianceRecord stub + enforce(mode) 확정.
v0.3 뒷반:
ValidationOutcome 집계 (ANY_FAIL_BLOCK, MIN_PASS_THRESHOLD 등)
policy_ref를 enforcement 입력으로 승격, Evidence에 기록.
그래서 지금 턴에서는:
strict reachability 헌법
enforce(mode) + ComplianceRecord 1줄 보장
까지가 “락” 포인트.
6. v0.3 산출물(파일/테스트 단위) + 내가 보이는 보완점
네가 잡은 세 개 그대로 가는 것을 추천하고, 각 파일에서 “반드시 테스트할 케이스”만 추가로 박아볼게.skgraph​
6.1 src/integration_core/consistency.py
포함해야 할 것:
Graph validators (기존 유지).
strict reachability 구현:
VALID VAL = “exactly one PLAN_TO_VAL upstream” + 기타 VAL invariants.
ROLLOUT마다 “valid PLAN→VAL→ROLLOUT path 존재 여부” 계산.
enforce(mode, on_record):
mode에 따라 decision(allowed/blocked) 결정.
ComplianceRecord 생성 후 on_record 호출.
보완 포인트 한 줄:
“strict 모드에서 ‘valid path 없음’은 반드시 blocked” 라는 invariant를 docstring/헬퍼로 명시해두는 게 좋음.arxiv​
6.2 tests_mvp/integration_core/test_consistency_strict_reachability.py
필수 시나리오:
valid 단일 체인:
PLAN1 → VAL1 → ROLLOUT1 (VAL1이 exactly one PLAN_TO_VAL) → allowed.arxiv​
orphan VAL:
VAL이 PLAN_TO_VAL 없이 있거나, 어느 PLAN에서도 도달 못함 → ROLLOUT1은 blocked.arxiv​
multi PLAN edges VAL:
PLAN1 → VAL1, PLAN2 → VAL1 (PLAN_TO_VAL 두 개) → VAL1은 invalid, 이 VAL을 포함하는 경로는 무효.arxiv​
multiple VAL 경로:
하나의 ROLLOUT에 대해,
경로1: invalid VAL 포함,
경로2: valid VAL 포함 → “하나라도 valid path 있으면 allowed”.arxiv​
6.3 tests_mvp/integration_core/test_compliance_stub.py
필수 시나리오:
enforce() 한 번 호출 → ComplianceRecord 정확히 1개 생성.
decision = allowed일 때도 record 생성되는지 확인.
mode별 동작:
mode="warn": blocked 조건이어도 decision은 allowed 가능하지만, violations가 채워지고 record 남는지.
mode="block"/"strict": 동일 조건에서 decision이 blocked인지.hoop​
principal/ timestamp_utc 가 누락 없이 세팅되는지.
추가로 권장:
on_record 훅에 더미 콜백 넣고, “항상 딱 한 번 호출”되는지 assert.
snapshot_id vs graph_hash 둘 중 하나만 채우는 케이스도 허용할지, 아니면 graph_hash required로 갈지 결정해서 테스트에 반영.