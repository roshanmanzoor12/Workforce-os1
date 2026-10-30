from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import replace

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.effective import (
    resolve_membership_permissions,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceResourceScope,
    WorkspaceScopeType,
)
from app.modules.workspace_rbac.scope_models import (
    SAVED_RESOURCE_SCOPE_TYPES,
)
from app.modules.workspace_rbac.scope_repository import (
    MembershipScopeGrantRepository,
)
from app.modules.workspace_rbac.scope_resources import (
    TenantScopeResourceValidator,
)


def merge_saved_scopes(
    context: WorkspaceAccessContext,
    grants: Iterable[object],
) -> WorkspaceAccessContext:
    """
    Merge validated grants without changing permissions or identity.

    Callers must first validate workspace ownership, membership status,
    moderation, and current tenant resources.
    """

    scopes = list(context.scopes)
    seen = {(scope.type, scope.id) for scope in scopes}

    for grant in grants:
        scope_type = getattr(grant, "scope_type", None)
        resource_id = getattr(grant, "resource_id", None)

        if (
            getattr(grant, "membership_id", None)
            != context.membership_id
            or scope_type not in SAVED_RESOURCE_SCOPE_TYPES
            or not isinstance(resource_id, uuid.UUID)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Saved resource scope is invalid.",
            )

        scope = WorkspaceResourceScope(
            type=WorkspaceScopeType(scope_type),
            id=resource_id,
        )

        key = (scope.type, scope.id)

        if key not in seen:
            scopes.append(scope)
            seen.add(key)

    return replace(context, scopes=tuple(scopes))


async def resolve_saved_scope_access(
    control_session: AsyncSession,
    *,
    tenant_scope: object,
    context: WorkspaceAccessContext,
) -> WorkspaceAccessContext:
    """
    Add current saved grants to an existing employee access context.

    This helper performs no writes and commits neither database session.
    Deleted or inactive resources contribute no scope.
    """

    if any(
        getattr(tenant_scope, name, None) != getattr(context, name)
        for name in ("workspace_id", "user_id", "membership_id")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Saved scope identity does not match the caller.",
        )

    repository = MembershipScopeGrantRepository(control_session)

    await repository.require_workspace(
        workspace_id=context.workspace_id,
    )

    membership = await repository.require_membership(
        workspace_id=context.workspace_id,
        membership_id=context.membership_id,
        active_only=True,
    )

    if membership.user_id != context.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Saved scope membership does not match the caller.",
        )

    permissions = await resolve_membership_permissions(
        control_session,
        workspace_id=context.workspace_id,
        membership=membership,
    )

    if (
        frozenset(permissions) != context.permissions
        or membership.role_key.strip().lower() != context.role_key
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access context must be refreshed before resolving scopes.",
        )

    resources = TenantScopeResourceValidator(
        workspace_id=context.workspace_id,
        tenant_scope=tenant_scope,
    )

    grants = await repository.list_for(
        workspace_id=context.workspace_id,
        membership_id=context.membership_id,
    )

    valid_grants = []

    for grant in grants:
        # Reject malformed/cross-member rows before any resource query.
        merge_saved_scopes(context, (grant,))

        if await resources.is_active(
            scope_type=grant.scope_type,
            resource_id=grant.resource_id,
        ):
            valid_grants.append(grant)

    return merge_saved_scopes(context, valid_grants)


__all__ = [
    "merge_saved_scopes",
    "resolve_saved_scope_access",
]