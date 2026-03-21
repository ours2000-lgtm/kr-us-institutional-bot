#!/usr/bin/env python3
"""
validate_contracts_v1.py

Single CI entrypoint for validating v1 canonical contracts.

FAIL behavior:
- Any invariant violation -> exit non-zero
- Soft-fail is forbidden

Exit codes (machine-parseable):
- 0: PASS
- 1: UNEXPECTED_ERROR (catch-all)
- 2: TAXONOMY invariants failed
- 3: SCHEMA guard failed
- 4: BOTH taxonomy + schema failed
"""

import sys
import traceback
from pathlib import Path

from invariants_fail_code_taxonomy_v1 import validate_fail_code_taxonomy
from invariants_verification_report_v1 import validate_verification_report_schema


def _find_repo_root(start: Path) -> Path:
    """
    Repo root discovery without git dependency.

    Rule:
    - repo_root must contain: logs/evidence/_specs/ (directory)

    Notes:
    - We intentionally do not cap traversal depth; it walks to filesystem root.
    - This script is expected to live under tools/ci/, but can still work elsewhere.
    """
    cur = start.resolve()
    visited = []
    while True:
        visited.append(cur)
        candidate = cur / "logs" / "evidence" / "_specs"
        if candidate.exists() and candidate.is_dir():
            return cur
        if cur.parent == cur:
            # reached filesystem root
            break
        cur = cur.parent

    visited_str = "\n  - ".join(str(p) for p in visited[:15])
    raise AssertionError(
        "Cannot locate repo root. Expected to find 'logs/evidence/_specs/' above this script.\n"
        "Searched (top 15):\n  - "
        + visited_str
        + ("\n  - ... (truncated)" if len(visited) > 15 else "")
    )


def _stat_line(path: Path) -> str:
    try:
        st = path.stat()
        return f"size={st.st_size} mtime={st.st_mtime}"
    except Exception:
        return "stat=unavailable"


def main() -> int:
    try:
        script_path = Path(__file__).resolve()
        repo_root = _find_repo_root(script_path.parent)

        taxonomy_path = repo_root / "logs" / "evidence" / "_specs" / "fail_code_taxonomy_v1.json"
        schema_path = repo_root / "logs" / "evidence" / "_specs" / "verification_report_v1.schema.json"

        print("[INFO] repo_root:", repo_root)
        print("[INFO] taxonomy_path:", taxonomy_path, f"({_stat_line(taxonomy_path)})")
        print("[INFO] schema_path:", schema_path, f"({_stat_line(schema_path)})")
        print("[INFO] exit_codes: 1=unexpected 2=taxonomy 3=schema 4=both")

        failures = []
        taxonomy_failed = False
        schema_failed = False

        # Pre-check existence (more direct error messages)
        if not taxonomy_path.exists():
            taxonomy_failed = True
            failures.append(f"[FAIL][TAXONOMY] missing file: {taxonomy_path}")
        if not schema_path.exists():
            schema_failed = True
            failures.append(f"[FAIL][SCHEMA] missing file: {schema_path}")

        # Taxonomy invariants
        if not taxonomy_failed:
            try:
                validate_fail_code_taxonomy(taxonomy_path, repo_root=repo_root)
                print("[PASS] fail_code_taxonomy_v1 invariants")
            except AssertionError as e:
                taxonomy_failed = True
                failures.append(f"[FAIL][TAXONOMY] {taxonomy_path}: {e}")
            except Exception as e:
                taxonomy_failed = True
                failures.append(f"[FAIL][TAXONOMY] {taxonomy_path}: unexpected error: {e}")

        # Schema guard
        if not schema_failed:
            try:
                validate_verification_report_schema(schema_path)
                print("[PASS] verification_report_v1 schema guard")
            except AssertionError as e:
                schema_failed = True
                failures.append(f"[FAIL][SCHEMA] {schema_path}: {e}")
            except Exception as e:
                schema_failed = True
                failures.append(f"[FAIL][SCHEMA] {schema_path}: unexpected error: {e}")

        if failures:
            print("\n=== CONTRACT VALIDATION FAILED ===")
            for f in failures:
                print(f)

            if taxonomy_failed and schema_failed:
                return 4
            if taxonomy_failed:
                return 2
            return 3

        print("\n=== CONTRACT VALIDATION PASSED (v1 LOCK) ===")
        return 0

    except Exception:
        print("\n=== CONTRACT VALIDATION FAILED (UNEXPECTED_ERROR) ===")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
