from __future__ import annotations

import uuid
from datetime import (
    datetime,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.analytics.access import (
    AnalyticsAccess,
)
from app.modules.analytics.repository import (
    AnalyticsRepository,
)
from app.modules.analytics.schemas import (
    AnalyticsNamedUsage,
    AnalyticsWindow,
)
from app.modules.analytics.service import (
    AnalyticsService,
)
from app.modules.productivity_insights.calculations import (
    metric_change,
    percentage,
)
from app.modules.productivity_insights.schemas import (
    ProductivityActivityResponse,
    ProductivityComparisonResponse,
    ProductivityGoalsResponse,
    ProductivityMetricComparison,
    ProductivityOverviewResponse,
    ProductivityUsageResponse,
)


class ProductivityInsightsService:
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

    @staticmethod
    def resolve_window(
        *,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> AnalyticsWindow:
        return (
            AnalyticsService
            .resolve_window(
                start_at=start_at,
                end_at=end_at,
            )
        )

    @staticmethod
    def _scope(
        access: AnalyticsAccess,
    ) -> str:
        return access.scope.value

    @staticmethod
    def _previous_window(
        window: AnalyticsWindow,
    ) -> AnalyticsWindow:
        duration = (
            window.end_at
            - window.start_at
        )

        return AnalyticsWindow(
            start_at=(
                window.start_at
                - duration
            ),
            end_at=window.start_at,
        )

    # =====================================================
    # INTERNAL SNAPSHOT
    # =====================================================

    async def _snapshot(
        self,
        *,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> dict[
        str,
        object,
    ]:
        # Deliberately sequential:
        #
        # all calls use the same AsyncSession.

        employees = await (
            self.repository
            .employee_count(
                access
            )
        )

        activity = await (
            self.repository
            .activity_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        attendance = await (
            self.repository
            .attendance_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        apps = await (
            self.repository
            .app_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        websites = await (
            self.repository
            .website_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        goals = await (
            self.repository
            .goal_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        return {
            "employees": employees,
            "activity": activity,
            "attendance": attendance,
            "apps": apps,
            "websites": websites,
            "goals": goals,
        }

    # =====================================================
    # OVERVIEW
    # =====================================================

    async def overview(
        self,
        *,
        workspace_id: uuid.UUID,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> ProductivityOverviewResponse:
        snapshot = await self._snapshot(
            access=access,
            window=window,
        )

        activity = snapshot[
            "activity"
        ]

        attendance = snapshot[
            "attendance"
        ]

        apps = snapshot[
            "apps"
        ]

        websites = snapshot[
            "websites"
        ]

        goals = snapshot[
            "goals"
        ]

        activity_total = int(
            activity["total"]
        )

        goals_total = int(
            goals["total"]
        )

        goals_completed = int(
            goals["completed"]
        )

        return ProductivityOverviewResponse(
            workspace_id=workspace_id,

            scope=self._scope(
                access
            ),

            window=window,

            employee_count=int(
                snapshot["employees"]
            ),

            activity_events=activity_total,

            active_events=int(
                activity["active"]
            ),

            idle_events=int(
                activity["idle"]
            ),

            active_event_percent=percentage(
                activity["active"],
                activity_total,
            ),

            idle_event_percent=percentage(
                activity["idle"],
                activity_total,
            ),

            average_idle_seconds=float(
                activity[
                    "average_idle_seconds"
                ]
            ),

            worked_minutes=int(
                attendance[
                    "worked_minutes"
                ]
            ),

            break_minutes=int(
                attendance[
                    "break_minutes"
                ]
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

            goals_total=goals_total,

            goals_completed=(
                goals_completed
            ),

            goal_completion_percent=(
                percentage(
                    goals_completed,
                    goals_total,
                )
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
    ) -> ProductivityActivityResponse:
        activity = await (
            self.repository
            .activity_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        attendance = await (
            self.repository
            .attendance_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        total = int(
            activity["total"]
        )

        return ProductivityActivityResponse(
            workspace_id=workspace_id,

            scope=self._scope(
                access
            ),

            window=window,

            activity_events=total,

            active_events=int(
                activity["active"]
            ),

            idle_events=int(
                activity["idle"]
            ),

            active_event_percent=percentage(
                activity["active"],
                total,
            ),

            idle_event_percent=percentage(
                activity["idle"],
                total,
            ),

            average_idle_seconds=float(
                activity[
                    "average_idle_seconds"
                ]
            ),

            attendance_records=int(
                attendance["total"]
            ),

            worked_minutes=int(
                attendance[
                    "worked_minutes"
                ]
            ),

            break_minutes=int(
                attendance[
                    "break_minutes"
                ]
            ),
        )

    # =====================================================
    # USAGE
    # =====================================================

    async def usage(
        self,
        *,
        workspace_id: uuid.UUID,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> ProductivityUsageResponse:
        apps = await (
            self.repository
            .app_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        websites = await (
            self.repository
            .website_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        return ProductivityUsageResponse(
            workspace_id=workspace_id,

            scope=self._scope(
                access
            ),

            window=window,

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
                in apps["items"]
            ],

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
                in websites["items"]
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
    ) -> ProductivityGoalsResponse:
        goals = await (
            self.repository
            .goal_summary(
                access=access,
                start_at=window.start_at,
                end_at=window.end_at,
            )
        )

        total = int(
            goals["total"]
        )

        completed = int(
            goals["completed"]
        )

        return ProductivityGoalsResponse(
            workspace_id=workspace_id,

            scope=self._scope(
                access
            ),

            window=window,

            total=total,

            active=int(
                goals["active"]
            ),

            completed=completed,

            cancelled=int(
                goals["cancelled"]
            ),

            archived=int(
                goals["archived"]
            ),

            completion_percent=percentage(
                completed,
                total,
            ),

            average_progress=float(
                goals[
                    "average_progress"
                ]
            ),
        )

    # =====================================================
    # COMPARISON
    # =====================================================

    async def comparison(
        self,
        *,
        workspace_id: uuid.UUID,
        access: AnalyticsAccess,
        window: AnalyticsWindow,
    ) -> ProductivityComparisonResponse:
        previous_window = (
            self._previous_window(
                window
            )
        )

        # Sequential intentionally.
        current = await self._snapshot(
            access=access,
            window=window,
        )

        previous = await self._snapshot(
            access=access,
            window=previous_window,
        )

        current_activity = current[
            "activity"
        ]

        previous_activity = previous[
            "activity"
        ]

        current_attendance = current[
            "attendance"
        ]

        previous_attendance = previous[
            "attendance"
        ]

        current_apps = current[
            "apps"
        ]

        previous_apps = previous[
            "apps"
        ]

        current_websites = current[
            "websites"
        ]

        previous_websites = previous[
            "websites"
        ]

        current_goals = current[
            "goals"
        ]

        previous_goals = previous[
            "goals"
        ]

        metric_values = {
            "activity_events": (
                current_activity["total"],
                previous_activity["total"],
            ),

            "active_events": (
                current_activity["active"],
                previous_activity["active"],
            ),

            "idle_events": (
                current_activity["idle"],
                previous_activity["idle"],
            ),

            "worked_minutes": (
                current_attendance[
                    "worked_minutes"
                ],
                previous_attendance[
                    "worked_minutes"
                ],
            ),

            "break_minutes": (
                current_attendance[
                    "break_minutes"
                ],
                previous_attendance[
                    "break_minutes"
                ],
            ),

            "app_seconds": (
                current_apps[
                    "total_seconds"
                ],
                previous_apps[
                    "total_seconds"
                ],
            ),

            "website_seconds": (
                current_websites[
                    "total_seconds"
                ],
                previous_websites[
                    "total_seconds"
                ],
            ),

            "goals_completed": (
                current_goals[
                    "completed"
                ],
                previous_goals[
                    "completed"
                ],
            ),

            "goals_average_progress": (
                current_goals[
                    "average_progress"
                ],
                previous_goals[
                    "average_progress"
                ],
            ),
        }

        metrics: list[
            ProductivityMetricComparison
        ] = []

        for (
            key,
            (
                current_value,
                previous_value,
            ),
        ) in metric_values.items():
            change = metric_change(
                current=current_value,
                previous=previous_value,
            )

            metrics.append(
                ProductivityMetricComparison(
                    key=key,
                    current=change.current,
                    previous=change.previous,
                    absolute_change=(
                        change.absolute_change
                    ),
                    percent_change=(
                        change.percent_change
                    ),
                )
            )

        return (
            ProductivityComparisonResponse(
                workspace_id=workspace_id,

                scope=self._scope(
                    access
                ),

                current_window=window,

                previous_window=(
                    previous_window
                ),

                metrics=metrics,
            )
        )


__all__ = [
    "ProductivityInsightsService",
]