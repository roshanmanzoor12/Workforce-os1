from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated, AsyncIterator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.db.tenant_context import (
    AuthorizedTenantContext,
    authorized_tenant_session,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user


ControlDB = Annotated[
    AsyncSession,
    Depends(get_control_db),
]

VerifiedUser = Annotated[
    User,
    Depends(get_current_verified_user),
]


@dataclass(slots=True)
class TenantRequestScope:
    """
    Trusted tenant routing context and sessions for one request.

    Tenant routing and physical tenant identity are verified by
    authorized_tenant_session before this scope is yielded.

    control_session is supplied by the server dependency.
    """
    context: AuthorizedTenantContext
    session: AsyncSession
    control_session: AsyncSession | None = None

    @property
    def workspace_id(self) -> uuid.UUID:
        return self.context.workspace_id

    @property
    def user_id(self) -> uuid.UUID:
        return self.context.user_id

    @property
    def membership_id(self) -> uuid.UUID:
        return self.context.membership_id

    @property
    def role_key(self) -> str:
        return self.context.role_key

    @property
    def effective_permissions(self) -> frozenset[str] | None:
        return getattr(
            self.context,
            "effective_permissions",
            None,
        )

    @property
    def schema_version(self) -> str | None:
        return self.context.schema_version


async def get_tenant_scope(
    request: Request,
    workspace_id: uuid.UUID,
    control_session: ControlDB,
    current_user: VerifiedUser,
) -> AsyncIterator[TenantRequestScope]:
    async with authorized_tenant_session(
        control_session,
        workspace_id=workspace_id,
        user_id=current_user.id,
    ) as (context, tenant_db):
        from app.modules.billing.payment_policy import feature_for_route, workspace_cleanup_route
        from app.modules.billing.workspace_billing import require_workspace_feature, require_workspace_access

        route = request.scope.get("route")
        if not workspace_cleanup_route(getattr(route, "path", ""), request.method):
            await require_workspace_access(control_session, workspace_id, current_user.id)
        feature = feature_for_route(getattr(route, "path", ""), request.method)
        if feature is not None:
            await require_workspace_feature(
                control_session, workspace_id, current_user.id, feature,
            )

        # Restoring a revoked device must not bypass enrollment quota checks.
        route_path = getattr(route, "path", "")
        if request.method == "PATCH" and route_path.endswith("/devices/{device_id}"):
            payload = await request.json()
            if isinstance(payload, dict) and payload.get("status") in {
                "pending", "active", "offline", "disabled",
            }:
                from app.modules.devices.models import Device
                from app.modules.workspace_permissions.service import WorkspacePermissionService

                WorkspacePermissionService(TenantRequestScope(
                    context=context, session=tenant_db, control_session=control_session,
                )).require("devices.manage")
                try:
                    device_id = uuid.UUID(str(request.path_params["device_id"]))
                except (ValueError, KeyError, TypeError) as exc:
                    raise HTTPException(422, "Invalid device ID.") from exc
                device = await tenant_db.get(Device, device_id)
                if device is not None and device.status == "revoked":
                    raise HTTPException(
                        409, "Re-enroll revoked devices to verify the device allowance.",
                    )

        yield TenantRequestScope(
            context=context,
            session=tenant_db,
            control_session=control_session,
        )


TenantScope = Annotated[
    TenantRequestScope,
    Depends(get_tenant_scope),
]


async def get_tenant_db(
    scope: TenantScope,
) -> AsyncSession:
    return scope.session


TenantDB = Annotated[
    AsyncSession,
    Depends(get_tenant_db),
]


__all__ = [
    "ControlDB",
    "VerifiedUser",
    "TenantRequestScope",
    "TenantScope",
    "TenantDB",
    "get_tenant_scope",
    "get_tenant_db",
]
