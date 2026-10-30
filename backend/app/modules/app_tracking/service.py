from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime
from uuid import UUID

from app.modules.app_tracking.models import (
    APP_USAGE_STATUS_CLOSED,
    APP_USAGE_STATUS_OPEN,
    AppObservation,
    AppUsageInterval,
)
from app.modules.app_tracking.repository import (
    AppTrackingRepository,
)
from app.modules.app_tracking.schemas import (
    AppTrackingProcessingResult,
    AppUsageSummaryItem,
    AppUsageSummaryResponse,
)


DEFAULT_MAX_OBSERVATION_GAP_SECONDS = 10 * 60


class AppTrackingService:
    def __init__(
        self,
        repository: AppTrackingRepository,
        *,
        max_observation_gap_seconds: int = (
            DEFAULT_MAX_OBSERVATION_GAP_SECONDS
        ),
    ) -> None:
        if max_observation_gap_seconds <= 0:
            raise ValueError(
                "max_observation_gap_seconds must be greater than zero."
            )

        self._repository = repository
        self._max_observation_gap_seconds = (
            max_observation_gap_seconds
        )

    @staticmethod
    def build_app_key(
        process_name: str,
        executable_path: str | None,
    ) -> str:
        process_part = (
            process_name
            .strip()
            .casefold()
        )

        path_part = (
            executable_path
            .strip()
            .casefold()
            if executable_path
            else ""
        )

        identity = (
            process_part
            + "\n"
            + path_part
        )

        return hashlib.sha256(
            identity.encode(
                "utf-8"
            )
        ).hexdigest()

    async def process_observation(
        self,
        observation: AppObservation,
    ) -> AppTrackingProcessingResult:
        open_interval = (
            await self._repository.get_open_interval_for_device(
                observation.device_id
            )
        )

        if open_interval is None:
            created = await self._create_interval(
                observation
            )

            await self._repository.commit()

            return self._result(
                created,
                created=True,
                closed_previous_interval=False,
                ignored_observation=False,
            )

        if (
            observation.observed_at
            <= open_interval.last_observed_at
        ):
            return self._result(
                open_interval,
                created=False,
                closed_previous_interval=False,
                ignored_observation=True,
            )

        elapsed_seconds = int(
            (
                observation.observed_at
                - open_interval.last_observed_at
            ).total_seconds()
        )

        if (
            elapsed_seconds
            > self._max_observation_gap_seconds
        ):
            self._close_interval(
                open_interval,
                open_interval.last_observed_at,
            )

            created = await self._create_interval(
                observation
            )

            await self._repository.commit()

            return self._result(
                created,
                created=True,
                closed_previous_interval=True,
                ignored_observation=False,
            )

        if (
            open_interval.app_key
            != observation.app_key
        ):
            self._close_interval(
                open_interval,
                observation.observed_at,
            )

            open_interval.duration_seconds += (
                elapsed_seconds
            )

            created = await self._create_interval(
                observation
            )

            await self._repository.commit()

            return self._result(
                created,
                created=True,
                closed_previous_interval=True,
                ignored_observation=False,
            )

        open_interval.duration_seconds += (
            elapsed_seconds
        )

        open_interval.last_observed_at = (
            observation.observed_at
        )

        open_interval.last_window_title = (
            observation.window_title
        )

        if (
            observation.employee_id is not None
            and open_interval.employee_id is None
        ):
            open_interval.employee_id = (
                observation.employee_id
            )

        await self._repository.commit()

        return self._result(
            open_interval,
            created=False,
            closed_previous_interval=False,
            ignored_observation=False,
        )

    async def close_open_interval(
        self,
        device_id: UUID,
        *,
        ended_at: datetime | None = None,
    ) -> AppUsageInterval | None:
        interval = (
            await self._repository.get_open_interval_for_device(
                device_id
            )
        )

        if interval is None:
            return None

        close_at = (
            ended_at
            or interval.last_observed_at
        )

        if close_at < interval.started_at:
            raise ValueError(
                "Interval end cannot be before interval start."
            )

        if close_at > interval.last_observed_at:
            elapsed_seconds = int(
                (
                    close_at
                    - interval.last_observed_at
                ).total_seconds()
            )

            if (
                elapsed_seconds
                <= self._max_observation_gap_seconds
            ):
                interval.duration_seconds += (
                    elapsed_seconds
                )

                interval.last_observed_at = (
                    close_at
                )

        self._close_interval(
            interval,
            close_at,
        )

        await self._repository.commit()

        return interval

    async def summarize_between(
        self,
        *,
        started_from: datetime,
        started_to: datetime,
        employee_id: UUID | None = None,
        device_id: UUID | None = None,
    ) -> AppUsageSummaryResponse:
        intervals = (
            await self._repository.list_intervals_between(
                started_from=started_from,
                started_to=started_to,
                employee_id=employee_id,
                device_id=device_id,
            )
        )

        totals: dict[
            tuple[str, str],
            int,
        ] = defaultdict(
            int
        )

        for interval in intervals:
            totals[
                (
                    interval.app_key,
                    interval.process_name,
                )
            ] += interval.duration_seconds

        items = [
            AppUsageSummaryItem(
                app_key=app_key,
                process_name=process_name,
                duration_seconds=duration_seconds,
            )
            for (
                app_key,
                process_name,
            ), duration_seconds
            in sorted(
                totals.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]

        return AppUsageSummaryResponse(
            items=items,
            total_seconds=sum(
                item.duration_seconds
                for item in items
            ),
        )

    async def _create_interval(
        self,
        observation: AppObservation,
    ) -> AppUsageInterval:
        interval = AppUsageInterval(
            device_id=observation.device_id,
            employee_id=observation.employee_id,
            app_key=observation.app_key,
            process_name=observation.process_name,
            executable_path=observation.executable_path,
            last_window_title=observation.window_title,
            status=APP_USAGE_STATUS_OPEN,
            started_at=observation.observed_at,
            ended_at=None,
            last_observed_at=observation.observed_at,
            duration_seconds=0,
        )

        return await self._repository.create_interval(
            interval
        )

    @staticmethod
    def _close_interval(
        interval: AppUsageInterval,
        ended_at: datetime,
    ) -> None:
        interval.status = (
            APP_USAGE_STATUS_CLOSED
        )

        interval.ended_at = (
            ended_at
        )

    @staticmethod
    def _result(
        interval: AppUsageInterval,
        *,
        created: bool,
        closed_previous_interval: bool,
        ignored_observation: bool,
    ) -> AppTrackingProcessingResult:
        return AppTrackingProcessingResult(
            interval_id=interval.id,
            created=created,
            closed_previous_interval=closed_previous_interval,
            ignored_observation=ignored_observation,
            app_key=interval.app_key,
            process_name=interval.process_name,
            status=interval.status,
            duration_seconds=interval.duration_seconds,
        )


__all__ = [
    "DEFAULT_MAX_OBSERVATION_GAP_SECONDS",
    "AppTrackingService",
]