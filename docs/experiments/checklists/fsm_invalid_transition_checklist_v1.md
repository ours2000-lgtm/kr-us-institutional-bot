FSM_INVALID_TRANSITION — Execution Checklist v1.0 (Sample-Generator Based)
0) Checklist Metadata

checklist_id: FSM_INVALID_TRANSITION_CHECKLIST_v1.0

checklist_status: FIRST_USE_DRAFT (첫 실행 후 LOCK 전환 후보)

experiment_plan_ref: docs/experiments/experiment_plan_fail_injection_v1.1.md (있으면 링크, 없으면 N/A)

operator_id: <ENUM or short-id> (예: OP_DH01)

environment_type: <ENUM> (예: ISOLATED_SANDBOX_V3 / STAGING_SLICE_A)

environment_notes: FSM emitter: sample-generator-based only (runtime emitter NOT deployed)

scope: single run_id only; no concurrent experiments

1) run_id / Prefix

run_id: EXP_FAIL_INJECT_YYYYMMDD_FSM_ILLEGAL_TRANSITION_01

market_tag: <KR|US|CRYPTO>

engine_id: <ENGINE_V30|...>

2) Injection Definition (exactly once)
2.1 Injection Location (current implementation, v1.0)

file: logs/evidence/_specs/make_fsm_jsonl_sample.py

function: build_record_payload(...)

hook_point: return finalize_with_hash(obj) 직전 (obj가 완성되고 해시 계산 전에 1회 덮어쓰기)

2.2 Future Runtime Location (placeholder)

TBD: audit_fsm_emit.emit_transition(...) right before append_jsonl(...)

2.3 Illegal Transition Choice (spec-aligned)

from_state: S0_INIT

to_state: <ILLEGAL_TO_STATE> (fsm_definition_v1.json에서 S0_INIT outbound에 없는 상태 1개 고정)

verified_precheck:

 fsm_definition_v1.json에서 (S0_INIT -> <ILLEGAL_TO_STATE>) 가 allowed_transitions에 없음 확인

2.4 Enable Flag / Once Token

enable_flag: ops.fail_inject.fsm_invalid_transition.enabled

once_token_store: fsm_context.experiment_once_tokens

once_token_key: fsm_invalid_transition_once

once_rule:

 enable_flag == true AND once_token not consumed → 주입 실행

 주입 직후 once_token consumed → 다시 주입 금지

3) Hypothesis / Success Criteria (validator-level)
3.1 Expected outcomes

 verification summary.outcome == FAIL

 verification summary.fail_code == FSM_INVALID_TRANSITION

 validator check FSM_TRANSITION_ALLOWED (또는 동등 check_id) status == FAIL

 illegal transition violations == exactly 1

3.2 Non-goals (this checklist v1.0)

 Runtime “engine stop / fail-closed halt” 는 본 실험에서 검증하지 않음 (TODO: runtime-emitter checklist에서 검증)

4) Evidence Expectations (paths + integrity)
4.1 FSM transitions evidence

evidence_jsonl_path:

logs/evidence/rehearsal/fsm/fsm_transitions_<run_id>.jsonl

constraints:

 file_size_bytes > 0

 jsonl parse 성공 (0 parse error)

 expected run_id 포함

 (from_state=S0_INIT, to_state=<ILLEGAL_TO_STATE>) 매칭 count == 1

4.2 SHA256 integrity artifacts

sha256_sidecar_path (권장 고정):

logs/evidence/rehearsal/fsm/fsm_transitions_<run_id>.jsonl.sha256

hash_generation_timing:

 JSONL 생성 직후, validator 실행 직전 1회 계산

verification_report requirements:

 verification_report_v1.json에 입력 JSONL의 sha256 및 검증 결과 포함
(예: report.inputs.fsm_transitions.sha256 == actual file sha256)

4.3 Verification report location (example)

report_path (example):

logs/evidence/rehearsal/verification/verification_report_<run_id>.json

5) Abort Conditions (concrete)

Abort if ANY occurs:

 file_size == 0

 JSON parse failure (FSM_FILE_PARSE / PARSE_ERROR)

 expected run_id missing in evidence

 hash-chain break / unexpected spec violation (FSM_HASH_CHAIN_BROKEN 등)

 illegal transition 미탐지인데 다른 SPEC_VIOLATION이 뜸 (샘플/주입 설계 문제로 간주)

 실험 범위를 벗어난 보안/무결성 징후 관측 → 실험 중단 + IR/runbook으로 전환

Abort action:

 classify as SPEC_VIOLATION

 evidence 보존 + audit trail 기록 + experiment_report 작성

6) Execution Steps (with checks)
Step A — Generate evidence (sample-generator)

 sample generator로 JSONL 생성 (run_id 포함)

Step B — Pre-check counts

 JSONL에서 illegal transition grep/count == 1

Step C — Run validator / CI

 python tools\ci\validate_contracts_v1.py (컨트랙트 가드)

 python logs\evidence\_specs\fsm_transitions_validator_v1.py --fsm-transitions <path> (실제 커맨드는 repo 기준으로 맞추기)

Step D — Confirm report fields

 summary.outcome == FAIL

 summary.fail_code == FSM_INVALID_TRANSITION

 inputs.fsm_transitions.sha256 matches actual

7) Post-Experiment (traceability)

Create experiment_report.json (권장):

report_path (example):

logs/experiments/<run_id>/experiment_report.json

Mandatory fields:

checklist_id: FSM_INVALID_TRANSITION_CHECKLIST_v1.0

fsm_emitter_type: sample-generator

run_id, environment_type, operator_id

result: SUCCESS|FAIL

findings: ...

next_action_plan_ref: <doc/path or issue-id> (재실행 추적용)

LOCK transition rule:

 첫 실행이 “가설 충족 + abort 없음”이면 checklist_status를 LOCK_CANDIDATE로 승격(승인 절차는 plan에 따름)