# AMENDMENT_PROCEDURE.md (v1.0 Ratified — 2025-12-28, Commit d11d332)

## Section 0: The Constitutional Premise
**0.1 Nature of Document:** 본 문서는 시스템의 '헌법' 그 자체가 아니며, 헌법 v1.0의 무결성을 수호하기 위한 '개정 절차법'입니다.
**0.2 Precedence:** 모든 개정 절차는 본 문서의 규정을 따라야 하며, 이를 통과하지 않은 변경은 원천 무효입니다.
**0.3 Nullification Rule:** 절차적 결함이 발견된 모든 개정안은 발견 시점과 관계없이 '즉각 무효화(Null and Void)'되며, 시스템은 직전의 검증된 기준선(Baseline)으로 롤백됩니다.

## Section 1: Non-Goals (What we reject)
본 절차는 다음을 목표로 하지 않으며, 이를 위해 설계되지 않았습니다.
* **Rejecting Efficiency:** 우리는 의사결정의 속도와 효율성을 명시적으로 거부합니다.
* **Rejecting Unverified Innovation:** 검증되지 않은 혁신보다 기존 안전 기준선의 유지를 우선합니다.
* **Friction as Design:** 우리의 목표는 개정을 어렵게 만드는 '의도적 마찰'을 제공하는 것입니다.

## Section 2: Gatekeeping & Disqualifiers
### 2.1 The Gatekeeping Principle
모든 개정 제안은 실질적 내용 검토 이전에 '절차적 결격 사유'를 먼저 심사받습니다.
### 2.2 Absolute Disqualifiers (즉각 실격 사유)
다음 중 하나라도 해당할 경우, 제안은 실질적 검토 없이 즉각 기각됩니다.
1. Section 0~3(핵심 가치) 및 LOCK Rules의 강제력을 약화시키는 시도.
2. 제안자의 책임 범위를 모호하게 하거나 면책을 시도하는 조항.
3. 소급 적용(Retroactive) 또는 특정 상황에 대한 예외 조항의 신설.
4. 동일 회차 내에서 이미 기각된 제안의 단순 재제출.

## Section 3: Constitutional Impact Assessment (CIA) Model
모든 제안은 헌법적 무결성을 검증하기 위한 다음 3대 평가 차원을 통과해야 합니다.
**3.1 The Principle: In Dubio Pro Baseline**
모든 평가 과정에서 모호함이나 불확실성이 발생할 경우, 기존 기준선을 우선합니다. 안정성(Stability)과 보수성(Conservatism)이 절대적 우선순위를 가집니다.
**3.2 Dimension 1: Baseline Delta Type**
* **Additive:** 새로운 안전장치나 절차의 추가.
* **Supplementary:** 기존 조항의 의미 명확화.
* **Substitutive:** 기존 로직 변경 (거부 추정을 전제로 한 가장 엄격한 심사 대상).
**3.3 Dimension 2: Constitutional Impact**
모든 제안은 직접 영향(Direct Impact)과 간접 영향(Indirect Impact) 두 차원 모두에 대해 필수적으로 평가되어야 합니다.
**3.4 Dimension 3: Residual Safety Margin**
개정 후에도 시스템의 안전 마진이 v1.0의 최소 안전 허용치(Minimum Threshold)를 상회함을 논리적·정량적 근거와 함께 입증해야 합니다.

## Section 4: Proposal Package Requirements
제안자는 다음 규격을 충족하는 산출물을 제출해야 합니다. 미달 시 즉각 기각됩니다.
**4.1 Constitutional Diff:** Unified/Side-by-side 포맷의 텍스트 변화 및 권한·제약 구조의 의미적 변화 기술(Semantic Layer).
**4.2 CIA Evidence Report:** 직접/간접 영향 구분 기술 및 수학적 모델, 시뮬레이션, 테스트 로그를 포함한 실증적 증거.
**4.3 ID Traceability & Heritage Ledger:** `YYYYMMDD-NN` 형식 준수 및 이전 거절 사유에 대한 구조적 해소 증명(Refutation).
**4.4 Constitutional Compatibility Oath:** 허위·은폐 발견 시 모든 책임을 인정하며, 서명/날짜/역할을 명시한 선언문.

