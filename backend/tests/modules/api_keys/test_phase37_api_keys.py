from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.modules.api_keys.models import WorkspaceAPIKey
from app.modules.api_keys.permissions import (
    require_api_key_management,
)
from app.modules.api_keys.repository import APIKeyRepository
from app.modules.api_keys.router import router
from app.modules.api_keys.schemas import APIKeyCreate
from app.modules.api_keys.service import APIKeyService, hash_secret
from app.modules.workspace_permissions.roles import OWNER_ROLE


class FakeRepository:
    def __init__(self, workspace_id):
        self.workspace_id = workspace_id
        self.rows = {}

    async def add(self, row):
        self.rows[row.id] = row

    async def get(self, key_id, *, for_update=False):
        row = self.rows.get(key_id)

        if row is None or row.workspace_id != self.workspace_id:
            return None

        return row

    async def list(self, *, limit=100, offset=0):
        rows = [
            row
            for row in self.rows.values()
            if row.workspace_id == self.workspace_id
        ]
        return rows[offset:offset + limit]


def make_service():
    session = SimpleNamespace(
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )

    scope = SimpleNamespace(
        workspace_id=uuid4(),
        user_id=uuid4(),
        role_key=OWNER_ROLE,
        session=session,
    )

    service = APIKeyService(scope)
    service.repository = FakeRepository(scope.workspace_id)

    return service, scope


def payload():
    return APIKeyCreate(
        name="Reporting integration",
        scopes=["reports.self.read"],
    )


def test_unknown_role_cannot_manage_keys():
    scope = SimpleNamespace(role_key="unknown-role")

    with pytest.raises(HTTPException) as error:
        require_api_key_management(scope)

    assert error.value.status_code == 403


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "   "},
        {"scopes": []},
        {"scopes": [""]},
        {"expires_at": datetime.now()},
        {
            "expires_at": datetime.now(timezone.utc)
            - timedelta(days=1)
        },
        {"workspace_id": str(uuid4())},
    ],
)
def test_invalid_create_payload_is_rejected(changes):
    data = {
        "name": "Reporting",
        "scopes": ["reports.self.read"],
    }
    data.update(changes)

    with pytest.raises(ValidationError):
        APIKeyCreate(**data)


def test_creation_stores_hash_and_list_hides_secrets():
    async def scenario():
        service, scope = make_service()
        issued = await service.create_key(payload())
        raw = issued.secret.get_secret_value()
        row = service.repository.rows[issued.key.id]

        assert raw.startswith(issued.key.key_prefix + ".")
        assert row.secret_hash == hash_secret(raw)
        assert row.secret_hash != raw
        assert raw not in repr(issued)

        listed = await service.list_keys()
        public = listed[0].model_dump()

        assert "secret" not in public
        assert "secret_hash" not in public
        scope.session.commit.assert_awaited_once()

    asyncio.run(scenario())


def test_unsupported_scope_is_rejected_before_writing():
    async def scenario():
        service, scope = make_service()

        with pytest.raises(HTTPException) as error:
            await service.create_key(
                APIKeyCreate(
                    name="Invalid",
                    scopes=["integrations.manage"],
                )
            )

        assert error.value.status_code == 422
        assert service.repository.rows == {}
        scope.session.commit.assert_not_awaited()

    asyncio.run(scenario())


def test_service_denies_unknown_role_before_repository_access():
    async def scenario():
        service, scope = make_service()
        scope.role_key = "unknown-role"

        with pytest.raises(HTTPException) as error:
            await service.create_key(payload())

        assert error.value.status_code == 403
        assert service.repository.rows == {}
        scope.session.commit.assert_not_awaited()

    asyncio.run(scenario())


def test_rotation_revokes_old_key_and_issues_new_secret():
    async def scenario():
        service, scope = make_service()
        old = await service.create_key(payload())
        replacement = await service.rotate_key(old.key.id)

        old_row = service.repository.rows[old.key.id]
        new_row = service.repository.rows[replacement.key.id]

        assert replacement.key.id != old.key.id
        assert old_row.revoked_at is not None
        assert old_row.revoked_by_user_id == scope.user_id
        assert new_row.revoked_at is None
        assert (
            replacement.secret.get_secret_value()
            != old.secret.get_secret_value()
        )

        with pytest.raises(HTTPException) as error:
            await service.rotate_key(old.key.id)

        assert error.value.status_code == 409

    asyncio.run(scenario())


def test_revocation_is_idempotent():
    async def scenario():
        service, _ = make_service()
        issued = await service.create_key(payload())

        first = await service.revoke_key(issued.key.id)
        second = await service.revoke_key(issued.key.id)

        assert first.revoked_at == second.revoked_at
        assert (
            first.revoked_by_user_id
            == second.revoked_by_user_id
        )

    asyncio.run(scenario())


def test_expired_key_cannot_be_rotated():
    async def scenario():
        service, _ = make_service()
        issued = await service.create_key(payload())
        row = service.repository.rows[issued.key.id]
        row.expires_at = (
            datetime.now(timezone.utc) - timedelta(seconds=1)
        )

        with pytest.raises(HTTPException) as error:
            await service.rotate_key(issued.key.id)

        assert error.value.status_code == 409
        assert row.revoked_at is None

    asyncio.run(scenario())


def test_failed_commit_rolls_back():
    async def scenario():
        service, scope = make_service()
        scope.session.commit.side_effect = RuntimeError(
            "Database unavailable"
        )

        with pytest.raises(RuntimeError):
            await service.create_key(payload())

        scope.session.rollback.assert_awaited_once()

    asyncio.run(scenario())


def test_repository_queries_filter_workspace_and_lock_rotation():
    async def scenario():
        workspace_id = uuid4()
        key_id = uuid4()

        result = SimpleNamespace(
            scalar_one_or_none=lambda: None,
            scalars=lambda: SimpleNamespace(all=lambda: []),
        )

        session = SimpleNamespace(
            execute=AsyncMock(return_value=result)
        )
        repository = APIKeyRepository(session, workspace_id)

        await repository.get(key_id, for_update=True)
        await repository.list()

        statements = [
            call.args[0]
            for call in session.execute.await_args_list
        ]

        compiled = [
            statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
            for statement in statements
        ]

        for statement in compiled:
            sql = str(statement)
            assert "workspace_api_keys.workspace_id =" in sql
            assert workspace_id.hex in sql.replace("-", "")

        assert "FOR UPDATE" in str(compiled[0])

    asyncio.run(scenario())


def test_repository_rejects_workspace_mismatch():
    async def scenario():
        session = SimpleNamespace(
            add=lambda row: pytest.fail("Must not add row"),
            flush=AsyncMock(),
        )
        repository = APIKeyRepository(session, uuid4())

        with pytest.raises(ValueError):
            await repository.add(
                WorkspaceAPIKey(workspace_id=uuid4())
            )

        session.flush.assert_not_awaited()

    asyncio.run(scenario())


def test_router_exposes_management_endpoints():
    routes = {
        (route.path, method)
        for route in router.routes
        for method in route.methods
    }

    base = "/workspaces/{workspace_id}/api-keys"

    assert (base, "GET") in routes
    assert (base, "POST") in routes
    assert (base + "/{key_id}", "GET") in routes
    assert (base + "/{key_id}/revoke", "POST") in routes
    assert (base + "/{key_id}/rotate", "POST") in routes