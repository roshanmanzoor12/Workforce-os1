from __future__ import annotations

import inspect
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.workspaces.models import (
    TENANT_STATUS_FAILED,
    TENANT_STATUS_PENDING,
    TENANT_STATUS_PROVISIONING,
    TENANT_STATUS_READY,
    WORKSPACE_STATUS_PROVISIONING,
    WORKSPACE_STATUS_READY,
)
from app.modules.workspaces.provisioning import (
    WorkspaceProvisioningError,
    WorkspaceProvisioningResult,
    provision_workspace_tenant,
    retry_workspace_tenant_provisioning,
)


# =========================================================
# CONSTANTS
# =========================================================

WORKSPACE_ID = uuid.UUID(
    "11111111-1111-4111-8111-111111111111"
)

DATABASE_NAME = (
    "tenant_11111111111141118111111111111111"
)

SCHEMA_VERSION = "p6k7l8m9n0o1"


# =========================================================
# HELPERS
# =========================================================


def make_workspace(
    *,
    status: str = WORKSPACE_STATUS_PROVISIONING,
    is_active: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=WORKSPACE_ID,
        status=status,
        is_active=is_active,
    )


def make_registry(
    *,
    status: str = TENANT_STATUS_PENDING,
    schema_version: str | None = None,
    provision_attempts: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        workspace_id=WORKSPACE_ID,
        database_name=DATABASE_NAME,
        cluster_key="primary",
        status=status,
        schema_version=schema_version,
        provision_attempts=provision_attempts,
        provisioned_at=None,
        failed_at=None,
        last_error_code=None,
        last_error_message=None,
    )


def make_provision_result(
    *,
    created: bool = True,
    already_existed: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        database_name=DATABASE_NAME,
        cluster_key="primary",
        created=created,
        already_existed=already_existed,
    )


def make_initialization_result(
    *,
    metadata_created: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        workspace_id=WORKSPACE_ID,
        database_name=DATABASE_NAME,
        schema_version=SCHEMA_VERSION,
        metadata_created=metadata_created,
        registry_marked_ready=True,
    )


# =========================================================
# PUBLIC API SECURITY
# =========================================================


def test_provisioning_api_does_not_accept_database_name(
) -> None:
    signature = inspect.signature(
        provision_workspace_tenant
    )

    assert "workspace_id" in signature.parameters
    assert "database_name" not in signature.parameters
    assert "database_url" not in signature.parameters
    assert "cluster_key" not in signature.parameters


def test_retry_api_does_not_accept_database_name(
) -> None:
    signature = inspect.signature(
        retry_workspace_tenant_provisioning
    )

    assert "workspace_id" in signature.parameters
    assert "database_name" not in signature.parameters
    assert "database_url" not in signature.parameters


# =========================================================
# SUCCESSFUL PROVISIONING
# =========================================================


@pytest.mark.asyncio
async def test_provision_workspace_tenant_success(
) -> None:
    session = AsyncMock()

    workspace = make_workspace()
    registry = make_registry()

    load_mock = AsyncMock(
        return_value=(
            workspace,
            registry,
        )
    )

    mark_provisioning_mock = AsyncMock()
    mark_ready_mock = AsyncMock()

    physical_provision_mock = AsyncMock(
        return_value=make_provision_result(
            created=True,
            already_existed=False,
        )
    )

    migration_mock = AsyncMock()

    initialization_mock = AsyncMock(
        return_value=make_initialization_result(
            metadata_created=True,
        )
    )

    with (
        patch(
            "app.modules.workspaces.provisioning._load_workspace_and_registry",
            new=load_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning._mark_provisioning",
            new=mark_provisioning_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning.provision_tenant_database",
            new=physical_provision_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning.upgrade_tenant_database_to_head",
            new=migration_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning.initialize_registered_tenant",
            new=initialization_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning._mark_workspace_ready",
            new=mark_ready_mock,
        ),
    ):
        result = await provision_workspace_tenant(
            session,
            workspace_id=WORKSPACE_ID,
        )

    assert isinstance(
        result,
        WorkspaceProvisioningResult,
    )

    assert result.workspace_id == WORKSPACE_ID
    assert result.database_name == DATABASE_NAME
    assert result.cluster_key == "primary"
    assert result.schema_version == SCHEMA_VERSION

    assert result.database_created is True
    assert result.database_already_existed is False
    assert result.metadata_created is True

    assert result.workspace_ready is True
    assert result.tenant_ready is True

    load_mock.assert_awaited_once_with(
        session,
        workspace_id=WORKSPACE_ID,
    )

    mark_provisioning_mock.assert_awaited_once_with(
        session,
        workspace=workspace,
        registry=registry,
    )

    physical_provision_mock.assert_awaited_once_with(
        DATABASE_NAME,
        cluster_key="primary",
    )

    migration_mock.assert_awaited_once_with(
        DATABASE_NAME,
        cluster_key="primary",
    )

    initialization_mock.assert_awaited_once_with(
        session,
        workspace_id=WORKSPACE_ID,
        schema_version=SCHEMA_VERSION,
    )

    mark_ready_mock.assert_awaited_once_with(
        session,
        workspace=workspace,
        registry=registry,
    )


