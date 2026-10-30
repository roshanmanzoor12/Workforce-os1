from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import (
    Depends,
    HTTPException,
    Request,
)

from app.modules.monitoring_admin.service import (
    MonitoringAdminService,
    MonitoringPolicyDisabledError,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)


TenantContext = Annotated[
    Any,
    Depends(
        get_authorized_tenant_context
    ),
]


async def require_live_monitoring_policy(
    request: Request,
    workspace_id: uuid.UUID,
    context: TenantContext,
) -> None:
    """
    Workspace policy gate applied to the existing
    Phase 14 live-monitoring router.

    It does not replace RBAC.

    Existing live_monitoring access checks still
    authorize who may perform the operation.

    This layer answers whether the workspace policy
    allows the sensitive feature at all.
    """

    path = request.url.path.lower()

    # Capability discovery remains readable even
    # when capture functionality is disabled.
    if path.endswith(
        "/live-monitoring/capabilities"
    ):
        return

    service = MonitoringAdminService(
        tenant_session=(
            context.tenant_session
        ),
        workspace_id=workspace_id,
    )

    try:
        if "/screenshots" in path:
            await (
                service
                .require_screenshot_allowed()
            )

            return

        if "/live-sessions" in path:
            await (
                service
                .require_live_screen_allowed()
            )

            return

    except MonitoringPolicyDisabledError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(
                exc
            ),
        ) from exc


__all__ = [
    "require_live_monitoring_policy",
]