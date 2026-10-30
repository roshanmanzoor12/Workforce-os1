from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import (
    datetime,
    timezone,
)

from app.modules.website_tracking.history_schemas import (
    WebsiteUsageAggregateItem,
    WebsiteUsageAggregateResponse,
    WebsiteUsageHistoryItem,
    WebsiteUsageHistoryResponse,
)
from app.modules.website_tracking.repository import (
    WebsiteTrackingRepository,
)


class WebsiteTrackingHistoryService:
    def __init__(
        self,
        repository: WebsiteTrackingRepository,
    ) -> None:
        self._repository = repository

    async def list_device_history(
        self,
        *,
        device_id: uuid.UUID,
        limit: int = 100,
    ) -> WebsiteUsageHistoryResponse:
        bounded_limit = max(
            1,
            min(
                limit,
                5000,
            ),
        )

        intervals = (
            await self._repository
            .list_device_intervals(
                device_id=device_id,
                limit=bounded_limit,
            )
        )

        items = [
            WebsiteUsageHistoryItem
            .model_validate(
                interval
            )
            for interval in intervals
        ]

        return WebsiteUsageHistoryResponse(
            items=items,
            count=len(items),
        )

    async def aggregate_between(
        self,
        *,
        device_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> WebsiteUsageAggregateResponse:
        if start_at.tzinfo is None:
            raise ValueError(
                "start_at must be timezone-aware."
            )

        if end_at.tzinfo is None:
            raise ValueError(
                "end_at must be timezone-aware."
            )

        start_at = start_at.astimezone(
            timezone.utc
        )

        end_at = end_at.astimezone(
            timezone.utc
        )

        if end_at <= start_at:
            raise ValueError(
                "end_at must be after start_at."
            )

        intervals = (
            await self._repository
            .list_intervals_between(
                device_id=device_id,
                start_at=start_at,
                end_at=end_at,
            )
        )

        duration_by_domain: dict[
            str,
            int,
        ] = defaultdict(
            int
        )

        count_by_domain: dict[
            str,
            int,
        ] = defaultdict(
            int
        )

        display_domain: dict[
            str,
            str,
        ] = {}

        total_seconds = 0

        for interval in intervals:
            interval_start = max(
                interval.started_at,
                start_at,
            )

            interval_end = min(
                (
                    interval.ended_at
                    or interval.last_observed_at
                ),
                end_at,
            )

            if interval_end <= interval_start:
                continue

            seconds = int(
                (
                    interval_end
                    - interval_start
                ).total_seconds()
            )

            if seconds <= 0:
                continue

            key = (
                interval.normalized_domain
            )

            duration_by_domain[
                key
            ] += seconds

            count_by_domain[
                key
            ] += 1

            display_domain[
                key
            ] = interval.domain

            total_seconds += seconds

        items = [
            WebsiteUsageAggregateItem(
                normalized_domain=key,
                domain=display_domain[
                    key
                ],
                duration_seconds=duration,
                interval_count=(
                    count_by_domain[
                        key
                    ]
                ),
            )
            for (
                key,
                duration,
            ) in duration_by_domain.items()
        ]

        items.sort(
            key=lambda item: (
                -item.duration_seconds,
                item.normalized_domain,
            )
        )

        return WebsiteUsageAggregateResponse(
            items=items,
            total_seconds=total_seconds,
            interval_count=sum(
                count_by_domain.values()
            ),
        )


__all__ = [
    "WebsiteTrackingHistoryService",
]