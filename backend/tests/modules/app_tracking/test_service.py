from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.modules.app_tracking.models import (
    APP_USAGE_STATUS_CLOSED,
    APP_USAGE_STATUS_OPEN,
    AppObservation,
    AppUsageInterval,
)
from app.modules.app_tracking.service import (
    AppTrackingService,
)


class FakeAppTrackingRepository:
    def __init__(self) -> None:
        self.intervals: list[
            AppUsageInterval
        ] = []

        self.commit_count = 0

    async def create_interval(
        self,
        interval: AppUsageInterval,
    ) -> AppUsageInterval:
        if interval.id is None:
            interval.id = uuid4()

        self.intervals.append(
            interval
        )

        return interval

    async def get_open_interval_for_device(
        self,
        device_id: UUID,
    ) -> AppUsageInterval | None:
        matches = [
            interval
            for interval in self.intervals
            if (
                interval.device_id == device_id
                and interval.status == APP_USAGE_STATUS_OPEN
            )
        ]

        if not matches:
            return None

        return max(
            matches,
            key=lambda interval: interval.started_at,
        )

    async def list_intervals_between(
        self,
        *,
        started_from: datetime,
        started_to: datetime,
        employee_id: UUID | None = None,
        device_id: UUID | None = None,
        limit: int = 5000,
    ) -> list[AppUsageInterval]:
        result: list[
            AppUsageInterval
        ] = []

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
                employee_id is not None
                and interval.employee_id
                != employee_id
            ):
                continue

            if (
                device_id is not None
                and interval.device_id
                != device_id
            ):
                continue

            result.append(
                interval
            )

        return result[:limit]

    async def commit(
        self,
    ) -> None:
        self.commit_count += 1


def make_observation(
    *,
    device_id: UUID,
    observed_at: datetime,
    process_name: str,
    executable_path: str | None = None,
    employee_id: UUID | None = None,
    window_title: str | None = None,
) -> AppObservation:
    app_key = (
        AppTrackingService.build_app_key(
            process_name,
            executable_path,
        )
    )

    return AppObservation(
        id=uuid4(),
        device_id=device_id,
        employee_id=employee_id,
        app_key=app_key,
        process_name=process_name,
        executable_path=executable_path,
        window_title=window_title,
        observed_at=observed_at,
        received_at=observed_at,
        created_at=observed_at,
    )


@pytest.mark.asyncio
async def test_first_observation_creates_interval() -> None:
    repository = (
        FakeAppTrackingRepository()
    )

    service = AppTrackingService(
        repository
    )

    device_id = uuid4()

    now = datetime(
        2026,
        8,
        28,
        17,
        0,
        tzinfo=timezone.utc,
    )

    result = await service.process_observation(
        make_observation(
            device_id=device_id,
            observed_at=now,
            process_name="code.exe",
        )
    )

    assert result.created is True
    assert result.duration_seconds == 0

    assert len(
        repository.intervals
    ) == 1


@pytest.mark.asyncio
async def test_same_app_accumulates_duration() -> None:
    repository = (
        FakeAppTrackingRepository()
    )

    service = AppTrackingService(
        repository
    )

    device_id = uuid4()

    start = datetime(
        2026,
        8,
        28,
        17,
        0,
        tzinfo=timezone.utc,
    )

    await service.process_observation(
        make_observation(
            device_id=device_id,
            observed_at=start,
            process_name="code.exe",
        )
    )

    result = await service.process_observation(
        make_observation(
            device_id=device_id,
            observed_at=(
                start
                + timedelta(
                    seconds=60
                )
            ),
            process_name="code.exe",
        )
    )

    assert result.created is False
    assert result.duration_seconds == 60


@pytest.mark.asyncio
async def test_app_switch_closes_old_interval() -> None:
    repository = (
        FakeAppTrackingRepository()
    )

    service = AppTrackingService(
        repository
    )

    device_id = uuid4()

    start = datetime(
        2026,
        8,
        28,
        17,
        0,
        tzinfo=timezone.utc,
    )

    await service.process_observation(
        make_observation(
            device_id=device_id,
            observed_at=start,
            process_name="code.exe",
        )
    )

    result = await service.process_observation(
        make_observation(
            device_id=device_id,
            observed_at=(
                start
                + timedelta(
                    seconds=120
                )
            ),
            process_name="chrome.exe",
        )
    )

    assert result.created is True

    assert (
        result.closed_previous_interval
        is True
    )

    assert len(
        repository.intervals
    ) == 2

    old_interval = (
        repository.intervals[0]
    )

    new_interval = (
        repository.intervals[1]
    )

    assert (
        old_interval.status
        == APP_USAGE_STATUS_CLOSED
    )

    assert old_interval.duration_seconds == 120

    assert (
        new_interval.status
        == APP_USAGE_STATUS_OPEN
    )

    assert (
        new_interval.process_name
        == "chrome.exe"
    )


@pytest.mark.asyncio
async def test_large_gap_does_not_count_offline_time() -> None:
    repository = (
        FakeAppTrackingRepository()
    )

    service = AppTrackingService(
        repository,
        max_observation_gap_seconds=600,
    )

    device_id = uuid4()

    start = datetime(
        2026,
        8,
        28,
        17,
        0,
        tzinfo=timezone.utc,
    )

    await service.process_observation(
        make_observation(
            device_id=device_id,
            observed_at=start,
            process_name="code.exe",
        )
    )

    await service.process_observation(
        make_observation(
            device_id=device_id,
            observed_at=(
                start
                + timedelta(
                    seconds=601
                )
            ),
            process_name="code.exe",
        )
    )

    assert len(
        repository.intervals
    ) == 2

    old_interval = (
        repository.intervals[0]
    )

    assert (
        old_interval.status
        == APP_USAGE_STATUS_CLOSED
    )

    assert old_interval.duration_seconds == 0

    assert old_interval.ended_at == start


@pytest.mark.asyncio
async def test_old_observation_is_ignored() -> None:
    repository = (
        FakeAppTrackingRepository()
    )

    service = AppTrackingService(
        repository
    )

    device_id = uuid4()

    start = datetime(
        2026,
        8,
        28,
        17,
        0,
        tzinfo=timezone.utc,
    )

    await service.process_observation(
        make_observation(
            device_id=device_id,
            observed_at=start,
            process_name="code.exe",
        )
    )

    result = await service.process_observation(
        make_observation(
            device_id=device_id,
            observed_at=start,
            process_name="chrome.exe",
        )
    )

    assert (
        result.ignored_observation
        is True
    )

    assert len(
        repository.intervals
    ) == 1


def test_app_key_is_stable_and_case_insensitive() -> None:
    first = (
        AppTrackingService.build_app_key(
            "Chrome.EXE",
            "C:\\Program Files\\Chrome\\chrome.exe",
        )
    )

    second = (
        AppTrackingService.build_app_key(
            "chrome.exe",
            "c:\\program files\\chrome\\CHROME.EXE",
        )
    )

    assert first == second

    assert len(first) == 64