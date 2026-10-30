from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import ResourceNotFound
from app.db.tenant_context import (
    AuthorizedTenantContext,
    TenantIdentityMismatchError,
    TenantUnavailableError,
    authorized_tenant_session,
    resolve_authorized_tenant_context,
    verify_tenant_identity,
)
from app.modules.workspaces.models import TENANT_STATUS_READY


# =========================================================
# TEST CONSTANTS
# =========================================================

WORKSPACE_A_ID = uuid.UUID(
    "11111111-1111-4111-8111-111111111111"
)

WORKSPACE_B_ID = uuid.UUID(
    "22222222-2222-4222-8222-222222222222"
)

USER_A_ID = uuid.UUID(
    "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
)

USER_B_ID = uuid.UUID(
    "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
)

MEMBERSHIP_A_ID = uuid.UUID(
    "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
)

MEMBERSHIP_B_ID = uuid.UUID(
    "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
)

TENANT_A_DATABASE = (
    "tenant_11111111111141118111111111111111"
)

TENANT_B_DATABASE = (
    "tenant_22222222222242228222222222222222"
)

SCHEMA_VERSION = "2f8aa89ee8cc"


# =========================================================
# HELPERS
# =========================================================


def make_workspace(
    *,
    workspace_id: uuid.UUID = WORKSPACE_A_ID,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=workspace_id,
    )


def make_membership(
    *,
    membership_id: uuid.UUID = MEMBERSHIP_A_ID,
    role_key: str = "owner",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=membership_id,
        role_key=role_key,
    )


def make_registry(
    *,
    database_name: str = TENANT_A_DATABASE,
    cluster_key: str = "primary",
    status: str = TENANT_STATUS_READY,
    schema_version: str | None = SCHEMA_VERSION,
) -> SimpleNamespace:
    return SimpleNamespace(
        database_name=database_name,
        cluster_key=cluster_key,
        status=status,
        schema_version=schema_version,
    )


def make_context(
    *,
    workspace_id: uuid.UUID = WORKSPACE_A_ID,
    user_id: uuid.UUID = USER_A_ID,
    membership_id: uuid.UUID = MEMBERSHIP_A_ID,
    role_key: str = "owner",
    database_name: str = TENANT_A_DATABASE,
    cluster_key: str = "primary",
    schema_version: str | None = SCHEMA_VERSION,
) -> AuthorizedTenantContext:
    return AuthorizedTenantContext(
        workspace_id=workspace_id,
        user_id=user_id,
        membership_id=membership_id,
        role_key=role_key,
        database_name=database_name,
        cluster_key=cluster_key,
        schema_version=schema_version,
    )


class FakeScalarResult:
    def __init__(
        self,
        rows: list[object],
    ) -> None:
        self._rows = rows

    def all(
        self,
    ) -> list[object]:
        return self._rows


class FakeExecuteResult:
    def __init__(
        self,
        rows: list[object],
    ) -> None:
        self._rows = rows

    def scalars(
        self,
    ) -> FakeScalarResult:
        return FakeScalarResult(
            self._rows
        )


def make_tenant_metadata(
    *,
    workspace_id: uuid.UUID = WORKSPACE_A_ID,
    schema_version: str = SCHEMA_VERSION,
    is_active: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        workspace_id=workspace_id,
        schema_version=schema_version,
        is_active=is_active,
    )


# =========================================================
# AUTHORIZED CONTROL-PLANE RESOLUTION
# =========================================================


