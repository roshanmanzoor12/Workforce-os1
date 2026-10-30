from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.db.tenant import (
    get_tenant_sessionmaker,
)
from app.db.tenant_context import (
    resolve_authorized_tenant_context,
    verify_tenant_identity,
)


# =========================================================
# TENANT SESSION RESOLVER
# =========================================================


async def resolve_tenant_session(
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    control_session: AsyncSession,
) -> AsyncSession:
    """
    Resolve and open the authorized tenant AsyncSession.

    Security sequence:

        authenticated user
            ->
        active control-plane workspace membership
            ->
        READY TenantDatabaseRegistry
            ->
        trusted database name / cluster validation
            ->
        tenant AsyncSession
            ->
        physical tenant identity verification

    Session ownership:

        The caller owns the returned AsyncSession and MUST close it.

    No database identity, URL, credential, or cluster information is
    accepted from the client.
    """

    routing_context = (
        await resolve_authorized_tenant_context(
            control_session,
            workspace_id=workspace_id,
            user_id=actor_user_id,
        )
    )

    session_factory = (
        get_tenant_sessionmaker(
            routing_context.database_name,
            cluster_key=(
                routing_context.cluster_key
            ),
        )
    )

    tenant_session = session_factory()

    try:
        await verify_tenant_identity(
            tenant_session,
            context=routing_context,
        )

        return tenant_session

    except Exception:
        await tenant_session.close()
        raise


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "resolve_tenant_session",
]