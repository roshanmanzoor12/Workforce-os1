from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.modules.activity.models import ActivityStateEvent
from app.modules.work_sessions.models import (
    WORK_SESSION_STATE_ACTIVE,
    WORK_SESSION_STATE_IDLE,
    WORK_SESSION_STATUS_CLOSED,
    WORK_SESSION_STATUS_OPEN,
    WorkSession,
)
from app.modules.work_sessions.service import WorkSessionService


class FakeWorkSessionRepository:
    def __init__(self) -> None:
        self.sessions: list[WorkSession] = []
        self.commit_count = 0

    async def create(
        self,
        work_session: WorkSession,
    ) -> WorkSession:
        if work_session.id is None:
            work_session.id = uuid4()

        self.sessions.append(
            work_session
        )

        return work_session

    async def get_open_for_device(
        self,
        device_id: UUID,
    ) -> WorkSession | None:
        matches = [
            work_session
            for work_session in self.sessions
            if (
                work_session.device_id == device_id
                and work_session.status == WORK_SESSION_STATUS_OPEN
            )
        ]

        if not matches:
            return None

        return max(
            matches,
            key=lambda item: item.started_at,
        )

    async def list_for_device(
        self,
        device_id: UUID,
        *,
        limit: int = 100,
    ) -> list[WorkSession]:
        return [
            item
            for item in self.sessions
            if item.device_id == device_id
        ][:limit]

    async def list_for_employee(
        self,
        employee_id: UUID,
        *,
        limit: int = 100,
    ) -> list[WorkSession]:
        return [
            item
            for item in self.sessions
            if item.employee_id == employee_id
        ][:limit]

    async def list_between(
        self,
        *,
        started_from: datetime,
        started_to: datetime,
        employee_id: UUID | None = None,
        device_id: UUID | None = None,
        limit: int = 1000,
    ) -> list[WorkSession]:
        result: list[WorkSession] = []

        for item in self.sessions:
            if item.started_at < started_from:
                continue

            if item.started_at >= started_to:
                continue

            if (
                employee_id is not None
                and item.employee_id != employee_id
            ):
                continue

            if (
                device_id is not None
                and item.device_id != device_id
            ):
                continue

            result.append(
                item
            )

        return result[:limit]

    async def list_open_stale_before(
        self,
        cutoff: datetime,
        *,
        limit: int = 500,
    ) -> list[WorkSession]:
        return [
            item
            for item in self.sessions
            if (
                item.status == WORK_SESSION_STATUS_OPEN
                and item.last_observed_at < cutoff
            )
        ][:limit]

    async def commit(
        self,
    ) -> None:
        self.commit_count += 1


def make_event(
    *,
    device_id: UUID,
    observed_at: datetime,
    state: str,
    employee_id: UUID | None = None,
    idle_seconds: int = 0,
) -> ActivityStateEvent:
    return ActivityStateEvent(
        id=uuid4(),
        device_id=device_id,
        employee_id=employee_id,
        state=state,
        idle_seconds=idle_seconds,
        last_input_at=(
            observed_at
            - timedelta(
                seconds=idle_seconds
            )
        ),
        observed_at=observed_at,
        received_at=observed_at,
        created_at=observed_at,
    )


@pytest.mark.asyncio
async def test_first_activity_event_creates_open_session() -> None:
    repository = FakeWorkSessionRepository()

    service = WorkSessionService(
        repository
    )

    device_id = uuid4()

    observed_at = datetime(
        2026,
        8,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )

    event = make_event(
        device_id=device_id,
        observed_at=observed_at,
        state="active",
    )

    result = await service.process_activity_event(
        event
    )

    assert result.created is True
    assert result.ignored_event is False
    assert result.closed_previous_session is False

    assert len(repository.sessions) == 1

    work_session = repository.sessions[0]

    assert work_session.device_id == device_id
    assert work_session.status == WORK_SESSION_STATUS_OPEN
    assert work_session.current_state == WORK_SESSION_STATE_ACTIVE
    assert work_session.started_at == observed_at
    assert work_session.last_observed_at == observed_at
    assert work_session.active_seconds == 0
    assert work_session.idle_seconds == 0


@pytest.mark.asyncio
async def test_active_interval_is_accumulated() -> None:
    repository = FakeWorkSessionRepository()

    service = WorkSessionService(
        repository
    )

    device_id = uuid4()

    start = datetime(
        2026,
        8,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )

    await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=start,
            state="active",
        )
    )

    result = await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=(
                start
                + timedelta(
                    seconds=60
                )
            ),
            state="active",
        )
    )

    assert result.created is False
    assert result.active_seconds == 60
    assert result.idle_seconds == 0
    assert result.total_seconds == 60