## Section 5: Approval Model (Three-Key Consensus)
**5.0 The Non-Authority Nature of Approval**
승인은 권력의 행사가 아닌 '헌법적 보증(Constitutional Guarantee)' 행위입니다.
* **No Creative Power:** 승인권자는 제안 내용을 임의로 수정하거나 새로운 조항을 창조할 수 없습니다.
* **Binary Verification:** 오직 Section 2.2, 3, 4의 기준 충족 여부만 이진적(Pass/Fail)으로 검증합니다.
* **Liability:** 서명은 해당 개정이 기준선을 침해하지 않음을 자신의 역할을 걸고 확약하는 책임 행위입니다.

## Section 6: Rejection, Resubmission, and Cooling-off
**6.1 Finality:** 기각된 제안은 즉시 무효 처리되며, 동일 회차 내 수정·보정 재제출은 금지됩니다.
**6.2 Cooling-off Period:** 거절 결정일로부터 기산하여 최소 숙려 기간을 가집니다.
* **Type A, B:** 최소 14일 / **Type C (Substantive):** 최소 30일 및 1회 정규 회기 간격.
**6.3 Resubmission:** 단순 표현 변경이 아닌 구조적 해소를 증명하는 새로운 CIA Evidence Report가 필수입니다.
**6.4 Blacklisting:** 부적격 사유 미보완 반복 제출 시 '절차적 방해'로 간주하여 최소 90일간 제안 권한을 박탈합니다.

## Section 7: Recording, Traceability, and Audit
**7.1 Immutable Audit Trail:** 성공, 실패, 철회된 모든 시도를 Tamper-evident Ledger에 기록합니다. 각 서명자의 역할별 검토 의견을 포함합니다.
**7.2 External Hooks:** Git PR Link, ARB 회의록, 그리고 SHA-256 및 SHA-3 다중 알고리즘 해시 스냅샷을 기록합니다.
**7.3 Periodic Audit:** 분기별 1회 독립 감사자가 전수 조사를 수행하며, 결과는 공개 보고서로 발행됩니다.

## Section 8: Relationship to Versioning & Change Control
**8.1 Dependency:** 본 절차는 Section X(Versioning)에 종속됩니다. 이 절차를 거치지 않은 버전 증분은 단순 기술적 태그일 뿐 헌법적 효력이 없습니다.
**8.2 Governance Precedence:** 거버넌스 승인 이전에 이루어진 어떠한 기술적 병합(Merge)이나 태깅도 무효이며 즉각 교정 대상입니다. Audit Trail과 Git Hash는 양방향 검증되어야 합니다.

## Section 9: Failure Modes & Invalid Amendments
다음 결함 발견 시 해당 개정은 헌법상 부적격(Constitutionally Ineligible)으로 간주됩니다.
* **Technical:** 해시 불일치, 승인 전 태깅, 증거 자료의 실질적 미달.
* **Governance:** 승인권자 누락, 실격 사유(Section 2.2) 우회 승인, 숙려 기간 위반.
* **Remedy:** 발견 즉시 롤백 및 영향 분석 기록, 주동자 블랙리스트 등록. 재검토는 불가능합니다.

## Section 10: Closing Statement (The Philosophy of Friction)
**"The Friction is the Safeguard."** 본 절차는 의도적인 마찰을 통해 시스템의 영속성을 보장합니다. 기준선(Baseline)은 모든 개정의 출발점이자 귀착점인 사회적 계약입니다.
> "단 하나의 근본적인 안전 보장이 훼손되는 것보다 천 개의 혁신이 기다리는 것이 낫다."
이것이 본 절차가 설계된 이유이며, 시스템에 허용된 유일한 편향입니다. 본 문서는 이제 봉인되었습니다.