from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.modules.activity.models import (
    ACTIVITY_STATE_ACTIVE,
    ACTIVITY_STATE_IDLE,
    ActivityStateEvent,
)
from app.modules.work_sessions.models import (
    WORK_SESSION_STATE_ACTIVE,
    WORK_SESSION_STATE_IDLE,
    WORK_SESSION_STATUS_CLOSED,
    WORK_SESSION_STATUS_OPEN,
    WorkSession,
)
from app.modules.work_sessions.repository import (
    WorkSessionRepository,
)
from app.modules.work_sessions.schemas import (
    WorkSessionProcessingResult,
    WorkSessionResponse,
    WorkSessionSummaryResponse,
)


DEFAULT_MAX_EVENT_GAP_SECONDS = 10 * 60


class WorkSessionService:
    def __init__(
        self,
        repository: WorkSessionRepository,
        *,
        max_event_gap_seconds: int = DEFAULT_MAX_EVENT_GAP_SECONDS,
    ) -> None:
        if max_event_gap_seconds <= 0:
            raise ValueError(
                "max_event_gap_seconds must be greater than zero."
            )

        self._repository = repository
        self._max_event_gap_seconds = (
            max_event_gap_seconds
        )

    async def process_activity_event(
        self,
        event: ActivityStateEvent,
    ) -> WorkSessionProcessingResult:
        if event.state not in {
            ACTIVITY_STATE_ACTIVE,
            ACTIVITY_STATE_IDLE,
        }:
            raise ValueError(
                f"Unsupported activity state: {event.state!r}"
            )

        existing = (
            await self._repository.get_open_for_device(
                event.device_id
            )
        )

        if existing is None:
            created = await self._create_session_from_event(
                event
            )

            await self._repository.commit()

            return self._processing_result(
                created,
                created=True,
                closed_previous_session=False,
                ignored_event=False,
            )

        if event.observed_at <= existing.last_observed_at:
            return self._processing_result(
                existing,
                created=False,
                closed_previous_session=False,
                ignored_event=True,
            )

        elapsed_seconds = int(
            (
                event.observed_at
                - existing.last_observed_at
            ).total_seconds()
        )

        if elapsed_seconds > self._max_event_gap_seconds:
            await self._close_session(
                existing,
                existing.last_observed_at,
            )

            new_session = await self._create_session_from_event(
                event
            )

            await self._repository.commit()

            return self._processing_result(
                new_session,
                created=True,
                closed_previous_session=True,
                ignored_event=False,
            )

        self._apply_elapsed_time(
            existing,
            elapsed_seconds,
        )

        existing.current_state = (
            self._normalize_state(
                event.state
            )
        )

        existing.last_observed_at = (
            event.observed_at
        )

        if (
            event.employee_id is not None
            and existing.employee_id is None
        ):
            existing.employee_id = (
                event.employee_id
            )

        await self._repository.commit()

        return self._processing_result(
            existing,
            created=False,
            closed_previous_session=False,
            ignored_event=False,
        )

    async def close_open_session(
        self,
        device_id: UUID,
        *,
        ended_at: datetime | None = None,
    ) -> WorkSession | None:
        existing = (
            await self._repository.get_open_for_device(
                device_id
            )
        )

        if existing is None:
            return None

        close_at = (
            ended_at
            or existing.last_observed_at
        )

        if close_at < existing.started_at:
            raise ValueError(
                "Session end cannot be earlier than session start."
            )

        if close_at > existing.last_observed_at:
            elapsed_seconds = int(
                (
                    close_at
                    - existing.last_observed_at
                ).total_seconds()
            )

            if (
                elapsed_seconds
                <= self._max_event_gap_seconds
            ):
                self._apply_elapsed_time(
                    existing,
                    elapsed_seconds,
                )

        await self._close_session(
            existing,
            close_at,
        )

        await self._repository.commit()

        return existing

    async def close_stale_sessions(
        self,
        *,
        stale_before: datetime,
        limit: int = 500,
    ) -> int:
        stale_sessions = (
            await self._repository.list_open_stale_before(
                stale_before,
                limit=limit,
            )
        )

        for work_session in stale_sessions:
            await self._close_session(
                work_session,
                work_session.last_observed_at,
            )

        if stale_sessions:
            await self._repository.commit()

        return len(
            stale_sessions
        )

    async def get_device_sessions(
        self,
        device_id: UUID,
        *,
        limit: int = 100,
    ) -> list[WorkSessionResponse]:
        sessions = (
            await self._repository.list_for_device(
                device_id,
                limit=limit,
            )
        )

        return [
            self._to_response(
                session
            )
            for session in sessions
        ]

    async def get_employee_sessions(
        self,
        employee_id: UUID,
        *,
        limit: int = 100,
    ) -> list[WorkSessionResponse]:
        sessions = (
            await self._repository.list_for_employee(
                employee_id,
                limit=limit,
            )
        )

        return [
            self._to_response(
                session
            )
            for session in sessions
        ]

    async def summarize_between(
        self,
        *,
        started_from: datetime,
        started_to: datetime,
        employee_id: UUID | None = None,
        device_id: UUID | None = None,
    ) -> WorkSessionSummaryResponse:
        sessions = (
            await self._repository.list_between(
                started_from=started_from,
                started_to=started_to,
                employee_id=employee_id,
                device_id=device_id,
            )
        )

        active_seconds = sum(
            session.active_seconds
            for session in sessions
        )

        idle_seconds = sum(
            session.idle_seconds
            for session in sessions
        )

        first_started_at = (
            sessions[0].started_at
            if sessions
            else None
        )

        last_observed_at = (
            max(
                session.last_observed_at
                for session in sessions
            )
            if sessions
            else None
        )

        return WorkSessionSummaryResponse(
            session_count=len(
                sessions
            ),
            active_seconds=active_seconds,
            idle_seconds=idle_seconds,
            total_seconds=(
                active_seconds
                + idle_seconds
            ),
            first_started_at=first_started_at,
            last_observed_at=last_observed_at,
        )

    async def _create_session_from_event(
        self,
        event: ActivityStateEvent,
    ) -> WorkSession:
        session = WorkSession(
            device_id=event.device_id,
            employee_id=event.employee_id,
            status=WORK_SESSION_STATUS_OPEN,
            current_state=self._normalize_state(
                event.state
            ),
            started_at=event.observed_at,
            ended_at=None,
            last_observed_at=event.observed_at,
            active_seconds=0,
            idle_seconds=0,
        )

        return await self._repository.create(
            session
        )

    async def _close_session(
        self,
        work_session: WorkSession,
        ended_at: datetime,
    ) -> None:
        if ended_at < work_session.started_at:
            raise ValueError(
                "Session end cannot be earlier than session start."
            )

        work_session.status = (
            WORK_SESSION_STATUS_CLOSED
        )

        work_session.ended_at = (
            ended_at
        )

    @staticmethod
    def _apply_elapsed_time(
        work_session: WorkSession,
        elapsed_seconds: int,
    ) -> None:
        if elapsed_seconds <= 0:
            return

        if (
            work_session.current_state
            == WORK_SESSION_STATE_ACTIVE
        ):
            work_session.active_seconds += (
                elapsed_seconds
            )

        elif (
            work_session.current_state
            == WORK_SESSION_STATE_IDLE
        ):
            work_session.idle_seconds += (
                elapsed_seconds
            )

        else:
            raise ValueError(
                "Work session contains unsupported current_state: "
                f"{work_session.current_state!r}"
            )

    @staticmethod
    def _normalize_state(
        state: str,
    ) -> str:
        if state == ACTIVITY_STATE_ACTIVE:
            return WORK_SESSION_STATE_ACTIVE

        if state == ACTIVITY_STATE_IDLE:
            return WORK_SESSION_STATE_IDLE

        raise ValueError(
            f"Unsupported activity state: {state!r}"
        )

    @staticmethod
    def _to_response(
        work_session: WorkSession,
    ) -> WorkSessionResponse:
        return WorkSessionResponse(
            id=work_session.id,
            device_id=work_session.device_id,
            employee_id=work_session.employee_id,
            status=work_session.status,
            current_state=work_session.current_state,
            started_at=work_session.started_at,
            ended_at=work_session.ended_at,
            last_observed_at=work_session.last_observed_at,
            active_seconds=work_session.active_seconds,
            idle_seconds=work_session.idle_seconds,
            total_seconds=work_session.total_seconds,
        )

    @staticmethod
    def _processing_result(
        work_session: WorkSession,
        *,
        created: bool,
        closed_previous_session: bool,
        ignored_event: bool,
    ) -> WorkSessionProcessingResult:
        return WorkSessionProcessingResult(
            session_id=work_session.id,
            created=created,
            closed_previous_session=closed_previous_session,
            ignored_event=ignored_event,
            status=work_session.status,
            current_state=work_session.current_state,
            active_seconds=work_session.active_seconds,
            idle_seconds=work_session.idle_seconds,
            total_seconds=work_session.total_seconds,
        )


__all__ = [
    "DEFAULT_MAX_EVENT_GAP_SECONDS",
    "WorkSessionService",
]