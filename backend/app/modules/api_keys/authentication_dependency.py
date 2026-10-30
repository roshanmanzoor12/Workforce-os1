from __future__ import annotations

from types import SimpleNamespace
from typing import Annotated, AsyncIterator
from uuid import UUID

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.db.tenant import tenant_session
from app.db.tenant_context import verify_tenant_identity
from app.modules.api_keys.authentication import (
    APIKeyAuthentication,
    APIKeyPrincipal,
    SUPPORTED_SCOPES,
    authentication_error,
    parse_api_key,
)
from app.modules.workspaces.models import (
    TENANT_STATUS_READY,
    TenantDatabaseRegistry,
    Workspace,
)


api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="WorkspaceAPIKey",
    auto_error=False,
)


def require_api_key(*required_scopes: str):
    required = frozenset(required_scopes)

    if not required.issubset(SUPPORTED_SCOPES):
        raise ValueError("Unsupported API key scope requirement.")

    async def dependency(
        workspace_id: UUID,
        control_session: Annotated[
            AsyncSession,
            Depends(get_control_db),
        ],
        secret: Annotated[
            str | None,
            Security(api_key_header),
        ],
    ) -> AsyncIterator[APIKeyPrincipal]:
        # Reject malformed credentials before database routing.
        parse_api_key(secret)

        result = await control_session.execute(
            select(TenantDatabaseRegistry)
            .join(
                Workspace,
                Workspace.id == TenantDatabaseRegistry.workspace_id,
            )
            .where(
                TenantDatabaseRegistry.workspace_id == workspace_id,
                TenantDatabaseRegistry.status == TENANT_STATUS_READY,
                Workspace.is_active.is_(True),
            )
        )

        registry = result.scalar_one_or_none()

        if registry is None:
            raise authentication_error()

        database_name = registry.database_name
        cluster_key = registry.cluster_key

        async with tenant_session(
            database_name,
            cluster_key=cluster_key,
        ) as tenant_db:
            # This object is only a routing identity check.
            # User authorization happens after secret verification.
            routing_identity = SimpleNamespace(
                workspace_id=workspace_id,
                schema_version=registry.schema_version,
            )

            await verify_tenant_identity(
                tenant_db,
                context=routing_identity,
            )

            authentication = APIKeyAuthentication(
                tenant_session=tenant_db,
                control_session=control_session,
                workspace_id=workspace_id,
                database_name=database_name,
                cluster_key=cluster_key,
            )

            principal = await authentication.authenticate(
                secret,
                required_scopes=required,
            )

            yield principal

    return dependency