@pytest.mark.asyncio
async def test_resolve_authorized_tenant_context_returns_trusted_registry_data(
) -> None:
    workspace = make_workspace()
    membership = make_membership()
    registry = make_registry()

    repository = AsyncMock()

    repository.get_authorized_workspace.return_value = (
        workspace,
        membership,
        registry,
    )

    control_session = AsyncMock()

    with patch(
        "app.db.tenant_context.WorkspaceRepository",
        return_value=repository,
    ):
        context = await resolve_authorized_tenant_context(
            control_session,
            workspace_id=WORKSPACE_A_ID,
            user_id=USER_A_ID,
        )

    assert context.workspace_id == WORKSPACE_A_ID
    assert context.user_id == USER_A_ID
    assert context.membership_id == MEMBERSHIP_A_ID
    assert context.role_key == "owner"
    assert context.database_name == TENANT_A_DATABASE
    assert context.cluster_key == "primary"
    assert context.schema_version == SCHEMA_VERSION

    repository.get_authorized_workspace.assert_awaited_once_with(
        workspace_id=WORKSPACE_A_ID,
        user_id=USER_A_ID,
    )


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_resolve_workspace_tenant(
) -> None:
    repository = AsyncMock()

    repository.get_authorized_workspace.return_value = None

    control_session = AsyncMock()

    with patch(
        "app.db.tenant_context.WorkspaceRepository",
        return_value=repository,
    ):
        with pytest.raises(
            ResourceNotFound
        ):
            await resolve_authorized_tenant_context(
                control_session,
                workspace_id=WORKSPACE_A_ID,
                user_id=USER_B_ID,
            )

    repository.get_authorized_workspace.assert_awaited_once_with(
        workspace_id=WORKSPACE_A_ID,
        user_id=USER_B_ID,
    )


@pytest.mark.asyncio
async def test_missing_tenant_registry_is_not_routable(
) -> None:
    repository = AsyncMock()

    repository.get_authorized_workspace.return_value = (
        make_workspace(),
        make_membership(),
        None,
    )

    control_session = AsyncMock()

    with patch(
        "app.db.tenant_context.WorkspaceRepository",
        return_value=repository,
    ):
        with pytest.raises(
            TenantUnavailableError,
            match="not provisioned",
        ):
            await resolve_authorized_tenant_context(
                control_session,
                workspace_id=WORKSPACE_A_ID,
                user_id=USER_A_ID,
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        "pending",
        "provisioning",
        "failed",
        "suspended",
        "decommissioned",
    ],
)
async def test_non_ready_tenant_registry_is_not_routable(
    status: str,
) -> None:
    repository = AsyncMock()

    repository.get_authorized_workspace.return_value = (
        make_workspace(),
        make_membership(),
        make_registry(
            status=status,
        ),
    )

    control_session = AsyncMock()

    with patch(
        "app.db.tenant_context.WorkspaceRepository",
        return_value=repository,
    ):
        with pytest.raises(
            TenantUnavailableError,
            match="not ready",
        ):
            await resolve_authorized_tenant_context(
                control_session,
                workspace_id=WORKSPACE_A_ID,
                user_id=USER_A_ID,
            )


@pytest.mark.asyncio
async def test_invalid_database_name_from_registry_is_rejected(
) -> None:
    repository = AsyncMock()

    repository.get_authorized_workspace.return_value = (
        make_workspace(),
        make_membership(),
        make_registry(
            database_name="postgres",
        ),
    )

    control_session = AsyncMock()

    with patch(
        "app.db.tenant_context.WorkspaceRepository",
        return_value=repository,
    ):
        with pytest.raises(
            Exception
        ):
            await resolve_authorized_tenant_context(
                control_session,
                workspace_id=WORKSPACE_A_ID,
                user_id=USER_A_ID,
            )


@pytest.mark.asyncio
async def test_invalid_cluster_key_from_registry_is_rejected(
) -> None:
    repository = AsyncMock()

    repository.get_authorized_workspace.return_value = (
        make_workspace(),
        make_membership(),
        make_registry(
            cluster_key="client-selected-cluster",
        ),
    )

    control_session = AsyncMock()

    with patch(
        "app.db.tenant_context.WorkspaceRepository",
        return_value=repository,
    ):
        with pytest.raises(
            Exception
        ):
            await resolve_authorized_tenant_context(
                control_session,
                workspace_id=WORKSPACE_A_ID,
                user_id=USER_A_ID,
            )


# =========================================================
# PHYSICAL TENANT IDENTITY
# =========================================================