@pytest.mark.asyncio
async def test_active_to_idle_transition_counts_previous_active_interval() -> None:
    repository = FakeWorkSessionRepository()

    service = WorkSessionService(
        repository
    )

    device_id = uuid4()

    start = datetime(
        2026,
        8,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )

    await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=start,
            state="active",
        )
    )

    result = await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=(
                start
                + timedelta(
                    seconds=300
                )
            ),
            state="idle",
            idle_seconds=300,
        )
    )

    assert result.active_seconds == 300
    assert result.idle_seconds == 0
    assert result.current_state == WORK_SESSION_STATE_IDLE


@pytest.mark.asyncio
async def test_idle_interval_is_accumulated_until_next_event() -> None:
    repository = FakeWorkSessionRepository()

    service = WorkSessionService(
        repository
    )

    device_id = uuid4()

    start = datetime(
        2026,
        8,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )

    await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=start,
            state="active",
        )
    )

    await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=(
                start
                + timedelta(
                    seconds=300
                )
            ),
            state="idle",
            idle_seconds=300,
        )
    )

    result = await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=(
                start
                + timedelta(
                    seconds=420
                )
            ),
            state="active",
        )
    )

    assert result.active_seconds == 300
    assert result.idle_seconds == 120
    assert result.total_seconds == 420
    assert result.current_state == WORK_SESSION_STATE_ACTIVE


@pytest.mark.asyncio
async def test_duplicate_or_old_event_is_ignored() -> None:
    repository = FakeWorkSessionRepository()

    service = WorkSessionService(
        repository
    )

    device_id = uuid4()

    start = datetime(
        2026,
        8,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )

    await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=start,
            state="active",
        )
    )

    duplicate_result = (
        await service.process_activity_event(
            make_event(
                device_id=device_id,
                observed_at=start,
                state="idle",
            )
        )
    )

    assert duplicate_result.ignored_event is True

    work_session = repository.sessions[0]

    assert work_session.current_state == WORK_SESSION_STATE_ACTIVE
    assert work_session.active_seconds == 0
    assert work_session.idle_seconds == 0


@pytest.mark.asyncio
async def test_large_gap_closes_old_session_and_opens_new_one() -> None:
    repository = FakeWorkSessionRepository()

    service = WorkSessionService(
        repository,
        max_event_gap_seconds=600,
    )

    device_id = uuid4()

    start = datetime(
        2026,
        8,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )

    await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=start,
            state="active",
        )
    )

    result = await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=(
                start
                + timedelta(
                    seconds=601
                )
            ),
            state="active",
        )
    )

    assert result.created is True
    assert result.closed_previous_session is True

    assert len(repository.sessions) == 2

    old_session = repository.sessions[0]
    new_session = repository.sessions[1]

    assert old_session.status == WORK_SESSION_STATUS_CLOSED
    assert old_session.ended_at == start

    assert new_session.status == WORK_SESSION_STATUS_OPEN
    assert new_session.started_at == (
        start
        + timedelta(
            seconds=601
        )
    )

    assert old_session.active_seconds == 0


@pytest.mark.asyncio
async def test_employee_assignment_is_adopted_when_available() -> None:
    repository = FakeWorkSessionRepository()

    service = WorkSessionService(
        repository
    )

    device_id = uuid4()
    employee_id = uuid4()

    start = datetime(
        2026,
        8,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )

    await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=start,
            state="active",
            employee_id=None,
        )
    )

    await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=(
                start
                + timedelta(
                    seconds=30
                )
            ),
            state="active",
            employee_id=employee_id,
        )
    )

    work_session = repository.sessions[0]

    assert work_session.employee_id == employee_id


@pytest.mark.asyncio
async def test_close_stale_session_uses_last_observed_time() -> None:
    repository = FakeWorkSessionRepository()

    service = WorkSessionService(
        repository
    )

    device_id = uuid4()

    start = datetime(
        2026,
        8,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )

    await service.process_activity_event(
        make_event(
            device_id=device_id,
            observed_at=start,
            state="active",
        )
    )

    count = await service.close_stale_sessions(
        stale_before=(
            start
            + timedelta(
                minutes=20
            )
        )
    )

    assert count == 1

    work_session = repository.sessions[0]

    assert work_session.status == WORK_SESSION_STATUS_CLOSED
    assert work_session.ended_at == start