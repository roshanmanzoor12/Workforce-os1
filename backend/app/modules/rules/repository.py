from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.modules.rules.models import AutomationRule


class RulesRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, AutomationRule] = {}

    async def list(
        self,
        workspace_id: UUID,
    ) -> list[AutomationRule]:
        return [
            item
            for item in self._items.values()
            if item.workspace_id == workspace_id
        ]

    async def get(
        self,
        workspace_id: UUID,
        rule_id: UUID,
    ) -> AutomationRule | None:
        item = self._items.get(rule_id)

        if item is None or item.workspace_id != workspace_id:
            return None

        return item

    async def save(
        self,
        item: AutomationRule,
    ) -> AutomationRule:
        item.updated_at = datetime.now(timezone.utc)
        self._items[item.id] = item
        return item