@pytest.mark.asyncio
async def test_verify_tenant_identity_accepts_matching_workspace(
) -> None:
    context = make_context()

    tenant_db = AsyncMock()

    tenant_db.execute.return_value = FakeExecuteResult(
        [
            make_tenant_metadata()
        ]
    )

    metadata = await verify_tenant_identity(
        tenant_db,
        context=context,
    )

    assert metadata.workspace_id == WORKSPACE_A_ID
    assert metadata.schema_version == SCHEMA_VERSION
    assert metadata.is_active is True


@pytest.mark.asyncio
async def test_verify_tenant_identity_rejects_empty_metadata(
) -> None:
    context = make_context()

    tenant_db = AsyncMock()

    tenant_db.execute.return_value = FakeExecuteResult(
        []
    )

    with pytest.raises(
        TenantIdentityMismatchError,
        match="identity metadata is invalid",
    ):
        await verify_tenant_identity(
            tenant_db,
            context=context,
        )


@pytest.mark.asyncio
async def test_verify_tenant_identity_rejects_multiple_metadata_rows(
) -> None:
    context = make_context()

    tenant_db = AsyncMock()

    tenant_db.execute.return_value = FakeExecuteResult(
        [
            make_tenant_metadata(),
            make_tenant_metadata(),
        ]
    )

    with pytest.raises(
        TenantIdentityMismatchError,
        match="identity metadata is invalid",
    ):
        await verify_tenant_identity(
            tenant_db,
            context=context,
        )


@pytest.mark.asyncio
async def test_verify_tenant_identity_rejects_different_workspace(
) -> None:
    context = make_context()

    tenant_db = AsyncMock()

    tenant_db.execute.return_value = FakeExecuteResult(
        [
            make_tenant_metadata(
                workspace_id=WORKSPACE_B_ID,
            )
        ]
    )

    with pytest.raises(
        TenantIdentityMismatchError,
        match="workspace identity mismatch",
    ):
        await verify_tenant_identity(
            tenant_db,
            context=context,
        )


@pytest.mark.asyncio
async def test_verify_tenant_identity_rejects_inactive_tenant(
) -> None:
    context = make_context()

    tenant_db = AsyncMock()

    tenant_db.execute.return_value = FakeExecuteResult(
        [
            make_tenant_metadata(
                is_active=False,
            )
        ]
    )

    with pytest.raises(
        TenantUnavailableError,
        match="inactive",
    ):
        await verify_tenant_identity(
            tenant_db,
            context=context,
        )


@pytest.mark.asyncio
async def test_verify_tenant_identity_rejects_schema_version_mismatch(
) -> None:
    context = make_context()

    tenant_db = AsyncMock()

    tenant_db.execute.return_value = FakeExecuteResult(
        [
            make_tenant_metadata(
                schema_version="wrong-version",
            )
        ]
    )

    with pytest.raises(
        TenantIdentityMismatchError,
        match="schema version",
    ):
        await verify_tenant_identity(
            tenant_db,
            context=context,
        )


@pytest.mark.asyncio
async def test_verify_tenant_identity_allows_untracked_control_schema_version(
) -> None:
    context = make_context(
        schema_version=None,
    )

    tenant_db = AsyncMock()

    tenant_db.execute.return_value = FakeExecuteResult(
        [
            make_tenant_metadata(
                schema_version=SCHEMA_VERSION,
            )
        ]
    )

    metadata = await verify_tenant_identity(
        tenant_db,
        context=context,
    )

    assert metadata.workspace_id == WORKSPACE_A_ID


# =========================================================
# AUTHORIZED SESSION ROUTING
# =========================================================


