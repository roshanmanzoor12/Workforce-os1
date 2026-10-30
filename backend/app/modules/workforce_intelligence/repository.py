from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.attendance.models import (
    AttendanceRecord,
)
from app.modules.employees.models import (
    Employee,
)
from app.modules.goals.models import (
    Goal,
)
from app.modules.workforce_intelligence.access import (
    WorkforceIntelligenceAccess,
)


@dataclass(
    frozen=True,
    slots=True,
)
class AttendanceAggregate:
    record_count: int

    attendance_days: int

    total_worked_minutes: int

    total_break_minutes: int

    absence_record_count: int


@dataclass(
    frozen=True,
    slots=True,
)
class GoalAggregate:
    goal_count: int

    active_count: int

    completed_count: int

    cancelled_count: int

    archived_count: int

    progress_total: float


@dataclass(
    frozen=True,
    slots=True,
)
class EmployeeRow:
    id: uuid.UUID

    first_name: str

    last_name: str


@dataclass(
    frozen=True,
    slots=True,
)
class EmployeeAttendanceAggregate:
    employee_id: uuid.UUID

    record_count: int

    absence_count: int

    total_worked_minutes: int


@dataclass(
    frozen=True,
    slots=True,
)
class EmployeeGoalAggregate:
    employee_id: uuid.UUID

    goal_count: int

    active_count: int

    completed_count: int

    progress_total: float


@dataclass(
    frozen=True,
    slots=True,
)
class AttendanceTrendAggregate:
    day: date

    record_count: int

    absence_count: int

    total_worked_minutes: int


@dataclass(
    frozen=True,
    slots=True,
)
class GoalTrendAggregate:
    day: date

    created_count: int


class WorkforceIntelligenceRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    @staticmethod
    def _scope(
        statement,
        *,
        column,
        access: WorkforceIntelligenceAccess,
    ):
        if access.employee_ids is None:
            return statement

        if not access.employee_ids:
            return statement.where(
                column.in_(
                    []
                )
            )

        return statement.where(
            column.in_(
                tuple(
                    access.employee_ids
                )
            )
        )

    # =====================================================
    # EMPLOYEES
    # =====================================================

    async def employees(
        self,
        *,
        access: WorkforceIntelligenceAccess,
    ) -> list[
        EmployeeRow
    ]:
        statement = (
            select(
                Employee.id,
                Employee.first_name,
                Employee.last_name,
            )
            .where(
                Employee.is_active.is_(
                    True
                )
            )
            .order_by(
                Employee.first_name.asc(),
                Employee.last_name.asc(),
                Employee.id.asc(),
            )
        )

        statement = self._scope(
            statement,
            column=Employee.id,
            access=access,
        )

        result = await self.session.execute(
            statement
        )

        return [
            EmployeeRow(
                id=row.id,
                first_name=(
                    row.first_name
                    or ""
                ),
                last_name=(
                    row.last_name
                    or ""
                ),
            )
            for row
            in result.all()
        ]

    # =====================================================
    # WORKSPACE/SCOPE ATTENDANCE
    # =====================================================

    async def attendance_summary(
        self,
        *,
        access: WorkforceIntelligenceAccess,
        start_date: date,
        end_date: date,
    ) -> AttendanceAggregate:
        statement = select(
            AttendanceRecord.employee_id,
            AttendanceRecord.attendance_date,
            AttendanceRecord.status,
            AttendanceRecord.worked_minutes,
            AttendanceRecord.break_minutes,
        ).where(
            AttendanceRecord.attendance_date
            >= start_date,

            AttendanceRecord.attendance_date
            <= end_date,
        )

        statement = self._scope(
            statement,
            column=(
                AttendanceRecord.employee_id
            ),
            access=access,
        )

        result = await self.session.execute(
            statement
        )

        rows = result.all()

        absence_count = 0

        total_worked = 0

        total_break = 0

        unique_days: set[
            date
        ] = set()

        for row in rows:
            status = (
                row.status
                or ""
            ).strip().casefold()

            if status in {
                "absent",
                "absence",
                "missed",
            }:
                absence_count += 1

            total_worked += int(
                row.worked_minutes
                or 0
            )

            total_break += int(
                row.break_minutes
                or 0
            )

            unique_days.add(
                row.attendance_date
            )

        return AttendanceAggregate(
            record_count=len(
                rows
            ),

            attendance_days=len(
                unique_days
            ),

            total_worked_minutes=(
                total_worked
            ),

            total_break_minutes=(
                total_break
            ),

            absence_record_count=(
                absence_count
            ),
        )

    # =====================================================
    # GOAL SUMMARY
    # =====================================================

    async def goal_summary(
        self,
        *,
        access: WorkforceIntelligenceAccess,
    ) -> GoalAggregate:
        statement = select(
            Goal.status,
            Goal.progress_percent,
        )

        statement = self._scope(
            statement,
            column=(
                Goal.owner_employee_id
            ),
            access=access,
        )

        result = await self.session.execute(
            statement
        )

        rows = result.all()

        active = 0
        completed = 0
        cancelled = 0
        archived = 0
        progress_total = 0.0

        for row in rows:
            status = (
                row.status
                or ""
            ).strip().casefold()

            if status == "active":
                active += 1

            elif status == "completed":
                completed += 1

            elif status in {
                "cancelled",
                "canceled",
            }:
                cancelled += 1

            elif status == "archived":
                archived += 1

            progress_total += float(
                row.progress_percent
                or 0
            )

        return GoalAggregate(
            goal_count=len(
                rows
            ),

            active_count=active,

            completed_count=completed,

            cancelled_count=cancelled,

            archived_count=archived,

            progress_total=(
                progress_total
            ),
        )

    # =====================================================
    # PER-EMPLOYEE ATTENDANCE
    # =====================================================

    async def employee_attendance(
        self,
        *,
        access: WorkforceIntelligenceAccess,
        start_date: date,
        end_date: date,
    ) -> dict[
        uuid.UUID,
        EmployeeAttendanceAggregate,
    ]:
        statement = select(
            AttendanceRecord.employee_id,
            AttendanceRecord.status,
            AttendanceRecord.worked_minutes,
        ).where(
            AttendanceRecord.attendance_date
            >= start_date,

            AttendanceRecord.attendance_date
            <= end_date,
        )

        statement = self._scope(
            statement,
            column=(
                AttendanceRecord.employee_id
            ),
            access=access,
        )

        result = await self.session.execute(
            statement
        )

        accumulator: dict[
            uuid.UUID,
            dict[str, int],
        ] = {}

        for row in result.all():
            current = accumulator.setdefault(
                row.employee_id,
                {
                    "records": 0,
                    "absence": 0,
                    "worked": 0,
                },
            )

            current[
                "records"
            ] += 1

            status = (
                row.status
                or ""
            ).strip().casefold()

            if status in {
                "absent",
                "absence",
                "missed",
            }:
                current[
                    "absence"
                ] += 1

            current[
                "worked"
            ] += int(
                row.worked_minutes
                or 0
            )

        return {
            employee_id: (
                EmployeeAttendanceAggregate(
                    employee_id=(
                        employee_id
                    ),

                    record_count=(
                        values[
                            "records"
                        ]
                    ),

                    absence_count=(
                        values[
                            "absence"
                        ]
                    ),

                    total_worked_minutes=(
                        values[
                            "worked"
                        ]
                    ),
                )
            )
            for (
                employee_id,
                values,
            )
            in accumulator.items()
        }

    # =====================================================
    # PER-EMPLOYEE GOALS
    # =====================================================

    async def employee_goals(
        self,
        *,
        access: WorkforceIntelligenceAccess,
    ) -> dict[
        uuid.UUID,
        EmployeeGoalAggregate,
    ]:
        statement = select(
            Goal.owner_employee_id,
            Goal.status,
            Goal.progress_percent,
        )

        statement = self._scope(
            statement,
            column=(
                Goal.owner_employee_id
            ),
            access=access,
        )

        result = await self.session.execute(
            statement
        )

        accumulator: dict[
            uuid.UUID,
            dict[str, float],
        ] = {}

        for row in result.all():
            if (
                row.owner_employee_id
                is None
            ):
                continue

            current = accumulator.setdefault(
                row.owner_employee_id,
                {
                    "count": 0.0,
                    "active": 0.0,
                    "completed": 0.0,
                    "progress": 0.0,
                },
            )

            current[
                "count"
            ] += 1

            status = (
                row.status
                or ""
            ).strip().casefold()

            if status == "active":
                current[
                    "active"
                ] += 1

            if status == "completed":
                current[
                    "completed"
                ] += 1

            current[
                "progress"
            ] += float(
                row.progress_percent
                or 0
            )

        return {
            employee_id: (
                EmployeeGoalAggregate(
                    employee_id=(
                        employee_id
                    ),

                    goal_count=int(
                        values[
                            "count"
                        ]
                    ),

                    active_count=int(
                        values[
                            "active"
                        ]
                    ),

                    completed_count=int(
                        values[
                            "completed"
                        ]
                    ),

                    progress_total=float(
                        values[
                            "progress"
                        ]
                    ),
                )
            )
            for (
                employee_id,
                values,
            )
            in accumulator.items()
        }

    # =====================================================
    # TRENDS
    # =====================================================

    async def attendance_trends(
        self,
        *,
        access: WorkforceIntelligenceAccess,
        start_date: date,
        end_date: date,
    ) -> list[
        AttendanceTrendAggregate
    ]:
        statement = select(
            AttendanceRecord.attendance_date,
            AttendanceRecord.status,
            AttendanceRecord.worked_minutes,
        ).where(
            AttendanceRecord.attendance_date
            >= start_date,

            AttendanceRecord.attendance_date
            <= end_date,
        )

        statement = self._scope(
            statement,
            column=(
                AttendanceRecord.employee_id
            ),
            access=access,
        )

        result = await self.session.execute(
            statement
        )

        grouped: dict[
            date,
            dict[str, int],
        ] = {}

        for row in result.all():
            current = grouped.setdefault(
                row.attendance_date,
                {
                    "records": 0,
                    "absence": 0,
                    "worked": 0,
                },
            )

            current[
                "records"
            ] += 1

            current[
                "worked"
            ] += int(
                row.worked_minutes
                or 0
            )

            status = (
                row.status
                or ""
            ).strip().casefold()

            if status in {
                "absent",
                "absence",
                "missed",
            }:
                current[
                    "absence"
                ] += 1

        return [
            AttendanceTrendAggregate(
                day=day,

                record_count=(
                    values[
                        "records"
                    ]
                ),

                absence_count=(
                    values[
                        "absence"
                    ]
                ),

                total_worked_minutes=(
                    values[
                        "worked"
                    ]
                ),
            )
            for (
                day,
                values,
            )
            in sorted(
                grouped.items()
            )
        ]

    async def goal_trends(
        self,
        *,
        access: WorkforceIntelligenceAccess,
        start_date: date,
        end_date: date,
    ) -> list[
        GoalTrendAggregate
    ]:
        statement = select(
            func.date(
                Goal.created_at
            ).label(
                "day"
            ),

            func.count(
                Goal.id
            ).label(
                "created_count"
            ),
        ).where(
            Goal.created_at
            >= start_date,

            Goal.created_at
            < (
                end_date
            ),
        )

        statement = self._scope(
            statement,
            column=(
                Goal.owner_employee_id
            ),
            access=access,
        )

        statement = (
            statement
            .group_by(
                func.date(
                    Goal.created_at
                )
            )
            .order_by(
                func.date(
                    Goal.created_at
                )
            )
        )

        result = await self.session.execute(
            statement
        )

        return [
            GoalTrendAggregate(
                day=row.day,
                created_count=int(
                    row.created_count
                    or 0
                ),
            )
            for row
            in result.all()
        ]


__all__ = [
    "AttendanceAggregate",
    "GoalAggregate",
    "EmployeeRow",
    "EmployeeAttendanceAggregate",
    "EmployeeGoalAggregate",
    "AttendanceTrendAggregate",
    "GoalTrendAggregate",
    "WorkforceIntelligenceRepository",
]