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
    status,
)

from app.core.exceptions import (
    ValidationError,
)
from app.modules.employee_monitoring_detail.access import (
    resolve_employee_monitoring_detail_access,
)
from app.modules.employee_monitoring_detail.schemas import (
    EmployeeMonitoringDetailResponse,
)
from app.modules.employee_monitoring_detail.service import (
    EmployeeMonitoringDetailNotFoundError,
    EmployeeMonitoringDetailService,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)


# =========================================================
# ROUTER
# =========================================================


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/employee-monitoring"
    ),
    tags=[
        "employee-monitoring",
    ],
)


TenantContext = Annotated[
    Any,
    Depends(
        get_authorized_tenant_context
    ),
]


# =========================================================
# DETAIL
# =========================================================


@router.get(
    "/{employee_id}",
    response_model=(
        EmployeeMonitoringDetailResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Get scoped employee monitoring detail"
    ),
)
async def get_employee_monitoring_detail(
    workspace_id: uuid.UUID,
    employee_id: uuid.UUID,
    context: TenantContext,

    history_limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),

    screenshot_limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
) -> EmployeeMonitoringDetailResponse:
    try:
        access = await (
            resolve_employee_monitoring_detail_access(
                workspace_id=(
                    workspace_id
                ),
                context=context,
            )
        )

        service = (
            EmployeeMonitoringDetailService(
                context.tenant_session
            )
        )

        return await service.get_detail(
            access=access,
            employee_id=employee_id,
            history_limit=history_limit,
            screenshot_limit=(
                screenshot_limit
            ),
        )

    except (
        EmployeeMonitoringDetailNotFoundError
    ) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(
                exc
            ),
        ) from exc

    except ValidationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(
                exc
            ),
        ) from exc


__all__ = [
    "get_employee_monitoring_detail",
    "router",
]