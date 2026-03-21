import json
import re
from pathlib import Path
from typing import Optional, Tuple


_ALERT_ID_RE = re.compile(r"^ALERT_[A-Z0-9_]+_V[0-9]+$")
_RUNBOOK_REF_RE = re.compile(r"^RUNBOOK#[A-Z0-9_]+$")
_LOCK_ID_RE = re.compile(r"^[A-Z0-9_]+_LOCK$")
_ISO_Z_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")

_RUNBOOK_HINT_PREFIX = "RUNBOOK_ROOT/"


def _load_json(path: Path):
    if not path.exists():
        raise AssertionError(f"Missing taxonomy file: {path}")
    try:
        # Windows BOM 대비
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        raise AssertionError(f"Invalid JSON: {path} ({e})")


def _split_ref(ref: str) -> Tuple[str, Optional[str]]:
    """
    Split "path#anchor" into ("path", "anchor").
    If no "#", returns ("path", None).
    """
    if "#" in ref:
        p, a = ref.split("#", 1)
        return p, a
    return ref, None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except Exception as e:
        raise AssertionError(f"Cannot read text file: {path} ({e})")


def validate_fail_code_taxonomy(path: Path, repo_root: Optional[Path] = None):
    data = _load_json(path)

    # --- minimal top-level guards (LOCK-ish) ---
    if data.get("schema_version") != "fail-code-taxonomy/1.0":
        raise AssertionError("schema_version must be 'fail-code-taxonomy/1.0'")

    if not _ISO_Z_RE.match(data.get("declared_at_utc", "")):
        raise AssertionError("declared_at_utc must be ISO8601 UTC with Z suffix")

    lock = data.get("lock", {})
    lock_id = lock.get("lock_id", "")
    if not _LOCK_ID_RE.match(lock_id):
        raise AssertionError("lock.lock_id must match ^[A-Z0-9_]+_LOCK$")

    codes = data.get("codes")
    if not isinstance(codes, list) or not codes:
        raise AssertionError("codes[] must exist and be non-empty")

    domains = data.get("domains", {})
    for k in ["severity", "retry_policy", "category", "impact_scope"]:
        if k not in domains or not isinstance(domains[k], list) or not domains[k]:
            raise AssertionError(f"domains.{k} must exist and be non-empty list")

    allowed_severity = set(domains["severity"])
    allowed_retry = set(domains["retry_policy"])
    allowed_category = set(domains["category"])
    allowed_scope = set(domains["impact_scope"])

    reserved = set(data.get("reserved_categories", {}).get("v1_0_reserved", []))

    constraints_map = data.get("severity_retry_policy_constraints", {})
    if not isinstance(constraints_map, dict) or not constraints_map:
        raise AssertionError("severity_retry_policy_constraints must exist")

    seen_fail_codes = set()
    seen_alert_ids = set()
    seen_runbooks = set()

    for idx, code in enumerate(codes):
        # --- required keys ---
        for k in ["fail_code", "status", "category", "severity", "retry_policy", "impact_scope",
                  "required_fail_fields", "alert_id", "runbook_ref", "links"]:
            if k not in code:
                raise AssertionError(f"codes[{idx}].{k} missing")

        fc = code["fail_code"]

        # --- uniqueness ---
        if fc in seen_fail_codes:
            raise AssertionError(f"Duplicate fail_code: {fc}")
        seen_fail_codes.add(fc)

        # --- status ---
        status = code["status"]
        if status not in ["ACTIVE", "DEPRECATED", "RETIRED"]:
            raise AssertionError(f"{fc}: invalid status {status}")

        # --- category / reserved ---
        category = code["category"]
        if category not in allowed_category:
            raise AssertionError(f"{fc}: category '{category}' not in domains.category")
        if category in reserved:
            raise AssertionError(f"{fc}: reserved category '{category}' MUST NOT be used in v1.0")

        # --- severity / retry / scope domain checks ---
        severity = code["severity"]
        if severity not in allowed_severity:
            raise AssertionError(f"{fc}: severity '{severity}' not in domains.severity")

        retry = code["retry_policy"]
        if retry not in allowed_retry:
            raise AssertionError(f"{fc}: retry_policy '{retry}' not in domains.retry_policy")

        scope = code["impact_scope"]
        if scope not in allowed_scope:
            raise AssertionError(f"{fc}: impact_scope '{scope}' not in domains.impact_scope")

        # --- severity->retry constraints ---
        allowed_for_sev = constraints_map.get(severity)
        if not isinstance(allowed_for_sev, list) or not allowed_for_sev:
            raise AssertionError(f"{fc}: constraints missing for severity '{severity}'")
        if retry not in allowed_for_sev:
            raise AssertionError(f"{fc}: retry_policy '{retry}' not allowed for severity '{severity}'")

        # --- required_fail_fields ---
        rff = code["required_fail_fields"]
        if not isinstance(rff, list):
            raise AssertionError(f"{fc}: required_fail_fields must be list")
        for f_i, f in enumerate(rff):
            if not isinstance(f, str) or len(f.strip()) < 1:
                raise AssertionError(f"{fc}: required_fail_fields[{f_i}] invalid '{f}'")

        # --- alert_id regex + uniqueness ---
        alert_id = code["alert_id"]
        if not isinstance(alert_id, str) or not _ALERT_ID_RE.match(alert_id):
            raise AssertionError(f"{fc}: alert_id invalid format '{alert_id}'")
        if alert_id in seen_alert_ids:
            raise AssertionError(f"Duplicate alert_id: {alert_id}")
        seen_alert_ids.add(alert_id)

        # --- runbook_ref regex + uniqueness ---
        runbook = code["runbook_ref"]
        if not isinstance(runbook, str) or not _RUNBOOK_REF_RE.match(runbook):
            raise AssertionError(f"{fc}: runbook_ref invalid format '{runbook}'")
        if runbook in seen_runbooks:
            raise AssertionError(f"Duplicate runbook_ref: {runbook}")
        seen_runbooks.add(runbook)

        # --- links checks ---
        links = code["links"]
        if not isinstance(links, dict):
            raise AssertionError(f"{fc}: links must be object")

        auth_ref = links.get("authoritative_ref")
        if not isinstance(auth_ref, str) or len(auth_ref.strip()) < 1:
            raise AssertionError(f"{fc}: links.authoritative_ref missing/invalid")

        # IMPORTANT: split "path#anchor"
        auth_path_str, auth_anchor = _split_ref(auth_ref)
        if not auth_anchor:
            raise AssertionError(f"{fc}: links.authoritative_ref must include '#{fc}' anchor")
        if auth_anchor != fc:
            raise AssertionError(f"{fc}: authoritative_ref anchor must equal fail_code (got '{auth_anchor}')")

        if repo_root:
            auth_path = repo_root / auth_path_str
            if not auth_path.exists():
                raise AssertionError(f"{fc}: links.authoritative_ref file not found: {auth_path_str}")

            text = _read_text(auth_path)
            # anchor contract: "## <FAIL_CODE>" must exist
            needle = f"## {fc}"
            if needle not in text:
                raise AssertionError(f"{fc}: anchor not found in {auth_path_str} (missing '{needle}')")

        runbook_hint = links.get("runbook_path_hint")
        if not isinstance(runbook_hint, str) or not runbook_hint.startswith(_RUNBOOK_HINT_PREFIX):
            raise AssertionError(f"{fc}: runbook_path_hint must be RUNBOOK_ROOT-relative")

        # optional: enforce snake_case.md
        filename = runbook_hint.replace(_RUNBOOK_HINT_PREFIX, "")
        if not re.match(r"^[a-z0-9_]+\.md$", filename):
            raise AssertionError(f"{fc}: runbook_path_hint filename must be snake_case.md (got '{filename}')")

    # --- categories_index cross-check (bidirectional) ---
    index = data.get("categories_index", {})
    if not isinstance(index, dict):
        raise AssertionError("categories_index must be object")

    indexed = set()
    for cat, lst in index.items():
        if cat not in allowed_category:
            raise AssertionError(f"categories_index key '{cat}' not in domains.category")
        if not isinstance(lst, list):
            raise AssertionError(f"categories_index['{cat}'] must be list")
        for item in lst:
            if not isinstance(item, str) or not item:
                raise AssertionError(f"categories_index['{cat}'] contains invalid fail_code '{item}'")
            indexed.add(item)

    if indexed != seen_fail_codes:
        missing_in_index = sorted(seen_fail_codes - indexed)
        extra_in_index = sorted(indexed - seen_fail_codes)
        raise AssertionError(
            "categories_index does not match codes[] (bidirectional mismatch). "
            f"missing_in_index={missing_in_index} extra_in_index={extra_in_index}"
        )
