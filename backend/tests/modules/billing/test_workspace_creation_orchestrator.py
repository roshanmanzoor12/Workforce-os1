from __future__ import annotations

import uuid

import pytest

from app.modules.billing.workspace_creation_orchestrator import (
    WorkspaceCreationOrchestrator,
)


class FakeUser:
    def __init__(
        self,
    ) -> None:
        self.id = uuid.uuid4()


class FakeEntitlementAccess:
    def __init__(
        self,
        *,
        allowed: bool = True,
    ) -> None:
        self.allowed = allowed
        self.called = False

    async def require_workspace_creation(
        self,
        *,
        user_id,
    ):
        self.called = True

        if not self.allowed:
            raise RuntimeError(
                "denied"
            )

        return object()


class FakeWorkspaceCreator:
    def __init__(
        self,
    ) -> None:
        self.called = False

    async def create_workspace(
        self,
        request,
        *,
        user,
    ):
        self.called = True

        return "created"


@pytest.mark.asyncio
async def test_entitlement_checked_before_create():
    access = FakeEntitlementAccess()

    creator = FakeWorkspaceCreator()

    orchestrator = WorkspaceCreationOrchestrator(
        None,
        entitlement_access=access,
    )

    result = await orchestrator.create(
        object(),
        user=FakeUser(),
        workspace_creator=creator,
    )

    assert access.called is True
    assert creator.called is True
    assert result == "created"


@pytest.mark.asyncio
async def test_denied_entitlement_blocks_creation():
    access = FakeEntitlementAccess(
        allowed=False
    )

    creator = FakeWorkspaceCreator()

    orchestrator = WorkspaceCreationOrchestrator(
        None,
        entitlement_access=access,
    )

    with pytest.raises(
        RuntimeError,
        match="denied",
    ):
        await orchestrator.create(
            object(),
            user=FakeUser(),
            workspace_creator=creator,
        )

    assert access.called is True
    assert creator.called is False