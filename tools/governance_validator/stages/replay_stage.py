from __future__ import annotations

from typing import List

from ..io import EvidenceBundle
from ..result_contract import Severity, Violation


def replay_verify(bundle: EvidenceBundle) -> List[Violation]:
    # v0.1: placeholder
    # 이후: canonicalize → validate_again → stable 결과 비교
    return []
