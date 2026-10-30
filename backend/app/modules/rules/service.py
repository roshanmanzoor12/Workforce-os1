from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from app.modules.rules.models import AutomationRule
from app.modules.rules.repository import RulesRepository


class RuleNotFoundError(LookupError):
    pass


class RuleValidationError(ValueError):
    pass


class RulesService:
    def __init__(
        self,
        repository: RulesRepository | None = None,
    ) -> None:
        self.repository = (
            repository
            if repository is not None
            else RulesRepository()
        )

    async def list_rules(
        self,
        workspace_id: UUID,
    ) -> list[AutomationRule]:
        return await self.repository.list(workspace_id)

    async def get_rule(
        self,
        workspace_id: UUID,
        rule_id: UUID,
    ) -> AutomationRule:
        item = await self.repository.get(
            workspace_id,
            rule_id,
        )

        if item is None:
            raise RuleNotFoundError(
                f"Rule {rule_id} was not found."
            )

        return item

    async def create_rule(
        self,
        *,
        workspace_id: UUID,
        name: str,
        event_type: str,
        conditions: list[dict[str, Any]],
        actions: list[dict[str, Any]],
    ) -> AutomationRule:
        if not actions:
            raise RuleValidationError(
                "At least one action is required."
            )

        item = AutomationRule(
            id=uuid4(),
            workspace_id=workspace_id,
            name=name,
            event_type=event_type,
            conditions=conditions,
            actions=actions,
        )

        return await self.repository.save(item)

    async def set_enabled(
        self,
        *,
        workspace_id: UUID,
        rule_id: UUID,
        is_enabled: bool,
    ) -> AutomationRule:
        item = await self.get_rule(
            workspace_id,
            rule_id,
        )

        item.is_enabled = is_enabled

        return await self.repository.save(item)