from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.attendance.models import (
    AttendanceEvent,
)
from app.modules.goals.models import Goal
from app.modules.knowledge.models import (
    KnowledgeEntry,
)
from app.modules.live_monitoring.models import (
    SCREENSHOT_STATUS_COMPLETED,
    SCREENSHOT_STATUS_DENIED,
    SCREENSHOT_STATUS_EXPIRED,
    SCREENSHOT_STATUS_FAILED,
    SCREENSHOT_STATUS_PENDING,
    ScreenshotCaptureRequest,
)
from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)
from app.modules.notes.models import Note
from app.modules.timeline.enums import (
    TimelineEntityType,
    TimelineEventType,
    TimelineSourceKey,
)
from app.modules.timeline.presenters import (
    attendance_timeline_event_type,
    attendance_timeline_title,
    enum_string_value,
)
from app.modules.timeline.schemas import (
    TimelineEvent,
)


class TimelineSource(
    Protocol
):
    async def list_events(
        self,
        *,
        employee_id: uuid.UUID,
        before: datetime | None,
        after: datetime | None,
        limit: int,
    ) -> list[
        TimelineEvent
    ]:
        ...


class GoalTimelineSource:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def list_events(
        self,
        *,
        employee_id: uuid.UUID,
        before: datetime | None,
        after: datetime | None,
        limit: int,
    ) -> list[
        TimelineEvent
    ]:
        statement = select(
            Goal
        ).where(
            Goal.owner_employee_id
            == employee_id
        )

        if before is not None:
            statement = (
                statement.where(
                    Goal.created_at
                    < before
                )
            )

        if after is not None:
            statement = (
                statement.where(
                    Goal.created_at
                    >= after
                )
            )

        statement = (
            statement
            .order_by(
                Goal.created_at.desc()
            )
            .limit(
                limit
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        goals = list(
            result.scalars().all()
        )

        return [
            TimelineEvent(
                event_id=(
                    "goal.created:"
                    f"{goal.id}"
                ),
                event_type=(
                    TimelineEventType
                    .GOAL_CREATED
                ),
                source=(
                    TimelineSourceKey
                    .GOALS
                ),
                entity_type=(
                    TimelineEntityType
                    .GOAL
                ),
                entity_id=(
                    goal.id
                ),
                employee_id=(
                    employee_id
                ),
                occurred_at=(
                    goal.created_at
                ),
                title=(
                    goal.title
                ),
                summary=(
                    goal.description
                ),
                metadata={
                    "status": (
                        enum_string_value(
                            goal.status
                        )
                    ),
                    "priority": (
                        enum_string_value(
                            goal.priority
                        )
                    ),
                    "progress_percent": (
                        goal
                        .progress_percent
                    ),
                    "due_date": (
                        goal
                        .due_date
                        .isoformat()
                        if (
                            goal.due_date
                            is not None
                        )
                        else None
                    ),
                },
            )
            for goal in goals
        ]


class NoteTimelineSource:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def list_events(
        self,
        *,
        employee_id: uuid.UUID,
        before: datetime | None,
        after: datetime | None,
        limit: int,
    ) -> list[
        TimelineEvent
    ]:
        statement = select(
            Note
        ).where(
            Note.owner_employee_id
            == employee_id
        )

        if before is not None:
            statement = (
                statement.where(
                    Note.created_at
                    < before
                )
            )

        if after is not None:
            statement = (
                statement.where(
                    Note.created_at
                    >= after
                )
            )

        statement = (
            statement
            .order_by(
                Note.created_at.desc()
            )
            .limit(
                limit
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        notes = list(
            result.scalars().all()
        )

        return [
            TimelineEvent(
                event_id=(
                    "note.created:"
                    f"{note.id}"
                ),
                event_type=(
                    TimelineEventType
                    .NOTE_CREATED
                ),
                source=(
                    TimelineSourceKey
                    .NOTES
                ),
                entity_type=(
                    TimelineEntityType
                    .NOTE
                ),
                entity_id=(
                    note.id
                ),
                employee_id=(
                    employee_id
                ),
                occurred_at=(
                    note.created_at
                ),
                title=(
                    note.title
                ),
                summary=None,
                metadata={
                    "is_pinned": (
                        note.is_pinned
                    ),
                    "is_archived": (
                        note.is_archived
                    ),
                },
            )
            for note in notes
        ]


class KnowledgeTimelineSource:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def list_events(
        self,
        *,
        employee_id: uuid.UUID,
        before: datetime | None,
        after: datetime | None,
        limit: int,
    ) -> list[
        TimelineEvent
    ]:
        statement = select(
            KnowledgeEntry
        ).where(
            KnowledgeEntry
            .owner_employee_id
            == employee_id
        )

        if before is not None:
            statement = (
                statement.where(
                    KnowledgeEntry
                    .created_at
                    < before
                )
            )

        if after is not None:
            statement = (
                statement.where(
                    KnowledgeEntry
                    .created_at
                    >= after
                )
            )

        statement = (
            statement
            .order_by(
                KnowledgeEntry
                .created_at
                .desc()
            )
            .limit(
                limit
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        entries = list(
            result.scalars().all()
        )

        return [
            TimelineEvent(
                event_id=(
                    "knowledge.created:"
                    f"{entry.id}"
                ),
                event_type=(
                    TimelineEventType
                    .KNOWLEDGE_CREATED
                ),
                source=(
                    TimelineSourceKey
                    .KNOWLEDGE
                ),
                entity_type=(
                    TimelineEntityType
                    .KNOWLEDGE
                ),
                entity_id=(
                    entry.id
                ),
                employee_id=(
                    employee_id
                ),
                occurred_at=(
                    entry.created_at
                ),
                title=(
                    entry.title
                ),
                summary=None,
                metadata={
                    "category": (
                        enum_string_value(
                            entry.category
                        )
                    ),
                    "status": (
                        enum_string_value(
                            entry.status
                        )
                    ),
                    "visibility": (
                        enum_string_value(
                            entry.visibility
                        )
                    ),
                },
            )
            for entry in entries
        ]


class MeetingTimelineSource:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def list_events(
        self,
        *,
        employee_id: uuid.UUID,
        before: datetime | None,
        after: datetime | None,
        limit: int,
    ) -> list[
        TimelineEvent
    ]:
        statement = (
            select(
                Meeting
            )
            .join(
                MeetingParticipant,
                (
                    MeetingParticipant
                    .meeting_id
                    == Meeting.id
                ),
            )
            .where(
                MeetingParticipant
                .employee_id
                == employee_id
            )
        )

        if before is not None:
            statement = (
                statement.where(
                    Meeting
                    .scheduled_start_at
                    < before
                )
            )

        if after is not None:
            statement = (
                statement.where(
                    Meeting
                    .scheduled_start_at
                    >= after
                )
            )

        statement = (
            statement
            .order_by(
                Meeting
                .scheduled_start_at
                .desc()
            )
            .limit(
                limit
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        meetings = list(
            result.scalars().all()
        )

        return [
            TimelineEvent(
                event_id=(
                    "meeting.scheduled:"
                    f"{meeting.id}"
                ),
                event_type=(
                    TimelineEventType
                    .MEETING_SCHEDULED
                ),
                source=(
                    TimelineSourceKey
                    .MEETINGS
                ),
                entity_type=(
                    TimelineEntityType
                    .MEETING
                ),
                entity_id=(
                    meeting.id
                ),
                employee_id=(
                    employee_id
                ),
                occurred_at=(
                    meeting
                    .scheduled_start_at
                ),
                title=(
                    meeting.title
                ),
                summary=(
                    meeting.description
                ),
                metadata={
                    "meeting_type": (
                        enum_string_value(
                            meeting
                            .meeting_type
                        )
                    ),
                    "status": (
                        enum_string_value(
                            meeting.status
                        )
                    ),
                    "scheduled_end_at": (
                        meeting
                        .scheduled_end_at
                        .isoformat()
                        if (
                            meeting
                            .scheduled_end_at
                            is not None
                        )
                        else None
                    ),
                },
            )
            for meeting
            in meetings
        ]


class AttendanceTimelineSource:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def list_events(
        self,
        *,
        employee_id: uuid.UUID,
        before: datetime | None,
        after: datetime | None,
        limit: int,
    ) -> list[
        TimelineEvent
    ]:
        statement = select(
            AttendanceEvent
        ).where(
            AttendanceEvent.employee_id
            == employee_id
        )

        if before is not None:
            statement = (
                statement.where(
                    AttendanceEvent
                    .occurred_at
                    < before
                )
            )

        if after is not None:
            statement = (
                statement.where(
                    AttendanceEvent
                    .occurred_at
                    >= after
                )
            )

        statement = (
            statement
            .order_by(
                AttendanceEvent
                .occurred_at
                .desc(),
                AttendanceEvent
                .id
                .desc(),
            )
            .limit(
                limit
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        attendance_events = list(
            result.scalars().all()
        )

        items: list[
            TimelineEvent
        ] = []

        for event in attendance_events:
            try:
                timeline_event_type = (
                    attendance_timeline_event_type(
                        event.event_type
                    )
                )

                title = (
                    attendance_timeline_title(
                        event.event_type
                    )
                )

            except ValueError:
                # Forward compatibility:
                # skip unknown future attendance
                # event values instead of breaking
                # the complete timeline.
                continue

            items.append(
                TimelineEvent(
                    event_id=(
                        "attendance:"
                        f"{event.id}"
                    ),
                    event_type=(
                        timeline_event_type
                    ),
                    source=(
                        TimelineSourceKey
                        .ATTENDANCE
                    ),
                    entity_type=(
                        TimelineEntityType
                        .ATTENDANCE_EVENT
                    ),
                    entity_id=(
                        event.id
                    ),
                    employee_id=(
                        employee_id
                    ),
                    occurred_at=(
                        event.occurred_at
                    ),
                    title=(
                        title
                    ),
                    summary=None,
                    metadata={
                        "attendance_record_id": (
                            str(
                                event
                                .attendance_record_id
                            )
                        ),
                        "attendance_event_type": (
                            enum_string_value(
                                event.event_type
                            )
                        ),
                        "source": (
                            enum_string_value(
                                event.source
                            )
                        ),
                    },
                )
            )

        return items


class ScreenshotTimelineSource:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    @staticmethod
    def _event_type(
        status: str,
    ) -> TimelineEventType:
        mapping = {
            SCREENSHOT_STATUS_PENDING: (
                TimelineEventType
                .SCREENSHOT_REQUESTED
            ),
            SCREENSHOT_STATUS_COMPLETED: (
                TimelineEventType
                .SCREENSHOT_COMPLETED
            ),
            SCREENSHOT_STATUS_DENIED: (
                TimelineEventType
                .SCREENSHOT_DENIED
            ),
            SCREENSHOT_STATUS_EXPIRED: (
                TimelineEventType
                .SCREENSHOT_EXPIRED
            ),
            SCREENSHOT_STATUS_FAILED: (
                TimelineEventType
                .SCREENSHOT_FAILED
            ),
        }

        return mapping.get(
            status,
            TimelineEventType
            .SCREENSHOT_REQUESTED,
        )

    @staticmethod
    def _title(
        status: str,
    ) -> str:
        titles = {
            SCREENSHOT_STATUS_PENDING: (
                "Screenshot requested"
            ),
            SCREENSHOT_STATUS_COMPLETED: (
                "Screenshot completed"
            ),
            SCREENSHOT_STATUS_DENIED: (
                "Screenshot denied"
            ),
            SCREENSHOT_STATUS_EXPIRED: (
                "Screenshot expired"
            ),
            SCREENSHOT_STATUS_FAILED: (
                "Screenshot failed"
            ),
        }

        return titles.get(
            status,
            "Screenshot event",
        )

    async def list_events(
        self,
        *,
        employee_id: uuid.UUID,
        before: datetime | None,
        after: datetime | None,
        limit: int,
    ) -> list[
        TimelineEvent
    ]:
        statement = (
            select(
                ScreenshotCaptureRequest
            )
            .where(
                ScreenshotCaptureRequest
                .employee_id
                == employee_id
            )
        )

        if before is not None:
            statement = (
                statement.where(
                    ScreenshotCaptureRequest
                    .requested_at
                    < before
                )
            )

        if after is not None:
            statement = (
                statement.where(
                    ScreenshotCaptureRequest
                    .requested_at
                    >= after
                )
            )

        statement = (
            statement
            .order_by(
                ScreenshotCaptureRequest
                .requested_at
                .desc(),
                ScreenshotCaptureRequest
                .id
                .desc(),
            )
            .limit(
                limit
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        screenshots = list(
            result.scalars().all()
        )

        items: list[
            TimelineEvent
        ] = []

        for screenshot in screenshots:
            occurred_at = (
                screenshot.completed_at
                if (
                    screenshot.completed_at
                    is not None
                    and screenshot.status
                    != SCREENSHOT_STATUS_PENDING
                )
                else screenshot.requested_at
            )

            items.append(
                TimelineEvent(
                    event_id=(
                        "screenshot:"
                        f"{screenshot.status}:"
                        f"{screenshot.id}"
                    ),
                    event_type=(
                        self._event_type(
                            screenshot.status
                        )
                    ),
                    source=(
                        TimelineSourceKey
                        .SCREENSHOTS
                    ),
                    entity_type=(
                        TimelineEntityType
                        .SCREENSHOT_CAPTURE
                    ),
                    entity_id=(
                        screenshot.id
                    ),
                    employee_id=(
                        employee_id
                    ),
                    occurred_at=(
                        occurred_at
                    ),
                    title=(
                        self._title(
                            screenshot.status
                        )
                    ),
                    summary=(
                        screenshot.reason
                    ),
                    metadata={
                        "device_id": (
                            screenshot
                            .device_id
                        ),
                        "status": (
                            screenshot.status
                        ),
                        "width": (
                            screenshot.width
                        ),
                        "height": (
                            screenshot.height
                        ),
                        "consent_required": (
                            screenshot
                            .consent_required
                        ),
                        "visible_indicator_required": (
                            screenshot
                            .visible_indicator_required
                        ),
                    },
                )
            )

        return items


def build_default_timeline_sources(
    session: AsyncSession,
) -> list[
    TimelineSource
]:
    return [
        GoalTimelineSource(
            session
        ),
        NoteTimelineSource(
            session
        ),
        KnowledgeTimelineSource(
            session
        ),
        MeetingTimelineSource(
            session
        ),
        AttendanceTimelineSource(
            session
        ),
        ScreenshotTimelineSource(
            session
        ),
    ]


__all__ = [
    "TimelineSource",
    "GoalTimelineSource",
    "NoteTimelineSource",
    "KnowledgeTimelineSource",
    "MeetingTimelineSource",
    "AttendanceTimelineSource",
    "ScreenshotTimelineSource",
    "build_default_timeline_sources",
]