from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from uuid import UUID

from app.modules.app_tracking.history_schemas import (
    AppUsageAggregateItem,
    AppUsageAggregateResponse,
    AppUsageHistoryItem,
    AppUsageHistoryResponse,
)
from app.modules.app_tracking.repository import (
    AppTrackingRepository,
)


class AppTrackingHistoryService:
    def __init__(
        self,
        repository: AppTrackingRepository,
    ) -> None:
        self._repository = repository

    async def list_device_history(
        self,
        device_id: UUID,
        *,
        limit: int = 200,
    ) -> AppUsageHistoryResponse:
        if limit < 1 or limit > 5000:
            raise ValueError(
                "limit must be between 1 and 5000."
            )

        intervals = (
            await self._repository
            .list_intervals_for_device(
                device_id,
                limit=limit,
            )
        )

        items = [
            AppUsageHistoryItem(
                id=interval.id,
                device_id=interval.device_id,
                employee_id=interval.employee_id,
                app_key=interval.app_key,
                process_name=interval.process_name,
                executable_path=interval.executable_path,
                status=interval.status,
                started_at=interval.started_at,
                ended_at=interval.ended_at,
                last_observed_at=interval.last_observed_at,
                duration_seconds=interval.duration_seconds,
            )
            for interval in intervals
        ]

        return AppUsageHistoryResponse(
            items=items,
            count=len(items),
        )

    async def aggregate_between(
        self,
        *,
        started_from: datetime,
        started_to: datetime,
        device_id: UUID | None = None,
        employee_id: UUID | None = None,
    ) -> AppUsageAggregateResponse:
        if (
            started_from.tzinfo is None
            or started_to.tzinfo is None
        ):
            raise ValueError(
                "Date boundaries must be timezone-aware."
            )

        if started_to <= started_from:
            raise ValueError(
                "started_to must be after started_from."
            )

        intervals = (
            await self._repository
            .list_intervals_between(
                started_from=started_from,
                started_to=started_to,
                employee_id=employee_id,
                device_id=device_id,
            )
        )

        durations: dict[
            tuple[str, str],
            int,
        ] = defaultdict(int)

        counts: dict[
            tuple[str, str],
            int,
        ] = defaultdict(int)

        for interval in intervals:
            key = (
                interval.app_key,
                interval.process_name,
            )

            durations[key] += (
                interval.duration_seconds
            )

            counts[key] += 1

        items = [
            AppUsageAggregateItem(
                app_key=app_key,
                process_name=process_name,
                duration_seconds=duration,
                interval_count=counts[
                    (
                        app_key,
                        process_name,
                    )
                ],
            )
            for (
                app_key,
                process_name,
            ), duration in sorted(
                durations.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]

        return AppUsageAggregateResponse(
            items=items,
            total_seconds=sum(
                item.duration_seconds
                for item in items
            ),
            interval_count=sum(
                item.interval_count
                for item in items
            ),
        )


__all__ = [
    "AppTrackingHistoryService",
]