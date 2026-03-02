doc_id: INCIDENT_CLASSIFICATION_MATRIX_v1.0
status: FREEZE
semver: v1.0.0
bundle: OBS_SECURITY_FREEZE_BUNDLE
locked_at: 2026-03-02 KST
change_policy: "Any change requires v1.0.1+ via governance amendment"

# INCIDENT CLASSIFICATION MATRIX v1.0

## 1. Purpose

런타임 INCIDENT를 정량적으로 SEV 등급으로 분류하기 위한 단일 기준(SSOT).

---

## 2. Severity Levels

| Level | 의미 | 운영 영향 |
|-------|------|------------|
| SEV-1 | 경미 | 자동 재시도 |
| SEV-2 | 반복 가능성 | 모니터링 |
| SEV-3 | 전략 위험 | 전략 차단 가능 |
| SEV-4 | 보안 위험 | 전역 차단 |

---

## 3. Sustained Rule

sustained SEV-3 =
동일 code 기준 60분 내 3회 이상 발생

---

## 4. Escalation

- SEV-4 1회 → GLOBAL RED
- sustained SEV-3 → 전략 RED

---

## 5. Time Standard

판단 기준은 시스템 로그 타임스탬프 (UTC+9, ms precision)

---

## 6. Evidence Format

로그는 JSONL(.jsonl) 형식으로 저장한다.