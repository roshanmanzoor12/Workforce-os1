from __future__ import annotations

import uuid
from typing import (
    Annotated,
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.core.exceptions import (
    ValidationError,
)
from app.modules.live_monitoring.phase17 import (
    record_screenshot_audit,
)
from app.modules.monitoring_admin.access import (
    resolve_monitoring_admin_access,
)
from app.modules.monitoring_admin.schemas import (
    MonitoringAdminPolicyPublic,
    MonitoringAdminPolicyUpdate,
    MonitoringAdminSummaryResponse,
    MonitoringPolicyCapabilities,
    MonitoringScreenshotRetentionCleanupResponse,
)
from app.modules.monitoring_admin.service import (
    MonitoringAdminService,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/monitoring-admin"
    ),
    tags=[
        "Monitoring Admin",
    ],
)


TenantContext = Annotated[
    Any,
    Depends(
        get_authorized_tenant_context
    ),
]


def _service(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> MonitoringAdminService:
    return MonitoringAdminService(
        tenant_session=(
            context.tenant_session
        ),
        workspace_id=workspace_id,
    )


async def _access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
):
    return await (
        resolve_monitoring_admin_access(
            workspace_id=workspace_id,
            context=context,
        )
    )


def _translate(
    exc: Exception,
) -> HTTPException:
    if isinstance(
        exc,
        ValidationError,
    ):
        return HTTPException(
            status_code=403,
            detail=str(
                exc
            ),
        )

    raise exc


@router.get(
    "",
    response_model=(
        MonitoringAdminSummaryResponse
    ),
)
async def get_monitoring_admin_summary(
    workspace_id: uuid.UUID,
    context: TenantContext,
) -> MonitoringAdminSummaryResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .summary(
                access=access
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.get(
    "/policy",
    response_model=(
        MonitoringAdminPolicyPublic
    ),
)
async def get_monitoring_policy(
    workspace_id: uuid.UUID,
    context: TenantContext,
) -> MonitoringAdminPolicyPublic:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        summary = await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .summary(
                access=access
            )
        )

        return summary.policy

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.patch(
    "/policy",
    response_model=(
        MonitoringAdminPolicyPublic
    ),
)
async def update_monitoring_policy(
    workspace_id: uuid.UUID,
    payload: MonitoringAdminPolicyUpdate,
    context: TenantContext,
) -> MonitoringAdminPolicyPublic:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        result = await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .update_policy(
                access=access,
                payload=payload,
            )
        )

        await (
            context
            .tenant_session
            .commit()
        )

        return result

    except Exception as exc:
        await (
            context
            .tenant_session
            .rollback()
        )

        raise _translate(
            exc
        ) from exc


@router.get(
    "/capabilities",
    response_model=(
        MonitoringPolicyCapabilities
    ),
)
async def get_monitoring_policy_capabilities(
    workspace_id: uuid.UUID,
    context: TenantContext,
) -> MonitoringPolicyCapabilities:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        summary = await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .summary(
                access=access
            )
        )

        return summary.capabilities

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.post(
    "/screenshots/retention-cleanup",
    response_model=(
        MonitoringScreenshotRetentionCleanupResponse
    ),
)
async def cleanup_screenshot_retention(
    workspace_id: uuid.UUID,

    context: TenantContext,

    limit: int = Query(
        default=500,
        ge=1,
        le=5000,
    ),
) -> (
    MonitoringScreenshotRetentionCleanupResponse
):
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        result = await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .cleanup_screenshot_retention(
                access=access,
                limit=limit,
            )
        )

        await record_screenshot_audit(
            control_session=(
                context.control_session
            ),

            workspace_id=workspace_id,

            actor_user_id=(
                access.actor_user_id
            ),

            action=(
                "screenshot.retention.cleanup"
            ),

            event_data={
                "retention_days": (
                    result.retention_days
                ),

                "cutoff_at": (
                    result.cutoff_at
                ),

                "scanned": (
                    result.scanned
                ),

                "deleted": (
                    result.deleted
                ),

                "storage_failures": (
                    result.storage_failures
                ),

                "database_failures": (
                    result.database_failures
                ),

                "has_more": (
                    result.has_more
                ),
            },
        )

        return result

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


__all__ = [
    "router",
]