# =========================================================
# IDEMPOTENCY
# =========================================================


@pytest.mark.asyncio
async def test_ready_workspace_is_idempotent(
) -> None:
    session = AsyncMock()

    workspace = make_workspace(
        status=WORKSPACE_STATUS_READY,
    )

    registry = make_registry(
        status=TENANT_STATUS_READY,
        schema_version=SCHEMA_VERSION,
    )

    load_mock = AsyncMock(
        return_value=(
            workspace,
            registry,
        )
    )

    physical_provision_mock = AsyncMock()
    migration_mock = AsyncMock()
    initialization_mock = AsyncMock()

    with (
        patch(
            "app.modules.workspaces.provisioning._load_workspace_and_registry",
            new=load_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning.provision_tenant_database",
            new=physical_provision_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning.upgrade_tenant_database_to_head",
            new=migration_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning.initialize_registered_tenant",
            new=initialization_mock,
        ),
    ):
        result = await provision_workspace_tenant(
            session,
            workspace_id=WORKSPACE_ID,
        )

    assert result.database_created is False
    assert result.database_already_existed is True
    assert result.metadata_created is False
    assert result.workspace_ready is True
    assert result.tenant_ready is True

    physical_provision_mock.assert_not_awaited()
    migration_mock.assert_not_awaited()
    initialization_mock.assert_not_awaited()


# =========================================================
# RETRY
# =========================================================


@pytest.mark.asyncio
async def test_retry_uses_same_registered_database(
) -> None:
    session = AsyncMock()

    expected = WorkspaceProvisioningResult(
        workspace_id=WORKSPACE_ID,
        database_name=DATABASE_NAME,
        cluster_key="primary",
        schema_version=SCHEMA_VERSION,
        database_created=False,
        database_already_existed=True,
        metadata_created=False,
        workspace_ready=True,
        tenant_ready=True,
    )

    provision_mock = AsyncMock(
        return_value=expected
    )

    with patch(
        "app.modules.workspaces.provisioning.provision_workspace_tenant",
        new=provision_mock,
    ):
        result = (
            await retry_workspace_tenant_provisioning(
                session,
                workspace_id=WORKSPACE_ID,
            )
        )

    assert result == expected

    provision_mock.assert_awaited_once_with(
        session,
        workspace_id=WORKSPACE_ID,
    )


# =========================================================
# INVALID TENANT STATE
# =========================================================


@pytest.mark.asyncio
async def test_suspended_tenant_cannot_be_provisioned(
) -> None:
    session = AsyncMock()

    workspace = make_workspace()

    registry = make_registry(
        status="suspended",
    )

    with patch(
        "app.modules.workspaces.provisioning._load_workspace_and_registry",
        new=AsyncMock(
            return_value=(
                workspace,
                registry,
            )
        ),
    ):
        with pytest.raises(
            WorkspaceProvisioningError,
            match="not in a provisionable state",
        ):
            await provision_workspace_tenant(
                session,
                workspace_id=WORKSPACE_ID,
            )


@pytest.mark.asyncio
async def test_decommissioned_tenant_cannot_be_provisioned(
) -> None:
    session = AsyncMock()

    workspace = make_workspace()

    registry = make_registry(
        status="decommissioned",
    )

    with patch(
        "app.modules.workspaces.provisioning._load_workspace_and_registry",
        new=AsyncMock(
            return_value=(
                workspace,
                registry,
            )
        ),
    ):
        with pytest.raises(
            WorkspaceProvisioningError,
            match="not in a provisionable state",
        ):
            await provision_workspace_tenant(
                session,
                workspace_id=WORKSPACE_ID,
            )


