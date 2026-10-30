from __future__ import annotations

from app.modules.reports.permissions import (
    ReportsAccess,
)
from app.modules.reports.schemas import (
    ReportCatalogResponse,
    ReportDefinitionResponse,
    ReportFormat,
    ReportKey,
    ReportScope,
    ReportsCapabilitiesResponse,
)


REPORT_CATALOG = (
    ReportDefinitionResponse(
        key=ReportKey.ATTENDANCE,
        label="Attendance",
        description=(
            "Attendance records, "
            "worked time, breaks, "
            "status and summaries."
        ),
        supported_scopes=[
            ReportScope.SELF,
            ReportScope.TEAM,
            ReportScope.WORKSPACE,
        ],
        supported_formats=[
            ReportFormat.JSON,
            ReportFormat.CSV,
        ],
        supports_time_range=True,
        supports_employee_filter=True,
        supports_team_filter=True,
        supports_department_filter=True,
        supports_status_filter=True,
    ),

    ReportDefinitionResponse(
        key=ReportKey.PAYROLL,
        label="Payroll",
        description=(
            "Payroll runs, employee "
            "pay results and payslip "
            "summary data."
        ),
        supported_scopes=[
            ReportScope.SELF,
            ReportScope.WORKSPACE,
        ],
        supported_formats=[
            ReportFormat.JSON,
            ReportFormat.CSV,
        ],
        supports_time_range=True,
        supports_employee_filter=True,
        supports_team_filter=False,
        supports_department_filter=False,
        supports_status_filter=True,
    ),

    ReportDefinitionResponse(
        key=ReportKey.PRODUCTIVITY,
        label="Productivity",
        description=(
            "Observed productivity "
            "signals without opaque "
            "employee scoring."
        ),
        supported_scopes=[
            ReportScope.SELF,
            ReportScope.TEAM,
            ReportScope.WORKSPACE,
        ],
        supported_formats=[
            ReportFormat.JSON,
            ReportFormat.CSV,
        ],
        supports_time_range=True,
        supports_employee_filter=True,
        supports_team_filter=True,
        supports_department_filter=True,
        supports_status_filter=False,
    ),

    ReportDefinitionResponse(
        key=ReportKey.DEVICE_HEALTH,
        label="Device Health",
        description=(
            "Device readiness, "
            "assignment, agent state "
            "and heartbeat health."
        ),
        supported_scopes=[
            ReportScope.SELF,
            ReportScope.TEAM,
            ReportScope.WORKSPACE,
        ],
        supported_formats=[
            ReportFormat.JSON,
            ReportFormat.CSV,
        ],
        supports_time_range=False,
        supports_employee_filter=True,
        supports_team_filter=True,
        supports_department_filter=True,
        supports_status_filter=True,
    ),

    ReportDefinitionResponse(
        key=(
            ReportKey
            .MONITORING_SUMMARY
        ),
        label="Monitoring Summary",
        description=(
            "Authorized monitoring "
            "readiness and activity "
            "summary."
        ),
        supported_scopes=[
            ReportScope.SELF,
            ReportScope.TEAM,
            ReportScope.WORKSPACE,
        ],
        supported_formats=[
            ReportFormat.JSON,
            ReportFormat.CSV,
        ],
        supports_time_range=True,
        supports_employee_filter=True,
        supports_team_filter=True,
        supports_department_filter=True,
        supports_status_filter=True,
    ),

    ReportDefinitionResponse(
        key=ReportKey.GOALS,
        label="Goals",
        description=(
            "Goal status and progress "
            "within the viewer's "
            "authorized scope."
        ),
        supported_scopes=[
            ReportScope.SELF,
            ReportScope.TEAM,
            ReportScope.WORKSPACE,
        ],
        supported_formats=[
            ReportFormat.JSON,
            ReportFormat.CSV,
        ],
        supports_time_range=True,
        supports_employee_filter=True,
        supports_team_filter=True,
        supports_department_filter=True,
        supports_status_filter=True,
    ),

    ReportDefinitionResponse(
        key=ReportKey.AUDIT,
        label="Audit",
        description=(
            "Security and sensitive "
            "administrative activity "
            "history."
        ),
        supported_scopes=[
            ReportScope.WORKSPACE,
        ],
        supported_formats=[
            ReportFormat.JSON,
            ReportFormat.CSV,
        ],
        supports_time_range=True,
        supports_employee_filter=False,
        supports_team_filter=False,
        supports_department_filter=False,
        supports_status_filter=True,
    ),
)


class ReportsService:
    @staticmethod
    def catalog(
        access: ReportsAccess,
    ) -> ReportCatalogResponse:
        allowed_scopes = set(
            access.effective_scopes
        )

        items: list[
            ReportDefinitionResponse
        ] = []

        for definition in (
            REPORT_CATALOG
        ):
            visible_scopes = [
                report_scope
                for report_scope
                in (
                    definition
                    .supported_scopes
                )
                if report_scope
                in allowed_scopes
            ]

            if not visible_scopes:
                continue

            payload = (
                definition
                .model_copy(
                    deep=True
                )
            )

            payload.supported_scopes = (
                visible_scopes
            )

            if not access.can_export:
                payload.supported_formats = []

            items.append(
                payload
            )

        return ReportCatalogResponse(
            items=items
        )

    @staticmethod
    def capabilities(
        access: ReportsAccess,
    ) -> ReportsCapabilitiesResponse:
        catalog = (
            ReportsService
            .catalog(
                access
            )
        )

        return (
            ReportsCapabilitiesResponse(
                can_read_self=(
                    access
                    .can_read_self
                ),
                can_read_team=(
                    access
                    .can_read_team
                ),
                can_read_workspace=(
                    access
                    .can_read_workspace
                ),
                can_export=(
                    access
                    .can_export
                ),
                effective_scopes=(
                    access
                    .effective_scopes
                ),
                available_reports=[
                    item.key
                    for item
                    in catalog.items
                ],
                export_formats=(
                    [
                        ReportFormat.JSON,
                        ReportFormat.CSV,
                    ]
                    if access.can_export
                    else []
                ),
                async_exports_supported=False,
            )
        )


__all__ = [
    "REPORT_CATALOG",
    "ReportsService",
]