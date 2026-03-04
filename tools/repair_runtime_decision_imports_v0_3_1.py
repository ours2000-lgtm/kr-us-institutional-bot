from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # project root
FILES = {
    ROOT / "runtime" / "decision" / "reason_mapper_v1_2.py": """from __future__ import annotations

from typing import Optional

from runtime.decision.reason_code import ReasonCode
""",
    ROOT / "runtime" / "decision" / "runtime_decision.py": """from __future__ import annotations

from dataclasses import dataclass

from runtime.decision.reason_code import ReasonCode
""",
    ROOT / "runtime" / "decision" / "runtime_decision_factory.py": """from __future__ import annotations

from runtime.decision.reason_code import ReasonCode
from runtime.decision.runtime_decision import RuntimeDecision
""",
}

BAD_PATTERNS = [
    "runtime.runtime",
    "from decision.reason_code import ReasonCode",
    "from runtime.runtime.decision.reason_code import ReasonCode",
]


def _rewrite_header_only(path: Path, new_header: str) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(True)

    # 헤더(첫 blank line까지)만 교체: imports/dunder/docstring 등 초반부를 통째로 고정
    # 안전하게: 파일 시작부터 첫 "빈 줄 2번 연속" 또는 첫 함수/클래스 정의 직전까지를 헤더로 판단
    # 여기서는 간단히: 첫 번째 "def " / "class " / "@dataclass" / "REASON_TO_CODE" 같은 본문 신호를 찾아 그 전까지 교체
    cut_idx = None
    for i, line in enumerate(lines):
        s = line.lstrip()
        if s.startswith("def ") or s.startswith("class ") or s.startswith("@") or s.startswith("REASON_") or s.startswith("REASON_TO_"):
            cut_idx = i
            break

    if cut_idx is None:
        # 못 찾으면 파일 전체를 헤더로 보고 새 헤더 + 원문
        cut_idx = 0

    body = "".join(lines[cut_idx:])
    path.write_text(new_header + "\n" + body.lstrip("\n"), encoding="utf-8")


def _assert_no_bad(text: str, path: Path) -> None:
    for p in BAD_PATTERNS:
        if p in text:
            raise RuntimeError(f"[BAD PATTERN] {p} found in {path}")


def main() -> None:
    # 1) 대상 3개 파일 존재 확인
    for p in FILES:
        if not p.exists():
            raise FileNotFoundError(f"Missing file: {p}")

    # 2) 헤더를 SSOT로 고정 교체
    for path, header in FILES.items():
        _rewrite_header_only(path, header)

    # 3) runtime/decision/*.py 전체에서 runtime.runtime 오염 제거(있으면 실패)
    for path in (ROOT / "runtime" / "decision").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        _assert_no_bad(text, path)

    print("OK: decision imports repaired and validated.")


if __name__ == "__main__":
    main()