from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RuleStateChanged:
    workspace_id: UUID
    rule_id: UUID
    is_enabled: bool
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: UUID,
        rule_id: UUID,
        is_enabled: bool,
    ) -> "RuleStateChanged":
        return cls(
            workspace_id=workspace_id,
            rule_id=rule_id,
            is_enabled=is_enabled,
            occurred_at=datetime.now(timezone.utc),
        )