from __future__ import annotations

from enum import Enum


class LifecycleState(str, Enum):
    Draft = "Draft"
    Reviewed = "Reviewed"
    Approved = "Approved"
    Active = "Active"
    Deprecated = "Deprecated"
    Archived = "Archived"