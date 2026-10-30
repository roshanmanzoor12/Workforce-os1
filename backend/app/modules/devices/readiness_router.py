from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)

from app.modules.devices.readiness_schemas import (
    DeviceReadinessResponse,
)


# =========================================================
# REQUEST STATE KEY
# =========================================================

DEVICE_READINESS_SCOPE_STATE_KEY = (
    "device_readiness_scope"
)


# =========================================================
# ROUTER
# =========================================================


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/devices"
    ),
    tags=[
        "Device Readiness",
    ],
)


# =========================================================
# READINESS
# =========================================================


@router.get(
    "/readiness",
    response_model=(
        DeviceReadinessResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Get workspace device readiness"
    ),
)
async def get_device_readiness(
    workspace_id: uuid.UUID,
    request: Request,
) -> DeviceReadinessResponse:
    """
    Browser-safe workspace device readiness.

    Important import-boundary rule:

    This module deliberately imports no tenant authorization
    dependency at module-import time.

    The aggregate tenant API binds the already-authorized TenantScope
    into request.state before this endpoint runs.

    This prevents the circular-import sequence that caused FastAPI to
    copy an empty child router during tenant_api.router construction.
    """

    # -----------------------------------------------------
    # RESOLVE TRUSTED SCOPE
    # -----------------------------------------------------

    scope = getattr(
        request.state,
        DEVICE_READINESS_SCOPE_STATE_KEY,
        None,
    )

    if scope is None:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Device readiness tenant "
                "scope is unavailable."
            ),
        )

    # -----------------------------------------------------
    # WORKSPACE BOUNDARY
    # -----------------------------------------------------

    trusted_workspace_id = getattr(
        scope,
        "workspace_id",
        None,
    )

    if (
        trusted_workspace_id
        != workspace_id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Workspace authorization "
                "context mismatch."
            ),
        )

    tenant_session = getattr(
        scope,
        "session",
        None,
    )

    if tenant_session is None:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Authorized tenant session "
                "is unavailable."
            ),
        )

    # -----------------------------------------------------
    # DEFERRED DOMAIN IMPORTS
    # -----------------------------------------------------

    from app.core.exceptions import (
        ValidationError,
    )

    from app.modules.devices.readiness_access import (
        resolve_device_readiness_access,
    )

    from app.modules.devices.readiness_service import (
        DeviceReadinessService,
    )

    # -----------------------------------------------------
    # EFFECTIVE ACCESS
    # -----------------------------------------------------

    try:
        access = await (
            resolve_device_readiness_access(
                workspace_id=workspace_id,
                context=scope,
            )
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(
                exc
            ),
        ) from exc

    # -----------------------------------------------------
    # READINESS
    # -----------------------------------------------------

    service = DeviceReadinessService(
        tenant_session
    )

    return await (
        service.get_readiness(
            access=access
        )
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DEVICE_READINESS_SCOPE_STATE_KEY",
    "get_device_readiness",
    "router",
]