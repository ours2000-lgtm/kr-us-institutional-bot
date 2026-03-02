doc_id: GOV_HEALTH_MODEL_v1.0
status: FREEZE
semver: v1.0.0
bundle: OBS_SECURITY_FREEZE_BUNDLE
locked_at: 2026-03-02 KST
change_policy: "Any change requires v1.0.1+ via governance amendment"

# GOV_HEALTH MODEL v1.0

## 1. Purpose

INCIDENT 분포를 전략 단위 및 글로벌 단위 HEALTH 상태로 집계한다.

Health model MUST remain read-only analytics.

---

## 2. Strategy States

- GREEN
- YELLOW
- RED

---

## 3. Global Aggregation (Weighted)

w(s) =
- 1.0 if RED
- 0.5 if YELLOW
- 0.0 if GREEN

W_global = Σ w(s)

결정 규칙:
- 0 → GREEN
- (0,2) → YELLOW
- ≥2 → RED

---

## 4. Cool-down Rule

cool_down_period 동안
sev ≥ SEV-2 신규 이벤트 0건일 것