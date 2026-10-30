from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.privacy.router import router
from app.modules.privacy.schemas import (
    PrivacyExclusionCreate,
    PrivacyPolicyCreate,
    PrivacyZoneCreate,
)
from app.modules.privacy.service import PrivacyService


def test_privacy_routes_exist() -> None:
    paths = {
        route.path
        for route in router.routes
    }

    assert (
        "/workspaces/{workspace_id}/privacy/policies"
        in paths
    )
    assert (
        "/workspaces/{workspace_id}/privacy/zones"
        in paths
    )
    assert (
        "/workspaces/{workspace_id}/privacy/exclusions"
        in paths
    )


def test_policy_schema() -> None:
    payload = PrivacyPolicyCreate(
        name="Default Privacy Policy",
        description="Standard workspace policy",
    )

    assert payload.name == "Default Privacy Policy"


def test_zone_schema() -> None:
    payload = PrivacyZoneCreate(
        name="Office Hours",
        zone_type="schedule",
        value="09:00-18:00",
    )

    assert payload.zone_type == "schedule"


def test_exclusion_schema() -> None:
    payload = PrivacyExclusionCreate(
        exclusion_type="ip",
        value="192.168.1.10",
        reason="Internal office traffic",
    )

    assert payload.exclusion_type == "ip"


@pytest.mark.asyncio
async def test_privacy_workspace_isolation() -> None:
    service = PrivacyService()

    workspace_a = uuid4()
    workspace_b = uuid4()

    await service.create_policy(
        workspace_id=workspace_a,
        name="Workspace A Policy",
        description=None,
    )

    await service.create_policy(
        workspace_id=workspace_b,
        name="Workspace B Policy",
        description=None,
    )

    a_items = await service.list_policies(workspace_a)
    b_items = await service.list_policies(workspace_b)

    assert len(a_items) == 1
    assert len(b_items) == 1
    assert a_items[0].workspace_id == workspace_a
    assert b_items[0].workspace_id == workspace_b