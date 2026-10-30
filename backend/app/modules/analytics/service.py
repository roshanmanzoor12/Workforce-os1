from __future__ import annotations

import uuid
from datetime import (
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
from app.modules.analytics.access import (
    AnalyticsAccess,
)
from app.modules.analytics.repository import (
    AnalyticsRepository,
)
from app.modules.analytics.schemas import (
    AnalyticsActivityResponse,
    AnalyticsAppsResponse,
    AnalyticsAttendanceResponse,
    AnalyticsGoalsResponse,
    AnalyticsNamedUsage,
    AnalyticsOverviewResponse,
    AnalyticsProductivityResponse,
    AnalyticsSeriesPoint,
    AnalyticsTrendsResponse,
    AnalyticsTrendSeries,
    AnalyticsWebsitesResponse,
    AnalyticsWindow,
)


class AnalyticsService:
    MAX_RANGE_DAYS = 366

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            AnalyticsRepository(
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
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> AnalyticsWindow:
        resolved_end = (
            end_at
            or datetime.now(
                timezone.utc
            )
        )

        if resolved_end.tzinfo is None:
            resolved_end = (
                resolved_end.replace(
                    tzinfo=timezone.utc
                )
            )

        resolved_start = (
            start_at
            or (
                resolved_end
                - timedelta(
                    days=7
                )
            )
        )

        if resolved_start.tzinfo is None:
            resolved_start = (
                resolved_start.replace(
                    tzinfo=timezone.utc
                )
            )

        if resolved_start >= resolved_end:
            raise ValidationError(
                "start_at must be earlier "
                "than end_at."
            )

        if (
            resolved_end
            - resolved_start
            > timedelta(
                days=cls.MAX_RANGE_DAYS
            )
        ):
            raise ValidationError(
                "Analytics date range cannot "
                "exceed 366 days."
            )

        return AnalyticsWindow(
            start_at=resolved_start,
            end_at=resolved_end,
        )

    @staticmethod
    def _scope(
        access: AnalyticsAccess,
    ) -> str:
        return access.scope.value

    # =====================================================
    # OVERVIEW
    # =====================================================

    async def overview(
        self,
        *,
        workspace_id: uuid.UUID,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> AnalyticsOverviewResponse:
        employees = await (
            self.repository.employee_count(
                access
            )
        )

        activity = await (
            self.repository.activity_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        attendance = await (
            self.repository.attendance_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        apps = await (
            self.repository.app_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        websites = await (
            self.repository.website_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        goals = await (
            self.repository.goal_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        return AnalyticsOverviewResponse(
            workspace_id=workspace_id,
            scope=self._scope(
                access
            ),
            window=window,

            employees=employees,

            activity_events=int(
                activity["total"]
            ),
            active_events=int(
                activity["active"]
            ),
            idle_events=int(
                activity["idle"]
            ),

            attendance_records=int(
                attendance["total"]
            ),
            worked_minutes=int(
                attendance[
                    "worked_minutes"
                ]
            ),

            app_intervals=int(
                apps[
                    "total_intervals"
                ]
            ),
            app_seconds=int(
                apps[
                    "total_seconds"
                ]
            ),

            website_intervals=int(
                websites[
                    "total_intervals"
                ]
            ),
            website_seconds=int(
                websites[
                    "total_seconds"
                ]
            ),

            goals_total=int(
                goals["total"]
            ),
            goals_completed=int(
                goals["completed"]
            ),
            goals_average_progress=float(
                goals[
                    "average_progress"
                ]
            ),
        )

    # =====================================================
    # ACTIVITY
    # =====================================================

    async def activity(
        self,
        *,
        workspace_id: uuid.UUID,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> AnalyticsActivityResponse:
        summary = await (
            self.repository.activity_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        daily = await (
            self.repository.activity_daily(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        return AnalyticsActivityResponse(
            workspace_id=workspace_id,
            scope=self._scope(
                access
            ),
            window=window,
            total_events=int(
                summary["total"]
            ),
            active_events=int(
                summary["active"]
            ),
            idle_events=int(
                summary["idle"]
            ),
            average_idle_seconds=float(
                summary[
                    "average_idle_seconds"
                ]
            ),
            daily=[
                AnalyticsSeriesPoint(
                    date=day,
                    value=float(
                        value
                    ),
                )
                for (
                    day,
                    value,
                ) in daily
            ],
        )

    # =====================================================
    # ATTENDANCE
    # =====================================================

    async def attendance(
        self,
        *,
        workspace_id: uuid.UUID,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> AnalyticsAttendanceResponse:
        summary = await (
            self.repository
            .attendance_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        daily = await (
            self.repository
            .attendance_daily(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        return AnalyticsAttendanceResponse(
            workspace_id=workspace_id,
            scope=self._scope(
                access
            ),
            window=window,

            total_records=int(
                summary["total"]
            ),

            worked_minutes=int(
                summary[
                    "worked_minutes"
                ]
            ),

            break_minutes=int(
                summary[
                    "break_minutes"
                ]
            ),

            status_breakdown=dict(
                summary[
                    "status_breakdown"
                ]
            ),

            daily=[
                AnalyticsSeriesPoint(
                    date=day,
                    value=float(
                        value
                    ),
                )
                for (
                    day,
                    value,
                ) in daily
            ],
        )

    # =====================================================
    # APPS
    # =====================================================

    async def apps(
        self,
        *,
        workspace_id: uuid.UUID,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> AnalyticsAppsResponse:
        summary = await (
            self.repository.app_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        return AnalyticsAppsResponse(
            workspace_id=workspace_id,
            scope=self._scope(
                access
            ),
            window=window,

            total_intervals=int(
                summary[
                    "total_intervals"
                ]
            ),

            total_seconds=int(
                summary[
                    "total_seconds"
                ]
            ),

            top_apps=[
                AnalyticsNamedUsage(
                    name=str(
                        item["name"]
                    ),
                    duration_seconds=int(
                        item[
                            "duration_seconds"
                        ]
                    ),
                    event_count=int(
                        item[
                            "event_count"
                        ]
                    ),
                )
                for item
                in summary["items"]
            ],
        )

    # =====================================================
    # WEBSITES
    # =====================================================

    async def websites(
        self,
        *,
        workspace_id: uuid.UUID,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> AnalyticsWebsitesResponse:
        summary = await (
            self.repository
            .website_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        return AnalyticsWebsitesResponse(
            workspace_id=workspace_id,
            scope=self._scope(
                access
            ),
            window=window,

            total_intervals=int(
                summary[
                    "total_intervals"
                ]
            ),

            total_seconds=int(
                summary[
                    "total_seconds"
                ]
            ),

            top_websites=[
                AnalyticsNamedUsage(
                    name=str(
                        item["name"]
                    ),
                    duration_seconds=int(
                        item[
                            "duration_seconds"
                        ]
                    ),
                    event_count=int(
                        item[
                            "event_count"
                        ]
                    ),
                )
                for item
                in summary["items"]
            ],
        )

    # =====================================================
    # GOALS
    # =====================================================

    async def goals(
        self,
        *,
        workspace_id: uuid.UUID,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> AnalyticsGoalsResponse:
        summary = await (
            self.repository.goal_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        return AnalyticsGoalsResponse(
            workspace_id=workspace_id,
            scope=self._scope(
                access
            ),
            window=window,

            total=int(
                summary["total"]
            ),

            active=int(
                summary["active"]
            ),

            completed=int(
                summary["completed"]
            ),

            cancelled=int(
                summary["cancelled"]
            ),

            archived=int(
                summary["archived"]
            ),

            average_progress=float(
                summary[
                    "average_progress"
                ]
            ),
        )

    # =====================================================
    # PRODUCTIVITY
    # =====================================================

    async def productivity(
        self,
        *,
        workspace_id: uuid.UUID,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> AnalyticsProductivityResponse:
        activity = await (
            self.repository.activity_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        attendance = await (
            self.repository.attendance_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        apps = await (
            self.repository.app_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        websites = await (
            self.repository.website_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        goals = await (
            self.repository.goal_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        # No arbitrary "productivity score" here.
        #
        # Phase 12.5 Productivity Insights will own
        # derived interpretation/scoring policy.

        return AnalyticsProductivityResponse(
            workspace_id=workspace_id,
            scope=self._scope(
                access
            ),
            window=window,

            activity_events=int(
                activity["total"]
            ),

            active_events=int(
                activity["active"]
            ),

            idle_events=int(
                activity["idle"]
            ),

            app_seconds=int(
                apps[
                    "total_seconds"
                ]
            ),

            website_seconds=int(
                websites[
                    "total_seconds"
                ]
            ),

            worked_minutes=int(
                attendance[
                    "worked_minutes"
                ]
            ),

            goals_total=int(
                goals["total"]
            ),

            goals_completed=int(
                goals["completed"]
            ),

            goals_average_progress=float(
                goals[
                    "average_progress"
                ]
            ),
        )

    # =====================================================
    # TRENDS
    # =====================================================

    async def trends(
        self,
        *,
        workspace_id: uuid.UUID,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> AnalyticsTrendsResponse:
        # Deliberately sequential.
        #
        # Never asyncio.gather() multiple queries using
        # the same AsyncSession.

        activity = await (
            self.repository.activity_daily(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        attendance = await (
            self.repository.attendance_daily(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        apps = await (
            self.repository.app_daily(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        websites = await (
            self.repository.website_daily(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        goals = await (
            self.repository.goals_daily(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        def points(
            rows: list[
                tuple[
                    object,
                    int,
                ]
            ],
        ) -> list[
            AnalyticsSeriesPoint
        ]:
            return [
                AnalyticsSeriesPoint(
                    date=day,
                    value=float(
                        value
                    ),
                )
                for (
                    day,
                    value,
                ) in rows
            ]

        return AnalyticsTrendsResponse(
            workspace_id=workspace_id,
            scope=self._scope(
                access
            ),
            window=window,
            series=[
                AnalyticsTrendSeries(
                    key="activity_events",
                    points=points(
                        activity
                    ),
                ),
                AnalyticsTrendSeries(
                    key="attendance_records",
                    points=points(
                        attendance
                    ),
                ),
                AnalyticsTrendSeries(
                    key="app_seconds",
                    points=points(
                        apps
                    ),
                ),
                AnalyticsTrendSeries(
                    key="website_seconds",
                    points=points(
                        websites
                    ),
                ),
                AnalyticsTrendSeries(
                    key="goals_created",
                    points=points(
                        goals
                    ),
                ),
            ],
        )


__all__ = [
    "AnalyticsService",
]