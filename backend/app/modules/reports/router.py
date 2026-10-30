from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
)
from fastapi.responses import (
    Response,
)

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.reports.execution import (
    ReportExecutionService,
)
from app.modules.reports.exporter import (
    report_filename,
    report_to_csv,
)
from app.modules.reports.permissions import (
    require_report_export,
    resolve_reports_access,
)
from app.modules.reports.schemas import (
    ReportCatalogResponse,
    ReportRunRequest,
    ReportRunResponse,
    ReportsCapabilitiesResponse,
)
from app.modules.reports.service import (
    ReportsService,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/reports"
    ),
    tags=[
        "Reports",
    ],
)


@router.get(
    "/catalog",
    response_model=(
        ReportCatalogResponse
    ),
)
async def report_catalog(
    workspace_id: uuid.UUID,
    scope: TenantScope,
) -> ReportCatalogResponse:
    del workspace_id

    access = resolve_reports_access(
        scope
    )

    return ReportsService.catalog(
        access
    )


@router.get(
    "/capabilities",
    response_model=(
        ReportsCapabilitiesResponse
    ),
)
async def report_capabilities(
    workspace_id: uuid.UUID,
    scope: TenantScope,
) -> ReportsCapabilitiesResponse:
    del workspace_id

    access = resolve_reports_access(
        scope
    )

    return (
        ReportsService
        .capabilities(
            access
        )
    )


@router.post(
    "/run",
    response_model=(
        ReportRunResponse
    ),
)
async def run_report(
    workspace_id: uuid.UUID,
    request: ReportRunRequest,
    scope: TenantScope,
) -> ReportRunResponse:
    access = resolve_reports_access(
        scope
    )

    service = (
        ReportExecutionService(
            workspace_id=workspace_id,
            scope=scope,
            reports_access=access,
        )
    )

    return await service.run(
        request
    )


@router.post(
    "/export",
    response_class=Response,
)
async def export_report(
    workspace_id: uuid.UUID,
    request: ReportRunRequest,
    scope: TenantScope,
) -> Response:
    access = resolve_reports_access(
        scope
    )

    require_report_export(
        access
    )

    service = (
        ReportExecutionService(
            workspace_id=workspace_id,
            scope=scope,
            reports_access=access,
        )
    )

    result = await service.run(
        request
    )

    content = report_to_csv(
        result
    )

    filename = report_filename(
        result
    )

    return Response(
        content=content,
        media_type=(
            "text/csv; charset=utf-8"
        ),
        headers={
            "Content-Disposition": (
                "attachment; "
                f'filename="{filename}"'
            ),
        },
    )


__all__ = [
    "router",
]