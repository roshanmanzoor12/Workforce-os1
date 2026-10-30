from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select

from app.core.exceptions import ResourceNotFound
from app.modules.employees.models import Department, Team
from app.modules.workspace_rbac.scope_repository import (
    MembershipScopeGrantRepository,
)


class TenantScopeResourceValidator:
    """
    Validate resource IDs in an already authorized tenant request scope.

    Never select a tenant database from a submitted resource ID.
    """

    def __init__(
        self,
        *,
        workspace_id: uuid.UUID,
        tenant_scope: object,
    ) -> None:
        if (
            not isinstance(workspace_id, uuid.UUID)
            or getattr(tenant_scope, "workspace_id", None) != workspace_id
            or getattr(tenant_scope, "session", None) is None
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authorized tenant resource scope is unavailable.",
            )

        self.session = tenant_scope.session

    async def is_active(
        self,
        *,
        scope_type: str,
        resource_id: uuid.UUID,
    ) -> bool:
        scope_type = (
            MembershipScopeGrantRepository.validate_scope_type(
                scope_type,
            )
        )

        MembershipScopeGrantRepository.validate_uuid(
            resource_id,
            name="resource ID",
        )

        model = Department if scope_type == "department" else Team

        found_id = await self.session.scalar(
            select(model.id).where(
                model.id == resource_id,
                model.is_active.is_(True),
            ),
        )

        return found_id == resource_id

    async def require_active(
        self,
        *,
        scope_type: str,
        resource_id: uuid.UUID,
    ) -> None:
        if await self.is_active(
            scope_type=scope_type,
            resource_id=resource_id,
        ):
            return

        raise ResourceNotFound(
            "Active scope resource was not found in this workspace."
        )


__all__ = ["TenantScopeResourceValidator"]