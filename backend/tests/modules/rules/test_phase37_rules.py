from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.rules.router import router
from app.modules.rules.schemas import (
    RuleAction,
    RuleCondition,
    RuleCreate,
)
from app.modules.rules.service import RulesService


def test_rules_routes_exist() -> None:
    paths = {
        route.path
        for route in router.routes
    }

    assert "/workspaces/{workspace_id}/rules" in paths
    assert "/workspaces/{workspace_id}/rules/{rule_id}" in paths
    assert (
        "/workspaces/{workspace_id}/rules/{rule_id}/enable"
        in paths
    )
    assert (
        "/workspaces/{workspace_id}/rules/{rule_id}/disable"
        in paths
    )


def test_rule_schema_accepts_valid_payload() -> None:
    payload = RuleCreate(
        name="Block repeat visitors",
        event_type="visitor.detected",
        conditions=[
            RuleCondition(
                field="risk_score",
                operator="greater_than",
                value=80,
            )
        ],
        actions=[
            RuleAction(
                action_type="block",
                parameters={"duration": "24h"},
            )
        ],
    )

    assert payload.name == "Block repeat visitors"
    assert len(payload.actions) == 1


@pytest.mark.asyncio
async def test_rule_can_be_created_and_disabled() -> None:
    service = RulesService()
    workspace_id = uuid4()

    item = await service.create_rule(
        workspace_id=workspace_id,
        name="Fraud rule",
        event_type="visitor.detected",
        conditions=[],
        actions=[
            {
                "action_type": "challenge",
                "parameters": {},
            }
        ],
    )

    assert item.is_enabled is True

    updated = await service.set_enabled(
        workspace_id=workspace_id,
        rule_id=item.id,
        is_enabled=False,
    )

    assert updated.is_enabled is False


@pytest.mark.asyncio
async def test_rules_are_workspace_isolated() -> None:
    service = RulesService()

    workspace_a = uuid4()
    workspace_b = uuid4()

    await service.create_rule(
        workspace_id=workspace_a,
        name="Rule A",
        event_type="event.a",
        conditions=[],
        actions=[{"action_type": "notify"}],
    )

    await service.create_rule(
        workspace_id=workspace_b,
        name="Rule B",
        event_type="event.b",
        conditions=[],
        actions=[{"action_type": "notify"}],
    )

    rules_a = await service.list_rules(workspace_a)
    rules_b = await service.list_rules(workspace_b)

    assert len(rules_a) == 1
    assert len(rules_b) == 1
    assert rules_a[0].workspace_id == workspace_a
    assert rules_b[0].workspace_id == workspace_b