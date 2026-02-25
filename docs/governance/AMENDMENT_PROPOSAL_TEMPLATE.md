# [PROPOSAL-ID] 제안 제목: <TITLE_HERE>

## 0. 메타데이터 (Metadata)
- **제안자:** @username
- **Proposal Version:** v1.0
- **Last-Updated:** 2025-12-28
- **Change Type:** [Type A / Type B]
- **Related WHAT_COUNTS Clause:** (예: §2 Case 1 / §3 Case 2)
- **History:** (이전 PR 링크 및 Revert Commit Hash 필수 기재. 신규 시 'N/A')
- **CIA Evidence Reference:** ./CIA_EVIDENCE_[PROPOSAL-ID].md (Type A 필수)

---

## 1. 제안 개요 (Abstract)
- **변경 배경 및 목적:**
- **적용 범위 (Scope of Application):** (전체 시스템 / 특정 모듈 / 특정 파라미터 그룹)

## 2. Baseline Delta (변경 전후 상세 비교)
| 구분 | 변경 전 (As-Is) | 변경 후 (To-Be) | 영향 받는 Invariant / 조항 |
| :--- | :--- | :--- | :--- |
| **핵심 수치/로직** | `VALUE_A` | `VALUE_B` | `INVARIANT_X` |
| **권한/조직 구조** | `ROLE_A` | `ROLE_B` | `AUTHORITY_Y` |
| **절차 변수** | `PERIOD_A` | `PERIOD_B` | `PROCEDURE_Z` |
| **부수적 영향** | `NONE` | `EFFECT_B` | **Secondary Effects (간접 영향)** |

---

## 3. Residual Margin 계산 및 검증 (Technical Integrity)
> **[의무 계산식]**
> $Residual Margin = Current Margin - Delta$

- **Current Margin:**
- **Delta:**
- **Residual Margin:**
- **허용 오차 (±ε):**
- **Min Threshold:** (constitution.md §X.Y 참조)
- **검증 로그 참조:** [CIA Evidence Section #] / [Unique Log ID 필수]
- **검증 방법론 요약:** (사용한 시뮬레이션 도구 및 테스트 데이터 셋 상세 명시)

> **검증 결과:** Residual Margin이 Min Threshold 이상임을 확인하였는가? [ ] YES / [ ] NO
> **검증자 서명 (Sign-off):** @validator_username (**역할/Role:** 예: Security Auditor)
> **검증자 코멘트:** (방법론 재확인 및 수치 외 맥락적 특이사항 기술)

---

## 4. 리스크 분석 및 사후 대응 (Risk & Contingency)
- **기술적/거버넌스/운영 리스크:**
- **완화 대책 및 권장 보완 조치:**
- **사후 대응책 (Fallback Plan):** (이상 발생 시 즉각적인 롤백 절차 및 트리거 조건)
- **비상 보고 체계 (Escalation Path):**
  - **주 경로 책임자:** [Role 명시] / [SLA: 사고 인지 후 X시간 이내 대응 결정]
  - **대체 경로(Backup Path):** [비상 의사결정 책임자 Role] / [부재 시 권한 자동 승계 조건]
- **모니터링 체계 (Monitoring Lifecycle):**
  - **Standard (필수):** 단기(72h), 중기(7d), 장기(30d)
  - **Optional Extended (선택):** 영속성(90d~180d), 초장기(1y~20y) 안정성 평가

---

## 5. 투표 및 집행 정보 (Procedure)
- **집행 적용 범위 재확인:** (위 1. Abstract의 Scope와 일치 여부 필수 확인)
- **집행 책임자 (Role):** (가결 후 실제 시스템 반영을 책임질 주체/그룹)
- **적용 방식:** [ ] 즉시 적용 (Immediate) / [ ] 단계적 적용 (Phased)
- **정족수 요구사항:** (AMENDMENT_PROCEDURE.md v1.0 기준)
- **Cooling-off 기간:** (최소: X일 / 최대: Y일 범위 내 기재)
- **Effective Date:** (실제 시스템 적용 예정 일자)

---
**Failure to comply with this template indicates non-conformance with the governance system.**