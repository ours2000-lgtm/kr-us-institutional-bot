from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# Result Contract
# ============================================================

class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


class RuleCode(str, Enum):
    MISSING_THIS_HASH = "MISSING_THIS_HASH"
    MISSING_PREV_REFERENCE = "MISSING_PREV_REFERENCE"
    BROKEN_LINK = "BROKEN_LINK"
    HEAD_MISMATCH = "HEAD_MISMATCH"
    MULTIPLE_GENESIS = "MULTIPLE_GENESIS"
    TIME_DRIFT = "TIME_DRIFT"
    PAYLOAD_TAMPER = "PAYLOAD_TAMPER"


@dataclass
class Violation:
    rule: RuleCode
    severity: Severity
    message: str
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule.value,
            "severity": self.severity.value,
            "message": self.message,
            "context": self.context,
        }


@dataclass
class ChainStats:
    evidence_count: int
    genesis_count: int
    head_hash: Optional[str]
    tail_hash: Optional[str]
    head_created_at_utc: Optional[str]
    tail_created_at_utc: Optional[str]


@dataclass
class ChainValidationResult:
    status: str
    errors: List[Violation]
    warnings: List[Violation]
    stats: Optional[ChainStats]
    validated_at_utc: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "stats": asdict(self.stats) if self.stats else None,
            "validated_at_utc": self.validated_at_utc,
        }


# ============================================================
# Helpers
# ============================================================

def _utc_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _collect_evidence_files(dir_path: Path) -> List[Path]:
    return sorted(dir_path.glob("validation_*.json"))


def _extract_chain(evidence: Dict[str, Any]) -> Dict[str, Any]:
    return evidence.get("chain", {})


def _extract_created(evidence: Dict[str, Any]) -> Optional[str]:
    return evidence.get("created_at_utc")


# ============================================================
# Core Validator
# ============================================================

def validate_chain(dir_path: Path) -> ChainValidationResult:

    errors: List[Violation] = []
    warnings: List[Violation] = []

    evidence_files = _collect_evidence_files(dir_path)

    if not evidence_files:
        return ChainValidationResult(
            status="PASS",
            errors=[],
            warnings=[],
            stats=None,
            validated_at_utc=_utc_now(),
        )

    evidences = []

    for p in evidence_files:
        try:
            obj = _load_json(p)
            chain = _extract_chain(obj)

            evidences.append({
                "path": p,
                "this": chain.get("this_hash"),
                "prev": chain.get("prev_hash"),
                "created": _extract_created(obj),
            })
        except Exception as e:
            errors.append(Violation(
                rule=RuleCode.PAYLOAD_TAMPER,
                severity=Severity.ERROR,
                message=str(e),
                context={"file": str(p)}
            ))

    # --------------------------------------------------------
    # R1 MISSING_THIS_HASH
    # --------------------------------------------------------
    for ev in evidences:
        if not ev["this"]:
            errors.append(Violation(
                rule=RuleCode.MISSING_THIS_HASH,
                severity=Severity.ERROR,
                message="this_hash missing",
                context={"file": str(ev["path"])}
            ))

    # --------------------------------------------------------
    # R2 LINK CHECK
    # --------------------------------------------------------
    this_set = {ev["this"] for ev in evidences if ev["this"]}

    for ev in evidences:
        prev = ev["prev"]

        if prev and prev != "GENESIS" and prev not in this_set:
            errors.append(Violation(
                rule=RuleCode.BROKEN_LINK,
                severity=Severity.ERROR,
                message="prev_hash does not reference existing this_hash",
                context={"file": str(ev["path"]), "prev": prev}
            ))

    # --------------------------------------------------------
    # R5 MULTIPLE GENESIS
    # --------------------------------------------------------
    genesis = [ev for ev in evidences if ev["prev"] == "GENESIS"]

    if len(genesis) > 1:
        errors.append(Violation(
            rule=RuleCode.MULTIPLE_GENESIS,
            severity=Severity.ERROR,
            message="Multiple GENESIS detected",
            context={"count": len(genesis)}
        ))

    # --------------------------------------------------------
    # R6 TIME DRIFT
    # --------------------------------------------------------
    ordered = sorted(
        [ev for ev in evidences if ev["created"]],
        key=lambda x: x["created"]
    )

    for i in range(1, len(ordered)):
        prev = ordered[i - 1]
        curr = ordered[i]

        if curr["prev"] and curr["prev"] != prev["this"]:
            warnings.append(Violation(
                rule=RuleCode.TIME_DRIFT,
                severity=Severity.WARNING,
                message="Chain order differs from timestamp order",
                context={
                    "prev_file": str(prev["path"]),
                    "curr_file": str(curr["path"]),
                }
            ))

    # --------------------------------------------------------
    # HEAD CHECK
    # --------------------------------------------------------
    head_file = dir_path / "chain_head.json"
    head_hash = None

    if head_file.exists():
        head = _load_json(head_file)
        head_hash = head.get("last_hash")

        if head_hash not in this_set:
            errors.append(Violation(
                rule=RuleCode.HEAD_MISMATCH,
                severity=Severity.ERROR,
                message="chain_head.json mismatch",
                context={"head_hash": head_hash}
            ))

    # --------------------------------------------------------
    # Stats
    # --------------------------------------------------------
    stats = ChainStats(
        evidence_count=len(evidences),
        genesis_count=len(genesis),
        head_hash=head_hash,
        tail_hash=ordered[0]["this"] if ordered else None,
        head_created_at_utc=ordered[-1]["created"] if ordered else None,
        tail_created_at_utc=ordered[0]["created"] if ordered else None,
    )

    status = "FAIL" if errors else "PASS"

    return ChainValidationResult(
        status=status,
        errors=errors,
        warnings=warnings,
        stats=stats,
        validated_at_utc=_utc_now(),
    )


# ============================================================
# CLI ENTRY
# ============================================================

def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)

    args = parser.parse_args(argv)

    result = validate_chain(Path(args.dir))

    print(json.dumps(result.to_dict(), indent=2))

    return 1 if result.status == "FAIL" else 0
