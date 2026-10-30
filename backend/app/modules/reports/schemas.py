from __future__ import annotations

import uuid

from datetime import datetime
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class ReportScope(
    StrEnum
):
    SELF = "self"
    TEAM = "team"
    WORKSPACE = "workspace"


class ReportFormat(
    StrEnum
):
    JSON = "json"
    CSV = "csv"


class ReportKey(
    StrEnum
):
    ATTENDANCE = "attendance"
    PAYROLL = "payroll"
    PRODUCTIVITY = "productivity"
    DEVICE_HEALTH = "device_health"
    MONITORING_SUMMARY = (
        "monitoring_summary"
    )
    GOALS = "goals"
    AUDIT = "audit"


class ReportsSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )


class ReportDefinitionResponse(
    ReportsSchema
):
    key: ReportKey

    label: str

    description: str

    supported_scopes: list[
        ReportScope
    ] = Field(
        default_factory=list
    )

    supported_formats: list[
        ReportFormat
    ] = Field(
        default_factory=list
    )

    supports_time_range: bool = True

    supports_employee_filter: bool = False

    supports_team_filter: bool = False

    supports_department_filter: bool = False

    supports_status_filter: bool = False


class ReportCatalogResponse(
    ReportsSchema
):
    items: list[
        ReportDefinitionResponse
    ] = Field(
        default_factory=list
    )


class ReportsCapabilitiesResponse(
    ReportsSchema
):
    can_read_self: bool

    can_read_team: bool

    can_read_workspace: bool

    can_export: bool

    effective_scopes: list[
        ReportScope
    ] = Field(
        default_factory=list
    )

    available_reports: list[
        ReportKey
    ] = Field(
        default_factory=list
    )

    export_formats: list[
        ReportFormat
    ] = Field(
        default_factory=list
    )

    async_exports_supported: bool = False


class ReportRunRequest(
    ReportsSchema
):
    report: ReportKey

    scope: ReportScope

    start_at: datetime | None = None
    end_at: datetime | None = None

    employee_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None

    status: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    limit: int = Field(
        default=500,
        ge=1,
        le=5000,
    )

    @model_validator(
        mode="after"
    )
    def validate_window(
        self,
    ) -> "ReportRunRequest":
        if (
            self.start_at is not None
            and self.end_at is not None
            and self.start_at
            >= self.end_at
        ):
            raise ValueError(
                "start_at must be earlier "
                "than end_at."
            )

        return self


class ReportParametersResponse(
    ReportsSchema
):
    start_at: datetime | None = None
    end_at: datetime | None = None

    employee_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None

    status: str | None = None

    limit: int


class ReportRunResponse(
    ReportsSchema
):
    workspace_id: uuid.UUID

    report: ReportKey

    scope: ReportScope

    generated_at: datetime

    parameters: (
        ReportParametersResponse
    )

    data: dict


__all__ = [
    "ReportScope",
    "ReportFormat",
    "ReportKey",
    "ReportsSchema",
    "ReportDefinitionResponse",
    "ReportCatalogResponse",
    "ReportsCapabilitiesResponse",
    "ReportRunRequest",
    "ReportParametersResponse",
    "ReportRunResponse",
]