# =========================================================
# FAILURE HANDLING
# =========================================================


@pytest.mark.asyncio
async def test_physical_database_failure_marks_registry_failed(
) -> None:
    session = AsyncMock()

    initial_workspace = make_workspace()
    initial_registry = make_registry()

    failed_workspace = make_workspace()
    failed_registry = make_registry(
        status=TENANT_STATUS_PROVISIONING,
    )

    load_mock = AsyncMock(
        side_effect=[
            (
                initial_workspace,
                initial_registry,
            ),
            (
                failed_workspace,
                failed_registry,
            ),
        ]
    )

    mark_provisioning_mock = AsyncMock()
    mark_failed_mock = AsyncMock()
    dispose_mock = AsyncMock()

    physical_error = RuntimeError(
        "simulated physical provisioning failure"
    )

    with (
        patch(
            "app.modules.workspaces.provisioning._load_workspace_and_registry",
            new=load_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning._mark_provisioning",
            new=mark_provisioning_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning.provision_tenant_database",
            new=AsyncMock(
                side_effect=physical_error
            ),
        ),
        patch(
            "app.modules.workspaces.provisioning._mark_failed",
            new=mark_failed_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning.dispose_tenant_engine",
            new=dispose_mock,
        ),
    ):
        with pytest.raises(
            WorkspaceProvisioningError,
            match="provisioning failed",
        ):
            await provision_workspace_tenant(
                session,
                workspace_id=WORKSPACE_ID,
            )

    mark_provisioning_mock.assert_awaited_once()

    mark_failed_mock.assert_awaited_once_with(
        session,
        workspace=failed_workspace,
        registry=failed_registry,
        exc=physical_error,
    )

    dispose_mock.assert_awaited_once_with(
        DATABASE_NAME,
        cluster_key="primary",
    )


@pytest.mark.asyncio
async def test_migration_failure_never_marks_workspace_ready(
) -> None:
    session = AsyncMock()

    initial_workspace = make_workspace()
    initial_registry = make_registry()

    failed_workspace = make_workspace()
    failed_registry = make_registry(
        status=TENANT_STATUS_PROVISIONING,
    )

    load_mock = AsyncMock(
        side_effect=[
            (
                initial_workspace,
                initial_registry,
            ),
            (
                failed_workspace,
                failed_registry,
            ),
        ]
    )

    mark_ready_mock = AsyncMock()
    mark_failed_mock = AsyncMock()

    migration_error = RuntimeError(
        "simulated tenant migration failure"
    )

    with (
        patch(
            "app.modules.workspaces.provisioning._load_workspace_and_registry",
            new=load_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning._mark_provisioning",
            new=AsyncMock(),
        ),
        patch(
            "app.modules.workspaces.provisioning.provision_tenant_database",
            new=AsyncMock(
                return_value=make_provision_result()
            ),
        ),
        patch(
            "app.modules.workspaces.provisioning.upgrade_tenant_database_to_head",
            new=AsyncMock(
                side_effect=migration_error
            ),
        ),
        patch(
            "app.modules.workspaces.provisioning._mark_workspace_ready",
            new=mark_ready_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning._mark_failed",
            new=mark_failed_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning.dispose_tenant_engine",
            new=AsyncMock(),
        ),
    ):
        with pytest.raises(
            WorkspaceProvisioningError
        ):
            await provision_workspace_tenant(
                session,
                workspace_id=WORKSPACE_ID,
            )

    mark_ready_mock.assert_not_awaited()

    mark_failed_mock.assert_awaited_once_with(
        session,
        workspace=failed_workspace,
        registry=failed_registry,
        exc=migration_error,
    )