@pytest.mark.asyncio
async def test_authorized_tenant_session_routes_only_to_resolved_database(
) -> None:
    context = make_context()

    tenant_db = AsyncMock()

    captured: dict[
        str,
        str,
    ] = {}

    @asynccontextmanager
    async def fake_tenant_session(
        database_name: str,
        *,
        cluster_key: str,
    ):
        captured[
            "database_name"
        ] = database_name

        captured[
            "cluster_key"
        ] = cluster_key

        yield tenant_db

    with (
        patch(
            "app.db.tenant_context.resolve_authorized_tenant_context",
            new=AsyncMock(
                return_value=context
            ),
        ),
        patch(
            "app.db.tenant_context.tenant_session",
            new=fake_tenant_session,
        ),
        patch(
            "app.db.tenant_context.verify_tenant_identity",
            new=AsyncMock(
                return_value=make_tenant_metadata()
            ),
        ) as verify_identity,
    ):
        async with authorized_tenant_session(
            AsyncMock(),
            workspace_id=WORKSPACE_A_ID,
            user_id=USER_A_ID,
        ) as (
            routed_context,
            routed_session,
        ):
            assert routed_context == context
            assert routed_session is tenant_db

    assert captured["database_name"] == TENANT_A_DATABASE
    assert captured["cluster_key"] == "primary"

    verify_identity.assert_awaited_once_with(
        tenant_db,
        context=context,
    )


@pytest.mark.asyncio
async def test_workspace_b_context_cannot_route_to_workspace_a_database(
) -> None:
    context_b = make_context(
        workspace_id=WORKSPACE_B_ID,
        user_id=USER_B_ID,
        membership_id=MEMBERSHIP_B_ID,
        database_name=TENANT_B_DATABASE,
    )

    captured_database_names: list[str] = []

    tenant_db = AsyncMock()

    @asynccontextmanager
    async def fake_tenant_session(
        database_name: str,
        *,
        cluster_key: str,
    ):
        del cluster_key

        captured_database_names.append(
            database_name
        )

        yield tenant_db

    with (
        patch(
            "app.db.tenant_context.resolve_authorized_tenant_context",
            new=AsyncMock(
                return_value=context_b
            ),
        ),
        patch(
            "app.db.tenant_context.tenant_session",
            new=fake_tenant_session,
        ),
        patch(
            "app.db.tenant_context.verify_tenant_identity",
            new=AsyncMock(
                return_value=make_tenant_metadata(
                    workspace_id=WORKSPACE_B_ID,
                )
            ),
        ),
    ):
        async with authorized_tenant_session(
            AsyncMock(),
            workspace_id=WORKSPACE_B_ID,
            user_id=USER_B_ID,
        ):
            pass

    assert captured_database_names == [
        TENANT_B_DATABASE
    ]

    assert (
        TENANT_A_DATABASE
        not in captured_database_names
    )


@pytest.mark.asyncio
async def test_authorized_session_does_not_open_database_when_authorization_fails(
) -> None:
    tenant_session_mock = AsyncMock()

    with (
        patch(
            "app.db.tenant_context.resolve_authorized_tenant_context",
            new=AsyncMock(
                side_effect=ResourceNotFound(
                    "Workspace was not found."
                )
            ),
        ),
        patch(
            "app.db.tenant_context.tenant_session",
            new=tenant_session_mock,
        ),
    ):
        with pytest.raises(
            ResourceNotFound
        ):
            async with authorized_tenant_session(
                AsyncMock(),
                workspace_id=WORKSPACE_A_ID,
                user_id=USER_B_ID,
            ):
                pass

    tenant_session_mock.assert_not_called()


# =========================================================
# CONTEXT IMMUTABILITY
# =========================================================


def test_authorized_tenant_context_is_immutable(
) -> None:
    context = make_context()

    with pytest.raises(
        AttributeError
    ):
        context.database_name = (
            TENANT_B_DATABASE
        )


def test_authorized_tenant_context_preserves_workspace_database_mapping(
) -> None:
    context_a = make_context()

    context_b = replace(
        context_a,
        workspace_id=WORKSPACE_B_ID,
        user_id=USER_B_ID,
        membership_id=MEMBERSHIP_B_ID,
        database_name=TENANT_B_DATABASE,
    )

    assert context_a.workspace_id != context_b.workspace_id
    assert context_a.database_name != context_b.database_name

    assert context_a.database_name == TENANT_A_DATABASE
    assert context_b.database_name == TENANT_B_DATABASE