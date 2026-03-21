#!/usr/bin/env python3
"""
validate_contracts_v1.py

Single CI entrypoint for validating v1 canonical contracts.

FAIL behavior:
- Any invariant violation -> exit non-zero
- Soft-fail is forbidden

Exit codes:
- 2: taxonomy invariant failure (or combined)
- 3: schema invariant failure (or combined)
- 4: both taxonomy + schema failed
- 1: unexpected error
"""

from __future__ import annotations

import sys
from pathlib import Path

from invariants_fail_code_taxonomy_v1 import validate_fail_code_taxonomy
from invariants_verification_report_v1 import validate_verification_report_schema


def _find_repo_root(start: Path) -> Path:
    """
    Find repo root by walking up until we find 'logs/evidence/_specs'.
    This matches your repo topology and avoids hardcoding parents[2].

    If the repo becomes deeply nested, this still works (no fixed depth).
    """
    cur = start.resolve()
    visited = []

    while True:
        visited.append(str(cur))

        marker = cur / "logs" / "evidence" / "_specs"
        if marker.exists() and marker.is_dir():
            return cur

        if cur.parent == cur:
            raise AssertionError(
                "Repo root not found. Expected to find 'logs/evidence/_specs' while walking up.\n"
                f"Visited:\n- " + "\n- ".join(visited[-25:])
            )
        cur = cur.parent


def main() -> int:
    try:
        repo_root = _find_repo_root(Path(__file__))
    except Exception as e:
        print(f"[FAIL][REPO_ROOT] {e}")
        return 1

    # --- Path LOCK (based on your actual folder layout) ---
    taxonomy_path = repo_root / "logs" / "evidence" / "_specs" / "taxonomy" / "fail_code_taxonomy_v1.json"
    schema_path = repo_root / "logs" / "evidence" / "_specs" / "verification_report_v1.schema.json"

    failures_taxonomy = []
    failures_schema = []

    print(f"[INFO] repo_root = {repo_root}")
    print(f"[INFO] taxonomy_path = {taxonomy_path}")
    print(f"[INFO] schema_path   = {schema_path}")

    # --- Taxonomy invariants ---
    try:
        validate_fail_code_taxonomy(taxonomy_path, repo_root=repo_root)
        print("[PASS] fail_code_taxonomy_v1 invariants")
    except AssertionError as e:
        failures_taxonomy.append(f"[FAIL][TAXONOMY] {taxonomy_path}: {e}")
    except Exception as e:
        failures_taxonomy.append(f"[FAIL][TAXONOMY] {taxonomy_path}: unexpected error: {e}")

    # --- Verification report schema guard ---
    try:
        validate_verification_report_schema(schema_path)
        print("[PASS] verification_report_v1 schema LOCK guard")
    except AssertionError as e:
        failures_schema.append(f"[FAIL][SCHEMA] {schema_path}: {e}")
    except Exception as e:
        failures_schema.append(f"[FAIL][SCHEMA] {schema_path}: unexpected error: {e}")

    if failures_taxonomy or failures_schema:
        print("\n=== CONTRACT VALIDATION FAILED ===")
        for msg in failures_taxonomy + failures_schema:
            print(msg)

        if failures_taxonomy and failures_schema:
            return 4
        if failures_taxonomy:
            return 2
        return 3

    print("\n=== CONTRACT VALIDATION PASSED (v1 LOCK) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