@pytest.mark.asyncio
async def test_initialization_failure_never_marks_workspace_ready(
) -> None:
    session = AsyncMock()

    initial_workspace = make_workspace()
    initial_registry = make_registry()

    failed_workspace = make_workspace()
    failed_registry = make_registry(
        status=TENANT_STATUS_PROVISIONING,
    )

    load_mock = AsyncMock(
        side_effect=[
            (
                initial_workspace,
                initial_registry,
            ),
            (
                failed_workspace,
                failed_registry,
            ),
        ]
    )

    mark_ready_mock = AsyncMock()
    mark_failed_mock = AsyncMock()

    initialization_error = RuntimeError(
        "simulated metadata initialization failure"
    )

    with (
        patch(
            "app.modules.workspaces.provisioning._load_workspace_and_registry",
            new=load_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning._mark_provisioning",
            new=AsyncMock(),
        ),
        patch(
            "app.modules.workspaces.provisioning.provision_tenant_database",
            new=AsyncMock(
                return_value=make_provision_result()
            ),
        ),
        patch(
            "app.modules.workspaces.provisioning.upgrade_tenant_database_to_head",
            new=AsyncMock(),
        ),
        patch(
            "app.modules.workspaces.provisioning.initialize_registered_tenant",
            new=AsyncMock(
                side_effect=initialization_error
            ),
        ),
        patch(
            "app.modules.workspaces.provisioning._mark_workspace_ready",
            new=mark_ready_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning._mark_failed",
            new=mark_failed_mock,
        ),
        patch(
            "app.modules.workspaces.provisioning.dispose_tenant_engine",
            new=AsyncMock(),
        ),
    ):
        with pytest.raises(
            WorkspaceProvisioningError
        ):
            await provision_workspace_tenant(
                session,
                workspace_id=WORKSPACE_ID,
            )

    mark_ready_mock.assert_not_awaited()

    mark_failed_mock.assert_awaited_once_with(
        session,
        workspace=failed_workspace,
        registry=failed_registry,
        exc=initialization_error,
    )


# =========================================================
# STATE TRANSITIONS
# =========================================================


@pytest.mark.asyncio
async def test_mark_provisioning_increments_attempt_count(
) -> None:
    from app.modules.workspaces.provisioning import (
        _mark_provisioning,
    )

    session = AsyncMock()

    workspace = make_workspace(
        status=WORKSPACE_STATUS_PROVISIONING,
    )

    registry = make_registry(
        status=TENANT_STATUS_PENDING,
        provision_attempts=2,
    )

    registry.failed_at = object()
    registry.last_error_code = "OLD_ERROR"
    registry.last_error_message = "old error"

    await _mark_provisioning(
        session,
        workspace=workspace,
        registry=registry,
    )

    assert (
        workspace.status
        == WORKSPACE_STATUS_PROVISIONING
    )

    assert (
        registry.status
        == TENANT_STATUS_PROVISIONING
    )

    assert registry.provision_attempts == 3

    assert registry.failed_at is None
    assert registry.last_error_code is None
    assert registry.last_error_message is None

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_failed_never_marks_workspace_ready(
) -> None:
    from app.modules.workspaces.provisioning import (
        _mark_failed,
    )

    session = AsyncMock()

    workspace = make_workspace(
        status=WORKSPACE_STATUS_PROVISIONING,
    )

    registry = make_registry(
        status=TENANT_STATUS_PROVISIONING,
    )

    await _mark_failed(
        session,
        workspace=workspace,
        registry=registry,
        exc=RuntimeError(
            "secret driver details should not be persisted"
        ),
    )

    assert (
        workspace.status
        == WORKSPACE_STATUS_PROVISIONING
    )

    assert (
        registry.status
        == TENANT_STATUS_FAILED
    )

    assert registry.failed_at is not None
    assert registry.last_error_code is not None

    assert (
        registry.last_error_message
        == (
            "Tenant database provisioning failed. "
            "The operation may be retried."
        )
    )

    assert (
        "secret driver details"
        not in registry.last_error_message
    )

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_workspace_ready_sets_both_planes_ready(
) -> None:
    from app.modules.workspaces.provisioning import (
        _mark_workspace_ready,
    )

    session = AsyncMock()

    workspace = make_workspace(
        status=WORKSPACE_STATUS_PROVISIONING,
        is_active=False,
    )

    registry = make_registry(
        status=TENANT_STATUS_PROVISIONING,
    )

    await _mark_workspace_ready(
        session,
        workspace=workspace,
        registry=registry,
    )

    assert workspace.status == WORKSPACE_STATUS_READY
    assert workspace.is_active is True

    assert registry.status == TENANT_STATUS_READY
    assert registry.schema_version == SCHEMA_VERSION
    assert registry.provisioned_at is not None

    assert registry.failed_at is None
    assert registry.last_error_code is None
    assert registry.last_error_message is None

    session.commit.assert_awaited_once()
