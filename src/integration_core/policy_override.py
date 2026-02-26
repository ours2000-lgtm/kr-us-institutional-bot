from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional


Mode = Literal["default", "strict", "warn", "block"]
OverrideMode = Literal["none", "replace_set", "patch_specs", "force_mode"]


@dataclass(frozen=True)
class PolicyOverride:
    """
    v0.5.3 Override SSOT (MVP).

    Design principles:
    - Overrides MUST be recorded in rich_context only (hash-excluded).
    - When mode == "none", behavior MUST be identical to "no override".
    - force_policy_mode affects policy core inputs (mode is hashed), so hashes SHOULD change.
    """

    mode: OverrideMode = "none"

    # 1) replace_set
    policy_set_key: Optional[str] = None  # e.g. "default", "strict_guard", "experimental"

    # 2) patch_specs
    disable_refs: Optional[list[str]] = None
    priority_overrides: Optional[Dict[str, int]] = None  # ref -> priority

    # 3) force_mode
    force_policy_mode: Optional[Mode] = None  # "default"/"strict"/"warn"/"block"

    # audit (hash-excluded)
    override_reason: Optional[str] = None
    override_principal: Optional[Dict[str, str]] = None  # {"type": "...", "id": "..."} like evidence principal

    def to_rich_dict(self) -> dict:
        """Serialize for rich_context (hash-excluded)."""
        return {
            "mode": self.mode,
            "policy_set_key": self.policy_set_key,
            "disable_refs": list(self.disable_refs or []),
            "priority_overrides": dict(self.priority_overrides or {}),
            "force_policy_mode": self.force_policy_mode,
            "override_reason": self.override_reason,
            "override_principal": dict(self.override_principal or {}),
        }