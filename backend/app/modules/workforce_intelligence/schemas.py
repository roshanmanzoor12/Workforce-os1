from __future__ import annotations

import uuid
from datetime import date

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.workforce_intelligence.enums import (
    IntelligenceScope,
    IntelligenceSignalCode,
    IntelligenceSignalSeverity,
)


class IntelligenceSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )


class IntelligenceWindow(
    IntelligenceSchema
):
    start_date: date

    end_date: date

    days: int = Field(
        ge=1,
        le=366,
    )


class WorkforceOverview(
    IntelligenceSchema
):
    scope: IntelligenceScope

    window: IntelligenceWindow

    employee_count: int = Field(
        ge=0
    )

    attendance_record_count: int = Field(
        ge=0
    )

    attendance_days: int = Field(
        ge=0
    )

    absence_record_count: int = Field(
        ge=0
    )

    total_worked_minutes: int = Field(
        ge=0
    )

    average_worked_minutes: float = Field(
        ge=0
    )

    total_break_minutes: int = Field(
        ge=0
    )

    goal_count: int = Field(
        ge=0
    )

    active_goal_count: int = Field(
        ge=0
    )

    completed_goal_count: int = Field(
        ge=0
    )

    cancelled_goal_count: int = Field(
        ge=0
    )

    archived_goal_count: int = Field(
        ge=0
    )

    average_goal_progress_percent: float = Field(
        ge=0,
        le=100,
    )


class EmployeeIntelligenceSnapshot(
    IntelligenceSchema
):
    employee_id: uuid.UUID

    name: str

    attendance_record_count: int = Field(
        ge=0
    )

    absence_record_count: int = Field(
        ge=0
    )

    total_worked_minutes: int = Field(
        ge=0
    )

    average_worked_minutes: float = Field(
        ge=0
    )

    goal_count: int = Field(
        ge=0
    )

    active_goal_count: int = Field(
        ge=0
    )

    completed_goal_count: int = Field(
        ge=0
    )

    average_goal_progress_percent: float = Field(
        ge=0,
        le=100,
    )


class EmployeeIntelligenceResponse(
    IntelligenceSchema
):
    scope: IntelligenceScope

    window: IntelligenceWindow

    items: list[
        EmployeeIntelligenceSnapshot
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        ge=0
    )


class WorkforceTrendPoint(
    IntelligenceSchema
):
    date: date

    attendance_record_count: int = Field(
        ge=0
    )

    absence_record_count: int = Field(
        ge=0
    )

    total_worked_minutes: int = Field(
        ge=0
    )

    average_worked_minutes: float = Field(
        ge=0
    )

    goals_created: int = Field(
        ge=0
    )


class WorkforceTrendResponse(
    IntelligenceSchema
):
    scope: IntelligenceScope

    window: IntelligenceWindow

    items: list[
        WorkforceTrendPoint
    ] = Field(
        default_factory=list
    )


class WorkforceSignal(
    IntelligenceSchema
):
    code: IntelligenceSignalCode

    severity: IntelligenceSignalSeverity

    employee_id: (
        uuid.UUID
        | None
    ) = None

    employee_name: (
        str
        | None
    ) = None

    title: str

    detail: str

    data: dict = Field(
        default_factory=dict
    )


class WorkforceSignalResponse(
    IntelligenceSchema
):
    scope: IntelligenceScope

    window: IntelligenceWindow

    items: list[
        WorkforceSignal
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        ge=0
    )


class IntelligenceCapabilitiesResponse(
    IntelligenceSchema
):
    scope: IntelligenceScope

    descriptive_metrics_only: bool = True

    arbitrary_productivity_score: bool = False

    employee_ranking: bool = False

    hidden_monitoring: bool = False

    supports_overview: bool = True

    supports_employee_snapshots: bool = True

    supports_trends: bool = True

    supports_signals: bool = True

    max_window_days: int = 366


__all__ = [
    "IntelligenceWindow",
    "WorkforceOverview",
    "EmployeeIntelligenceSnapshot",
    "EmployeeIntelligenceResponse",
    "WorkforceTrendPoint",
    "WorkforceTrendResponse",
    "WorkforceSignal",
    "WorkforceSignalResponse",
    "IntelligenceCapabilitiesResponse",
]