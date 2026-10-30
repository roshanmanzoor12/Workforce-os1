from __future__ import annotations

import uuid
from collections.abc import (
    AsyncIterator,
)

from fastapi import (
    Depends,
    HTTPException,
    Path,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import (
    get_control_db,
)
from app.modules.auth.permissions import (
    get_current_verified_user,
)
from app.modules.memberships.repository import (
    WorkspaceMembershipRepository,
)
from app.modules.tenant_api.context import (
    AuthorizedTenantContext,
)
from app.modules.tenant_api.identity import (
    user_id_from,
)
from app.modules.tenant_api.provider import (
    get_registered_tenant_session_resolver,
)
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
)


# =========================================================
# AUTHORIZED TENANT CONTEXT
# =========================================================


async def get_authorized_tenant_context(
    workspace_id: uuid.UUID = Path(
        ...,
        description=(
            "Workspace whose authorized tenant "
            "database should be used."
        ),
    ),
    control_session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> AsyncIterator[
    AuthorizedTenantContext
]:
    """
    Resolve a request-scoped authorized tenant context.

    Security sequence:

        verified global user
            ->
        active WorkspaceMembership
            ->
        registered backend tenant resolver
            ->
        trusted tenant AsyncSession
            ->
        physical tenant identity verification
            ->
        tenant-domain service
            ->
        tenant session closed after request

    Client-controlled input:

        workspace_id only

    The client must never provide:

        database name
        database URL
        database password
        PostgreSQL credentials
        tenant connection string
    """

    # -----------------------------------------------------
    # GLOBAL USER
    # -----------------------------------------------------

    actor_user_id = user_id_from(
        current_user
    )

    # -----------------------------------------------------
    # CONTROL-PLANE MEMBERSHIP
    # -----------------------------------------------------

    memberships = (
        WorkspaceMembershipRepository(
            control_session
        )
    )

    membership = (
        await memberships
        .get_active_for_user(
            workspace_id=workspace_id,
            user_id=actor_user_id,
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Active workspace membership "
                "required."
            ),
        )

    # Defensive validation.
    #
    # get_active_for_user() should already enforce these
    # boundaries, but explicit checks protect against future
    # repository regressions.

    if (
        membership.workspace_id
        != workspace_id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Workspace membership does not "
                "belong to this workspace."
            ),
        )

    if (
        membership.user_id
        != actor_user_id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Workspace membership does not "
                "belong to the authenticated user."
            ),
        )

    if (
        membership.status
        != MEMBERSHIP_STATUS_ACTIVE
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Workspace membership is "
                "not active."
            ),
        )

    # -----------------------------------------------------
    # BACKEND TENANT RESOLVER
    # -----------------------------------------------------

    try:
        resolver = (
            get_registered_tenant_session_resolver()
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Tenant database resolver "
                "is not configured."
            ),
        ) from exc

    # -----------------------------------------------------
    # TENANT SESSION
    # -----------------------------------------------------

    tenant_session: (
        AsyncSession | None
    ) = None

    try:
        tenant_session = await resolver(
            workspace_id,
            actor_user_id,
            control_session,
        )

    except HTTPException:
        raise

    except RuntimeError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Tenant database is currently "
                "unavailable."
            ),
        ) from exc

    if tenant_session is None:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Tenant database session "
                "could not be resolved."
            ),
        )

    if not isinstance(
        tenant_session,
        AsyncSession,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Tenant resolver returned an "
                "invalid session type."
            ),
        )

    # -----------------------------------------------------
    # REQUEST-SCOPED CONTEXT
    # -----------------------------------------------------

    try:
        yield AuthorizedTenantContext(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            control_session=control_session,
            tenant_session=tenant_session,
        )

    finally:
        try:
            await tenant_session.close()

        except Exception:
            # Session cleanup must not hide the original
            # request exception.
            pass


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "get_authorized_tenant_context",
]