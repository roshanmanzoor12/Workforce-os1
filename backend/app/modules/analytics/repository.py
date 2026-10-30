from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import (
    date,
    datetime,
    timedelta,
)

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.activity.models import (
    ACTIVITY_STATE_ACTIVE,
    ACTIVITY_STATE_IDLE,
    ActivityStateEvent,
)
from app.modules.analytics.access import (
    AnalyticsAccess,
)
from app.modules.app_tracking.models import (
    AppUsageInterval,
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
from app.modules.website_tracking.models import (
    WebsiteUsageInterval,
)


class AnalyticsRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # SCOPE
    # =====================================================

    @staticmethod
    def _apply_employee_scope(
        statement,
        column,
        access: AnalyticsAccess,
    ):
        if access.employee_ids is None:
            return statement

        if not access.employee_ids:
            return statement.where(
                column.is_(None)
            ).where(
                column.is_not(None)
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

    async def employee_count(
        self,
        access: AnalyticsAccess,
    ) -> int:
        statement = (
            select(
                func.count()
            )
            .select_from(
                Employee
            )
            .where(
                Employee.is_active.is_(
                    True
                )
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                Employee.id,
                access,
            )
        )

        result = await self.session.execute(
            statement
        )

        return int(
            result.scalar_one()
        )

    # =====================================================
    # ACTIVITY
    # =====================================================

    async def activity_summary(
        self,
        *,
        access: AnalyticsAccess,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[str, float]:
        statement = (
            select(
                ActivityStateEvent.state,
                func.count(
                    ActivityStateEvent.id
                ),
                func.avg(
                    ActivityStateEvent
                    .idle_seconds
                ),
            )
            .where(
                ActivityStateEvent.observed_at
                >= start_at,
                ActivityStateEvent.observed_at
                < end_at,
            )
            .group_by(
                ActivityStateEvent.state
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                ActivityStateEvent.employee_id,
                access,
            )
        )

        result = await self.session.execute(
            statement
        )

        total = 0
        active = 0
        idle = 0

        idle_weighted_sum = 0.0
        idle_count = 0

        for (
            state,
            count,
            average_idle,
        ) in result.all():
            count_value = int(
                count
                or 0
            )

            total += count_value

            if state == ACTIVITY_STATE_ACTIVE:
                active += count_value

            elif state == ACTIVITY_STATE_IDLE:
                idle += count_value

                idle_weighted_sum += (
                    float(
                        average_idle
                        or 0
                    )
                    * count_value
                )

                idle_count += count_value

        return {
            "total": total,
            "active": active,
            "idle": idle,
            "average_idle_seconds": (
                idle_weighted_sum
                / idle_count
                if idle_count
                else 0.0
            ),
        }

    async def activity_daily(
        self,
        *,
        access: AnalyticsAccess,
        start_at: datetime,
        end_at: datetime,
    ) -> list[
        tuple[
            date,
            int,
        ]
    ]:
        day = func.date(
            ActivityStateEvent.observed_at
        )

        statement = (
            select(
                day.label(
                    "day"
                ),
                func.count(
                    ActivityStateEvent.id
                ).label(
                    "value"
                ),
            )
            .where(
                ActivityStateEvent.observed_at
                >= start_at,
                ActivityStateEvent.observed_at
                < end_at,
            )
            .group_by(
                day
            )
            .order_by(
                day.asc()
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                ActivityStateEvent.employee_id,
                access,
            )
        )

        result = await self.session.execute(
            statement
        )

        return [
            (
                row.day,
                int(
                    row.value
                    or 0
                ),
            )
            for row in result
        ]

    # =====================================================
    # ATTENDANCE
    # =====================================================

    @staticmethod
    def _attendance_date_range(
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> tuple[
        date,
        date,
    ]:
        start_date = start_at.date()

        # end_at is exclusive.
        #
        # Example:
        # 2026-09-23 00:00 should not include Sep 23.
        inclusive_end = (
            end_at
            - timedelta(
                microseconds=1
            )
        ).date()

        return (
            start_date,
            inclusive_end,
        )

    async def attendance_summary(
        self,
        *,
        access: AnalyticsAccess,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[
        str,
        object,
    ]:
        (
            start_date,
            end_date,
        ) = self._attendance_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        statement = (
            select(
                AttendanceRecord.status,
                func.count(
                    AttendanceRecord.id
                ).label(
                    "count"
                ),
                func.coalesce(
                    func.sum(
                        AttendanceRecord
                        .worked_minutes
                    ),
                    0,
                ).label(
                    "worked"
                ),
                func.coalesce(
                    func.sum(
                        AttendanceRecord
                        .break_minutes
                    ),
                    0,
                ).label(
                    "breaks"
                ),
            )
            .where(
                AttendanceRecord.attendance_date
                >= start_date,
                AttendanceRecord.attendance_date
                <= end_date,
            )
            .group_by(
                AttendanceRecord.status
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                AttendanceRecord.employee_id,
                access,
            )
        )

        result = await self.session.execute(
            statement
        )

        breakdown: dict[
            str,
            int,
        ] = {}

        total = 0
        worked = 0
        breaks = 0

        for row in result:
            count = int(
                row.count
                or 0
            )

            breakdown[
                str(
                    row.status
                )
            ] = count

            total += count

            worked += int(
                row.worked
                or 0
            )

            breaks += int(
                row.breaks
                or 0
            )

        return {
            "total": total,
            "worked_minutes": worked,
            "break_minutes": breaks,
            "status_breakdown": breakdown,
        }

    async def attendance_daily(
        self,
        *,
        access: AnalyticsAccess,
        start_at: datetime,
        end_at: datetime,
    ) -> list[
        tuple[
            date,
            int,
        ]
    ]:
        (
            start_date,
            end_date,
        ) = self._attendance_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        statement = (
            select(
                AttendanceRecord
                .attendance_date
                .label(
                    "day"
                ),
                func.count(
                    AttendanceRecord.id
                ).label(
                    "value"
                ),
            )
            .where(
                AttendanceRecord.attendance_date
                >= start_date,
                AttendanceRecord.attendance_date
                <= end_date,
            )
            .group_by(
                AttendanceRecord
                .attendance_date
            )
            .order_by(
                AttendanceRecord
                .attendance_date
                .asc()
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                AttendanceRecord.employee_id,
                access,
            )
        )

        result = await self.session.execute(
            statement
        )

        return [
            (
                row.day,
                int(
                    row.value
                    or 0
                ),
            )
            for row in result
        ]

    # =====================================================
    # APPLICATIONS
    # =====================================================

    async def app_summary(
        self,
        *,
        access: AnalyticsAccess,
        start_at: datetime,
        end_at: datetime,
        limit: int = 10,
    ) -> dict[
        str,
        object,
    ]:
        base = (
            select(
                AppUsageInterval
                .process_name
                .label(
                    "name"
                ),
                func.count(
                    AppUsageInterval.id
                ).label(
                    "event_count"
                ),
                func.coalesce(
                    func.sum(
                        AppUsageInterval
                        .duration_seconds
                    ),
                    0,
                ).label(
                    "duration_seconds"
                ),
            )
            .where(
                AppUsageInterval.started_at
                >= start_at,
                AppUsageInterval.started_at
                < end_at,
            )
            .group_by(
                AppUsageInterval
                .process_name
            )
            .order_by(
                func.sum(
                    AppUsageInterval
                    .duration_seconds
                ).desc()
            )
            .limit(
                limit
            )
        )

        base = (
            self._apply_employee_scope(
                base,
                AppUsageInterval.employee_id,
                access,
            )
        )

        result = await self.session.execute(
            base
        )

        items = [
            {
                "name": row.name,
                "event_count": int(
                    row.event_count
                    or 0
                ),
                "duration_seconds": int(
                    row.duration_seconds
                    or 0
                ),
            }
            for row in result
        ]

        totals_statement = (
            select(
                func.count(
                    AppUsageInterval.id
                ).label(
                    "total_intervals"
                ),
                func.coalesce(
                    func.sum(
                        AppUsageInterval
                        .duration_seconds
                    ),
                    0,
                ).label(
                    "total_seconds"
                ),
            )
            .where(
                AppUsageInterval.started_at
                >= start_at,
                AppUsageInterval.started_at
                < end_at,
            )
        )

        totals_statement = (
            self._apply_employee_scope(
                totals_statement,
                AppUsageInterval.employee_id,
                access,
            )
        )

        totals_result = (
            await self.session.execute(
                totals_statement
            )
        )

        totals = totals_result.one()

        return {
            "total_intervals": int(
                totals.total_intervals
                or 0
            ),
            "total_seconds": int(
                totals.total_seconds
                or 0
            ),
            "items": items,
        }

    async def app_daily(
        self,
        *,
        access: AnalyticsAccess,
        start_at: datetime,
        end_at: datetime,
    ) -> list[
        tuple[
            date,
            int,
        ]
    ]:
        day = func.date(
            AppUsageInterval.started_at
        )

        statement = (
            select(
                day.label(
                    "day"
                ),
                func.coalesce(
                    func.sum(
                        AppUsageInterval
                        .duration_seconds
                    ),
                    0,
                ).label(
                    "value"
                ),
            )
            .where(
                AppUsageInterval.started_at
                >= start_at,
                AppUsageInterval.started_at
                < end_at,
            )
            .group_by(
                day
            )
            .order_by(
                day.asc()
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                AppUsageInterval.employee_id,
                access,
            )
        )

        result = await self.session.execute(
            statement
        )

        return [
            (
                row.day,
                int(
                    row.value
                    or 0
                ),
            )
            for row in result
        ]

    # =====================================================
    # WEBSITES
    # =====================================================

    async def website_summary(
        self,
        *,
        access: AnalyticsAccess,
        start_at: datetime,
        end_at: datetime,
        limit: int = 10,
    ) -> dict[
        str,
        object,
    ]:
        statement = (
            select(
                WebsiteUsageInterval
                .normalized_domain
                .label(
                    "name"
                ),
                func.count(
                    WebsiteUsageInterval.id
                ).label(
                    "event_count"
                ),
                func.coalesce(
                    func.sum(
                        WebsiteUsageInterval
                        .duration_seconds
                    ),
                    0,
                ).label(
                    "duration_seconds"
                ),
            )
            .where(
                WebsiteUsageInterval.started_at
                >= start_at,
                WebsiteUsageInterval.started_at
                < end_at,
            )
            .group_by(
                WebsiteUsageInterval
                .normalized_domain
            )
            .order_by(
                func.sum(
                    WebsiteUsageInterval
                    .duration_seconds
                ).desc()
            )
            .limit(
                limit
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                WebsiteUsageInterval.employee_id,
                access,
            )
        )

        result = await self.session.execute(
            statement
        )

        items = [
            {
                "name": row.name,
                "event_count": int(
                    row.event_count
                    or 0
                ),
                "duration_seconds": int(
                    row.duration_seconds
                    or 0
                ),
            }
            for row in result
        ]

        totals_statement = (
            select(
                func.count(
                    WebsiteUsageInterval.id
                ).label(
                    "total_intervals"
                ),
                func.coalesce(
                    func.sum(
                        WebsiteUsageInterval
                        .duration_seconds
                    ),
                    0,
                ).label(
                    "total_seconds"
                ),
            )
            .where(
                WebsiteUsageInterval.started_at
                >= start_at,
                WebsiteUsageInterval.started_at
                < end_at,
            )
        )

        totals_statement = (
            self._apply_employee_scope(
                totals_statement,
                WebsiteUsageInterval.employee_id,
                access,
            )
        )

        totals_result = (
            await self.session.execute(
                totals_statement
            )
        )

        totals = totals_result.one()

        return {
            "total_intervals": int(
                totals.total_intervals
                or 0
            ),
            "total_seconds": int(
                totals.total_seconds
                or 0
            ),
            "items": items,
        }

    async def website_daily(
        self,
        *,
        access: AnalyticsAccess,
        start_at: datetime,
        end_at: datetime,
    ) -> list[
        tuple[
            date,
            int,
        ]
    ]:
        day = func.date(
            WebsiteUsageInterval.started_at
        )

        statement = (
            select(
                day.label(
                    "day"
                ),
                func.coalesce(
                    func.sum(
                        WebsiteUsageInterval
                        .duration_seconds
                    ),
                    0,
                ).label(
                    "value"
                ),
            )
            .where(
                WebsiteUsageInterval.started_at
                >= start_at,
                WebsiteUsageInterval.started_at
                < end_at,
            )
            .group_by(
                day
            )
            .order_by(
                day.asc()
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                WebsiteUsageInterval.employee_id,
                access,
            )
        )

        result = await self.session.execute(
            statement
        )

        return [
            (
                row.day,
                int(
                    row.value
                    or 0
                ),
            )
            for row in result
        ]

    # =====================================================
    # GOALS
    # =====================================================

    async def goal_summary(
        self,
        *,
        access: AnalyticsAccess,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[
        str,
        object,
    ]:
        statement = (
            select(
                Goal.status,
                func.count(
                    Goal.id
                ).label(
                    "count"
                ),
                func.coalesce(
                    func.avg(
                        Goal.progress_percent
                    ),
                    0,
                ).label(
                    "average_progress"
                ),
            )
            .where(
                Goal.created_at
                >= start_at,
                Goal.created_at
                < end_at,
            )
            .group_by(
                Goal.status
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                Goal.owner_employee_id,
                access,
            )
        )

        result = await self.session.execute(
            statement
        )

        status_counts: dict[
            str,
            int,
        ] = defaultdict(
            int
        )

        total = 0

        weighted_progress = 0.0

        for row in result:
            count = int(
                row.count
                or 0
            )

            status_counts[
                str(
                    row.status
                )
            ] = count

            total += count

            weighted_progress += (
                float(
                    row.average_progress
                    or 0
                )
                * count
            )

        return {
            "total": total,
            "active": status_counts[
                "active"
            ],
            "completed": status_counts[
                "completed"
            ],
            "cancelled": status_counts[
                "cancelled"
            ],
            "archived": status_counts[
                "archived"
            ],
            "average_progress": (
                weighted_progress
                / total
                if total
                else 0.0
            ),
        }

    async def goals_daily(
        self,
        *,
        access: AnalyticsAccess,
        start_at: datetime,
        end_at: datetime,
    ) -> list[
        tuple[
            date,
            int,
        ]
    ]:
        day = func.date(
            Goal.created_at
        )

        statement = (
            select(
                day.label(
                    "day"
                ),
                func.count(
                    Goal.id
                ).label(
                    "value"
                ),
            )
            .where(
                Goal.created_at
                >= start_at,
                Goal.created_at
                < end_at,
            )
            .group_by(
                day
            )
            .order_by(
                day.asc()
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                Goal.owner_employee_id,
                access,
            )
        )

        result = await self.session.execute(
            statement
        )

        return [
            (
                row.day,
                int(
                    row.value
                    or 0
                ),
            )
            for row in result
        ]


__all__ = [
    "AnalyticsRepository",
]