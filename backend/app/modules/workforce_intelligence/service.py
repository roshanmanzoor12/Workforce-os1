from __future__ import annotations

from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.exceptions import (
    ValidationError,
)
from app.modules.workforce_intelligence.access import (
    WorkforceIntelligenceAccess,
)
from app.modules.workforce_intelligence.calculations import (
    safe_ratio_average,
)
from app.modules.workforce_intelligence.enums import (
    IntelligenceSignalCode,
    IntelligenceSignalSeverity,
)
from app.modules.workforce_intelligence.repository import (
    WorkforceIntelligenceRepository,
)
from app.modules.workforce_intelligence.schemas import (
    EmployeeIntelligenceResponse,
    EmployeeIntelligenceSnapshot,
    IntelligenceCapabilitiesResponse,
    IntelligenceWindow,
    WorkforceOverview,
    WorkforceSignal,
    WorkforceSignalResponse,
    WorkforceTrendPoint,
    WorkforceTrendResponse,
)


class WorkforceIntelligenceService:
    MAX_DAYS = 366

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            WorkforceIntelligenceRepository(
                session
            )
        )

    # =====================================================
    # WINDOW
    # =====================================================

    @classmethod
    def resolve_window(
        cls,
        *,
        days: int,
    ) -> IntelligenceWindow:
        if days < 1:
            raise ValidationError(
                "days must be at least 1."
            )

        if days > cls.MAX_DAYS:
            raise ValidationError(
                "days cannot exceed 366."
            )

        end_date = (
            datetime.now(
                timezone.utc
            ).date()
        )

        start_date = (
            end_date
            - timedelta(
                days=(
                    days - 1
                )
            )
        )

        return IntelligenceWindow(
            start_date=start_date,
            end_date=end_date,
            days=days,
        )

    # =====================================================
    # OVERVIEW
    # =====================================================

    async def overview(
        self,
        *,
        access: WorkforceIntelligenceAccess,
        days: int,
    ) -> WorkforceOverview:
        window = self.resolve_window(
            days=days
        )

        employees = await (
            self.repository.employees(
                access=access
            )
        )

        attendance = await (
            self.repository
            .attendance_summary(
                access=access,
                start_date=(
                    window.start_date
                ),
                end_date=(
                    window.end_date
                ),
            )
        )

        goals = await (
            self.repository
            .goal_summary(
                access=access
            )
        )

        return WorkforceOverview(
            scope=access.scope,

            window=window,

            employee_count=len(
                employees
            ),

            attendance_record_count=(
                attendance
                .record_count
            ),

            attendance_days=(
                attendance
                .attendance_days
            ),

            absence_record_count=(
                attendance
                .absence_record_count
            ),

            total_worked_minutes=(
                attendance
                .total_worked_minutes
            ),

            average_worked_minutes=(
                safe_ratio_average(
                    total=(
                        attendance
                        .total_worked_minutes
                    ),
                    count=(
                        attendance
                        .record_count
                    ),
                )
            ),

            total_break_minutes=(
                attendance
                .total_break_minutes
            ),

            goal_count=(
                goals.goal_count
            ),

            active_goal_count=(
                goals.active_count
            ),

            completed_goal_count=(
                goals.completed_count
            ),

            cancelled_goal_count=(
                goals.cancelled_count
            ),

            archived_goal_count=(
                goals.archived_count
            ),

            average_goal_progress_percent=(
                safe_ratio_average(
                    total=(
                        goals
                        .progress_total
                    ),
                    count=(
                        goals
                        .goal_count
                    ),
                )
            ),
        )

    # =====================================================
    # EMPLOYEE SNAPSHOTS
    # =====================================================

    async def employees(
        self,
        *,
        access: WorkforceIntelligenceAccess,
        days: int,
        limit: int,
    ) -> EmployeeIntelligenceResponse:
        window = self.resolve_window(
            days=days
        )

        employees = await (
            self.repository.employees(
                access=access
            )
        )

        attendance = await (
            self.repository
            .employee_attendance(
                access=access,
                start_date=(
                    window.start_date
                ),
                end_date=(
                    window.end_date
                ),
            )
        )

        goals = await (
            self.repository
            .employee_goals(
                access=access
            )
        )

        items: list[
            EmployeeIntelligenceSnapshot
        ] = []

        for employee in employees:
            attendance_row = (
                attendance.get(
                    employee.id
                )
            )

            goal_row = goals.get(
                employee.id
            )

            record_count = (
                attendance_row
                .record_count
                if attendance_row
                is not None
                else 0
            )

            worked_minutes = (
                attendance_row
                .total_worked_minutes
                if attendance_row
                is not None
                else 0
            )

            goal_count = (
                goal_row.goal_count
                if goal_row
                is not None
                else 0
            )

            progress_total = (
                goal_row.progress_total
                if goal_row
                is not None
                else 0.0
            )

            name = (
                (
                    employee.first_name
                    + " "
                    + employee.last_name
                )
                .strip()
            )

            items.append(
                EmployeeIntelligenceSnapshot(
                    employee_id=(
                        employee.id
                    ),

                    name=(
                        name
                        or str(
                            employee.id
                        )
                    ),

                    attendance_record_count=(
                        record_count
                    ),

                    absence_record_count=(
                        attendance_row
                        .absence_count
                        if attendance_row
                        is not None
                        else 0
                    ),

                    total_worked_minutes=(
                        worked_minutes
                    ),

                    average_worked_minutes=(
                        safe_ratio_average(
                            total=(
                                worked_minutes
                            ),
                            count=(
                                record_count
                            ),
                        )
                    ),

                    goal_count=(
                        goal_count
                    ),

                    active_goal_count=(
                        goal_row
                        .active_count
                        if goal_row
                        is not None
                        else 0
                    ),

                    completed_goal_count=(
                        goal_row
                        .completed_count
                        if goal_row
                        is not None
                        else 0
                    ),

                    average_goal_progress_percent=(
                        safe_ratio_average(
                            total=(
                                progress_total
                            ),
                            count=(
                                goal_count
                            ),
                        )
                    ),
                )
            )

        # Deterministic alphabetical ordering only.
        #
        # Never rank employees by productivity metrics.
        items.sort(
            key=lambda item: (
                item.name.casefold(),
                str(
                    item.employee_id
                ),
            )
        )

        items = items[
            :limit
        ]

        return EmployeeIntelligenceResponse(
            scope=access.scope,
            window=window,
            items=items,
            total=len(
                employees
            ),
        )

    # =====================================================
    # TRENDS
    # =====================================================

    async def trends(
        self,
        *,
        access: WorkforceIntelligenceAccess,
        days: int,
    ) -> WorkforceTrendResponse:
        window = self.resolve_window(
            days=days
        )

        attendance_rows = await (
            self.repository
            .attendance_trends(
                access=access,
                start_date=(
                    window.start_date
                ),
                end_date=(
                    window.end_date
                ),
            )
        )

        goal_rows = await (
            self.repository.goal_trends(
                access=access,
                start_date=(
                    window.start_date
                ),
                end_date=(
                    window.end_date
                    + timedelta(
                        days=1
                    )
                ),
            )
        )

        attendance_by_date = {
            row.day: row
            for row
            in attendance_rows
        }

        goals_by_date = {
            row.day: row
            for row
            in goal_rows
        }

        items: list[
            WorkforceTrendPoint
        ] = []

        current = (
            window.start_date
        )

        while (
            current
            <= window.end_date
        ):
            attendance = (
                attendance_by_date
                .get(
                    current
                )
            )

            goals = (
                goals_by_date.get(
                    current
                )
            )

            records = (
                attendance
                .record_count
                if attendance
                is not None
                else 0
            )

            worked = (
                attendance
                .total_worked_minutes
                if attendance
                is not None
                else 0
            )

            items.append(
                WorkforceTrendPoint(
                    date=current,

                    attendance_record_count=(
                        records
                    ),

                    absence_record_count=(
                        attendance
                        .absence_count
                        if attendance
                        is not None
                        else 0
                    ),

                    total_worked_minutes=(
                        worked
                    ),

                    average_worked_minutes=(
                        safe_ratio_average(
                            total=worked,
                            count=records,
                        )
                    ),

                    goals_created=(
                        goals
                        .created_count
                        if goals
                        is not None
                        else 0
                    ),
                )
            )

            current += timedelta(
                days=1
            )

        return WorkforceTrendResponse(
            scope=access.scope,
            window=window,
            items=items,
        )

    # =====================================================
    # DESCRIPTIVE SIGNALS
    # =====================================================

    async def signals(
        self,
        *,
        access: WorkforceIntelligenceAccess,
        days: int,
    ) -> WorkforceSignalResponse:
        window = self.resolve_window(
            days=days
        )

        employees = await (
            self.repository.employees(
                access=access
            )
        )

        attendance = await (
            self.repository
            .employee_attendance(
                access=access,
                start_date=(
                    window.start_date
                ),
                end_date=(
                    window.end_date
                ),
            )
        )

        goals = await (
            self.repository
            .employee_goals(
                access=access
            )
        )

        items: list[
            WorkforceSignal
        ] = []

        for employee in employees:
            name = (
                (
                    employee.first_name
                    + " "
                    + employee.last_name
                )
                .strip()
            )

            display_name = (
                name
                or str(
                    employee.id
                )
            )

            attendance_row = (
                attendance.get(
                    employee.id
                )
            )

            goal_row = goals.get(
                employee.id
            )

            if attendance_row is None:
                items.append(
                    WorkforceSignal(
                        code=(
                            IntelligenceSignalCode
                            .NO_ATTENDANCE
                        ),

                        severity=(
                            IntelligenceSignalSeverity
                            .INFO
                        ),

                        employee_id=(
                            employee.id
                        ),

                        employee_name=(
                            display_name
                        ),

                        title=(
                            "No attendance records"
                        ),

                        detail=(
                            "No attendance record "
                            "exists for this employee "
                            "inside the selected window."
                        ),

                        data={
                            "days": (
                                window.days
                            ),
                        },
                    )
                )

            elif (
                attendance_row
                .absence_count
                > 0
            ):
                items.append(
                    WorkforceSignal(
                        code=(
                            IntelligenceSignalCode
                            .ABSENCE_RECORDED
                        ),

                        severity=(
                            IntelligenceSignalSeverity
                            .INFO
                        ),

                        employee_id=(
                            employee.id
                        ),

                        employee_name=(
                            display_name
                        ),

                        title=(
                            "Absence records present"
                        ),

                        detail=(
                            "One or more attendance "
                            "records use an absence "
                            "status in the selected "
                            "window."
                        ),

                        data={
                            "absence_records": (
                                attendance_row
                                .absence_count
                            ),
                        },
                    )
                )

            if (
                goal_row is not None
                and goal_row.active_count
                > 0
            ):
                items.append(
                    WorkforceSignal(
                        code=(
                            IntelligenceSignalCode
                            .OPEN_GOALS
                        ),

                        severity=(
                            IntelligenceSignalSeverity
                            .INFO
                        ),

                        employee_id=(
                            employee.id
                        ),

                        employee_name=(
                            display_name
                        ),

                        title=(
                            "Active goals present"
                        ),

                        detail=(
                            "Employee currently has "
                            "active goals."
                        ),

                        data={
                            "active_goals": (
                                goal_row
                                .active_count
                            ),
                        },
                    )
                )

            if (
                goal_row is not None
                and goal_row.goal_count
                > 0
            ):
                average_progress = (
                    safe_ratio_average(
                        total=(
                            goal_row
                            .progress_total
                        ),
                        count=(
                            goal_row
                            .goal_count
                        ),
                    )
                )

                if average_progress < 25:
                    items.append(
                        WorkforceSignal(
                            code=(
                                IntelligenceSignalCode
                                .LOW_GOAL_PROGRESS
                            ),

                            severity=(
                                IntelligenceSignalSeverity
                                .INFO
                            ),

                            employee_id=(
                                employee.id
                            ),

                            employee_name=(
                                display_name
                            ),

                            title=(
                                "Goal progress below 25%"
                            ),

                            detail=(
                                "Average recorded goal "
                                "progress is below 25%. "
                                "This is descriptive only "
                                "and is not a productivity "
                                "rating."
                            ),

                            data={
                                "average_progress_percent": (
                                    average_progress
                                ),
                            },
                        )
                    )

        items.sort(
            key=lambda item: (
                (
                    item.employee_name
                    or ""
                ).casefold(),

                item.code.value,
            )
        )

        return WorkforceSignalResponse(
            scope=access.scope,
            window=window,
            items=items,
            total=len(
                items
            ),
        )

    # =====================================================
    # CAPABILITIES
    # =====================================================

    @staticmethod
    def capabilities(
        *,
        access: WorkforceIntelligenceAccess,
    ) -> IntelligenceCapabilitiesResponse:
        return (
            IntelligenceCapabilitiesResponse(
                scope=access.scope,

                descriptive_metrics_only=True,

                arbitrary_productivity_score=False,

                employee_ranking=False,

                hidden_monitoring=False,

                supports_overview=True,

                supports_employee_snapshots=True,

                supports_trends=True,

                supports_signals=True,

                max_window_days=366,
            )
        )


__all__ = [
    "WorkforceIntelligenceService",
]