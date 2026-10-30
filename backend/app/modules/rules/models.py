from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class AutomationRule:
    id: UUID
    workspace_id: UUID
    name: str
    event_type: str
    conditions: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    is_enabled: bool = True
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)