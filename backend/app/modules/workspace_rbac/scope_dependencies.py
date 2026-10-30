from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.db.tenant_dependency import ControlDB, TenantScope
from app.modules.workspace_rbac.scope_service import (
    MembershipScopeGrantService,
)


def get_membership_scope_service(
    workspace_id: uuid.UUID,
    scope: TenantScope,
    control_session: ControlDB,
) -> MembershipScopeGrantService:
    """
    Build the service from authenticated server-side dependencies.

    The URL workspace must match the resolved tenant workspace.
    Actor identity and tenant session never come from request payloads.
    """

    if getattr(scope, "workspace_id", None) != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scope-management workspace does not match the caller.",
        )

    return MembershipScopeGrantService(
        control_session,
        scope,
    )


MembershipScopeServiceDep = Annotated[
    MembershipScopeGrantService,
    Depends(get_membership_scope_service),
]


__all__ = [
    "get_membership_scope_service",
    "MembershipScopeServiceDep",
]