from __future__ import annotations

from typing import List, Optional

from ..io import EvidenceBundle
from ..result_contract import Severity, Violation


# v0.1: JSON Schema draft-07 실제 검증은 다음 커밋에서 연결
# 확장 시, 각 위반에 {"schema_id": "...", "schema_path": "..."}를 refs로 남겨 감사/디버깅 가시성 확보.
def _mk_schema_ref(schema_id: Optional[str], schema_path: Optional[str]):
    ref = {}
    if schema_id:
        ref["schema_id"] = schema_id
    if schema_path:
        ref["schema_path"] = schema_path
    return ref


def schema_validate_all(bundle: EvidenceBundle) -> List[Violation]:
    violations: List[Violation] = []

    # v0.1에서는 번들 레벨만 검사하지만,
    # 추후 record별 검증 시 아래 두 값은 실제로 채워지게 될 예정.
    schema_id = "bundle.schema.json"
    schema_path = f"{bundle.schema_set_ref}/bundle.schema.json"
    sref = _mk_schema_ref(schema_id, schema_path)

    if not isinstance(bundle.records, list):
        violations.append(
            Violation(
                code="SCHEMA_BUNDLE_RECORDS_NOT_ARRAY",
                severity=Severity.BLOCKING,
                message="bundle.records must be an array",
                rule_id="SCHEMA-000",
                refs=sref,
            )
        )

    if len(bundle.records) == 0:
        violations.append(
            Violation(
                code="SCHEMA_EMPTY_BUNDLE",
                severity=Severity.BLOCKING,
                message="Evidence bundle contains no records",
                rule_id="SCHEMA-001",
                refs=sref,
            )
        )

    return violations
