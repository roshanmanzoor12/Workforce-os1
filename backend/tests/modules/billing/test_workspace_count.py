from __future__ import annotations

import uuid

import pytest

from app.modules.billing.workspace_count import (
    count_owned_active_workspaces,
)


class FakeResult:
    def __init__(
        self,
        value: int,
    ) -> None:
        self.value = value

    def scalar_one(
        self,
    ) -> int:
        return self.value


class FakeSession:
    def __init__(
        self,
        value: int,
    ) -> None:
        self.value = value
        self.statement = None

    async def execute(
        self,
        statement,
    ) -> FakeResult:
        self.statement = statement

        return FakeResult(
            self.value
        )


@pytest.mark.asyncio
async def test_workspace_count_returns_integer():
    session = FakeSession(
        2
    )

    result = await count_owned_active_workspaces(
        session,
        uuid.uuid4(),
    )

    assert result == 2

    assert session.statement is not None


@pytest.mark.asyncio
async def test_workspace_count_can_be_zero():
    session = FakeSession(
        0
    )

    result = await count_owned_active_workspaces(
        session,
        uuid.uuid4(),
    )

    assert result == 0