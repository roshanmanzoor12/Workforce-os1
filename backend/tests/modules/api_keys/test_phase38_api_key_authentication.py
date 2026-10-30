import hashlib
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.api_keys import authentication as module
from app.modules.api_keys.authentication import (
    APIKeyAuthentication,
    APIKeyPrincipal,
    parse_api_key,
)


SECRET = "wfos_" + "a" * 32 + "." + "b" * 43


def setup_authentication(monkeypatch):
    workspace_id = uuid4()
    user_id = uuid4()

    tenant = SimpleNamespace(
        execute=AsyncMock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )

    control = SimpleNamespace(execute=AsyncMock())

    authentication = APIKeyAuthentication(
        tenant_session=tenant,
        control_session=control,
        workspace_id=workspace_id,
        database_name="tenant_" + workspace_id.hex,
        cluster_key="primary",
    )

    key = SimpleNamespace(
        id=uuid4(),
        workspace_id=workspace_id,
        created_by_user_id=user_id,
        secret_hash=hashlib.sha256(SECRET.encode()).hexdigest(),
        scopes=["employees.read"],
        expires_at=None,
        revoked_at=None,
        last_used_at=None,
    )

    context = SimpleNamespace(
        workspace_id=workspace_id,
        user_id=user_id,
        membership_id=uuid4(),
        role_key="owner",
        database_name="tenant_" + workspace_id.hex,
        cluster_key="primary",
        schema_version=None,
    )

    authentication._load_key = AsyncMock(return_value=key)
    authentication._creator_context = AsyncMock(
        return_value=context
    )

    class Permissions:
        def __init__(self, scope):
            pass

        def has(self, permission):
            return permission == "employees.read"

    monkeypatch.setattr(
        module,
        "WorkspacePermissionService",
        Permissions,
    )

    return authentication, tenant, control, key, context


@pytest.mark.parametrize(
    "secret",
    [None, "", "invalid", SECRET + " ", SECRET[:-1]],
)
def test_malformed_credentials_are_rejected(secret):
    with pytest.raises(HTTPException) as error:
        parse_api_key(secret)

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_valid_key_records_usage(monkeypatch):
    authentication, tenant, control, key, context = (
        setup_authentication(monkeypatch)
    )

    principal = await authentication.authenticate(
        SECRET,
        required_scopes=frozenset({"employees.read"}),
    )

    assert principal.key_id == key.id
    assert principal.user_id == context.user_id
    assert principal.scopes == frozenset({"employees.read"})
    assert key.last_used_at is not None

    tenant.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    ["missing", "secret", "workspace", "revoked", "expired"],
)
async def test_invalid_key_does_not_record_usage(
    monkeypatch,
    failure,
):
    authentication, tenant, control, key, context = (
        setup_authentication(monkeypatch)
    )

    if failure == "missing":
        authentication._load_key.return_value = None
    elif failure == "secret":
        key.secret_hash = "0" * 64
    elif failure == "workspace":
        key.workspace_id = uuid4()
    elif failure == "revoked":
        key.revoked_at = datetime.now(timezone.utc)
    elif failure == "expired":
        key.expires_at = (
            datetime.now(timezone.utc) - timedelta(seconds=1)
        )

    with pytest.raises(HTTPException) as error:
        await authentication.authenticate(SECRET)

    assert error.value.status_code == 401
    assert key.last_used_at is None

    authentication._creator_context.assert_not_awaited()
    tenant.commit.assert_not_awaited()
    tenant.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_required_scope_is_forbidden(monkeypatch):
    authentication, tenant, control, key, context = (
        setup_authentication(monkeypatch)
    )

    with pytest.raises(HTTPException) as error:
        await authentication.authenticate(
            SECRET,
            required_scopes=frozenset({"reports.self.read"}),
        )

    assert error.value.status_code == 403
    assert key.last_used_at is None
    tenant.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_removed_creator_permission_is_forbidden(monkeypatch):
    authentication, tenant, control, key, context = (
        setup_authentication(monkeypatch)
    )

    class NoPermissions:
        def __init__(self, scope):
            pass

        def has(self, permission):
            return False

    monkeypatch.setattr(
        module,
        "WorkspacePermissionService",
        NoPermissions,
    )

    with pytest.raises(HTTPException) as error:
        await authentication.authenticate(SECRET)

    assert error.value.status_code == 403
    tenant.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_creator_rejection_prevents_usage(monkeypatch):
    authentication, tenant, control, key, context = (
        setup_authentication(monkeypatch)
    )

    authentication._creator_context.side_effect = (
        module.authentication_error()
    )

    with pytest.raises(HTTPException) as error:
        await authentication.authenticate(SECRET)

    assert error.value.status_code == 401
    assert key.last_used_at is None
    tenant.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_usage_commit_failure_is_propagated(monkeypatch):
    authentication, tenant, control, key, context = (
        setup_authentication(monkeypatch)
    )

    tenant.commit.side_effect = RuntimeError("Commit failed")

    with pytest.raises(RuntimeError, match="Commit failed"):
        await authentication.authenticate(SECRET)

    tenant.rollback.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "state",
    ["missing", "inactive", "locked", "unverified"],
)
async def test_creator_account_state_is_checked(monkeypatch, state):
    authentication, tenant, control, key, context = (
        setup_authentication(monkeypatch)
    )

    # Exercise the actual creator lookup method.
    del authentication._creator_context

    user = SimpleNamespace(
        is_active=state != "inactive",
        is_locked=state == "locked",
        is_email_verified=state != "unverified",
    )

    result = SimpleNamespace(
        scalar_one_or_none=lambda: (
            None if state == "missing" else user
        )
    )

    control.execute.return_value = result

    resolver = AsyncMock()
    monkeypatch.setattr(
        module,
        "resolve_authorized_tenant_context",
        resolver,
    )

    with pytest.raises(HTTPException) as error:
        await authentication._creator_context(context.user_id)

    assert error.value.status_code == 401
    resolver.assert_not_awaited()


def test_principal_cannot_use_an_ungranted_scope():
    principal = APIKeyPrincipal(
        key_id=uuid4(),
        workspace_id=uuid4(),
        user_id=uuid4(),
        membership_id=uuid4(),
        scopes=frozenset({"employees.read"}),
    )

    principal.require("employees.read")

    with pytest.raises(HTTPException) as error:
        principal.require("integrations.manage")

    assert error.value.status_code == 403