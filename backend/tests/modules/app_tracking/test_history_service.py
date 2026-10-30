from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

import pytest

from app.modules.app_tracking.history_service import (
    AppTrackingHistoryService,
)
from app.modules.app_tracking.models import (
    AppUsageInterval,
)


class FakeRepository:
    def __init__(
        self,
        intervals: list[
            AppUsageInterval
        ],
    ) -> None:
        self.intervals = (
            intervals
        )

    async def list_intervals_for_device(
        self,
        device_id,
        *,
        limit=200,
    ):
        return [
            interval
            for interval
            in self.intervals
            if interval.device_id
            == device_id
        ][:limit]

    async def list_intervals_between(
        self,
        *,
        started_from,
        started_to,
        employee_id=None,
        device_id=None,
        limit=5000,
    ):
        result = []

        for interval in self.intervals:
            if (
                interval.started_at
                < started_from
            ):
                continue

            if (
                interval.started_at
                >= started_to
            ):
                continue

            if (
                device_id is not None
                and interval.device_id
                != device_id
            ):
                continue

            if (
                employee_id is not None
                and interval.employee_id
                != employee_id
            ):
                continue

            result.append(
                interval
            )

        return result[
            :limit
        ]


def make_interval(
    process_name: str,
    duration: int,
    started_at: datetime,
    device_id,
) -> AppUsageInterval:
    return AppUsageInterval(
        id=uuid4(),
        device_id=device_id,
        employee_id=None,
        app_key=(
            process_name.casefold()
        ),
        process_name=process_name,
        executable_path=None,
        last_window_title=None,
        status="closed",
        started_at=started_at,
        ended_at=(
            started_at
            + timedelta(
                seconds=duration
            )
        ),
        last_observed_at=(
            started_at
            + timedelta(
                seconds=duration
            )
        ),
        duration_seconds=duration,
    )


@pytest.mark.asyncio
async def test_device_history() -> None:
    now = datetime.now(
        timezone.utc
    )

    device_id = uuid4()

    repository = FakeRepository(
        [
            make_interval(
                "code.exe",
                60,
                now,
                device_id,
            ),
            make_interval(
                "chrome.exe",
                30,
                now
                + timedelta(
                    minutes=2
                ),
                device_id,
            ),
        ]
    )

    service = AppTrackingHistoryService(
        repository
    )

    result = await service.list_device_history(
        device_id
    )

    assert result.count == 2


@pytest.mark.asyncio
async def test_aggregate_between() -> None:
    start = datetime(
        2026,
        8,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )

    device_id = uuid4()

    repository = FakeRepository(
        [
            make_interval(
                "code.exe",
                60,
                start,
                device_id,
            ),
            make_interval(
                "code.exe",
                120,
                start
                + timedelta(
                    minutes=3
                ),
                device_id,
            ),
            make_interval(
                "chrome.exe",
                30,
                start
                + timedelta(
                    minutes=6
                ),
                device_id,
            ),
        ]
    )

    service = AppTrackingHistoryService(
        repository
    )

    result = await service.aggregate_between(
        started_from=start,
        started_to=(
            start
            + timedelta(
                hours=1
            )
        ),
        device_id=device_id,
    )

    assert result.total_seconds == 210

    assert result.interval_count == 3

    assert result.items[0].process_name == (
        "code.exe"
    )

    assert (
        result.items[0].duration_seconds
        == 180
    )


@pytest.mark.asyncio
async def test_aggregate_rejects_invalid_range() -> None:
    repository = FakeRepository(
        []
    )

    service = AppTrackingHistoryService(
        repository
    )

    now = datetime.now(
        timezone.utc
    )

    with pytest.raises(
        ValueError,
        match="started_to",
    ):
        await service.aggregate_between(
            started_from=now,
            started_to=now,
        )