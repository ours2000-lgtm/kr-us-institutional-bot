from __future__ import annotations

import json
from pathlib import Path


def validate_verification_report_schema(schema_path: Path) -> None:
    if not schema_path.exists():
        raise AssertionError(f"verification_report_v1.schema.json missing: {schema_path}")

    try:
        text = schema_path.read_text(encoding="utf-8-sig")
    except Exception as e:
        raise AssertionError(f"Failed to read schema file: {schema_path} ({e})")

    try:
        obj = json.loads(text)
    except Exception as e:
        raise AssertionError(f"Invalid JSON schema (parse failed): {e}")

    if not isinstance(obj, dict):
        raise AssertionError("Schema root must be a JSON object")

    # Your schema uses "$id" = "verification-report/1.0" and schema_version const is also that.
    # We accept either "$id" or properties.schema_version.const as LOCK marker.
    schema_id = obj.get("$id")
    if schema_id != "verification-report/1.0":
        # fallback check (in case someone edits $id but keeps const)
        try:
            schema_version_const = (
                obj["properties"]["schema_version"]["const"]
            )
        except Exception:
            schema_version_const = None

        if schema_version_const != "verification-report/1.0":
            raise AssertionError(
                "LOCK marker not found: expected $id == 'verification-report/1.0' "
                "or properties.schema_version.const == 'verification-report/1.0'"
            )

    # Optional: verify schema syntax itself if jsonschema is available
    try:
        import jsonschema  # type: ignore

        # Draft 2020-12 is ok to check via the library's checker
        jsonschema.Draft202012Validator.check_schema(obj)
    except ImportError:
        # CI env may not have jsonschema; shape-only guard is still valuable.
        pass
    except Exception as e:
        raise AssertionError(f"Schema syntax invalid (jsonschema check failed): {e}")
