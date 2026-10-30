from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.employees.models import (
    Employee,
)
from app.modules.timeline.cursor import (
    TimelineCursor,
    TimelineCursorError,
    decode_timeline_cursor,
    encode_timeline_cursor,
)
from app.modules.timeline.enums import (
    TimelineEventType,
    TimelineSourceKey,
)
from app.modules.timeline.query import (
    TimelineQuery,
)
from app.modules.timeline.registry import (
    TimelineSourceRegistry,
)
from app.modules.timeline.schemas import (
    TimelineCapabilities,
    TimelineEvent,
    TimelineResponse,
)
from app.modules.timeline.security import (
    sanitize_timeline_metadata,
)


class TimelineEmployeeNotFoundError(
    LookupError
):
    pass


class TimelineValidationError(
    ValueError
):
    pass


class TimelineService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.registry = (
            TimelineSourceRegistry(
                session
            )
        )

    async def resolve_actor_employee(
        self,
        actor_user_id: uuid.UUID,
    ) -> Employee:
        result = await (
            self.session.execute(
                select(
                    Employee
                ).where(
                    Employee.user_id
                    == actor_user_id,
                    Employee.is_active.is_(
                        True
                    ),
                )
            )
        )

        employee = (
            result.scalar_one_or_none()
        )

        if employee is None:
            raise (
                TimelineEmployeeNotFoundError(
                    "Active employee profile "
                    "for current user was "
                    "not found."
                )
            )

        return employee

    async def require_employee(
        self,
        employee_id: uuid.UUID,
    ) -> Employee:
        result = await (
            self.session.execute(
                select(
                    Employee
                ).where(
                    Employee.id
                    == employee_id,
                    Employee.is_active.is_(
                        True
                    ),
                )
            )
        )

        employee = (
            result.scalar_one_or_none()
        )

        if employee is None:
            raise (
                TimelineEmployeeNotFoundError(
                    "Active employee was "
                    "not found."
                )
            )

        return employee

    async def list_my_timeline(
        self,
        *,
        actor_user_id: uuid.UUID,
        before: datetime | None,
        after: datetime | None,
        limit: int,
        sources: frozenset[
            TimelineSourceKey
        ],
        event_types: frozenset[
            TimelineEventType
        ],
        cursor: str | None,
    ) -> TimelineResponse:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        query = TimelineQuery(
            before=before,
            after=after,
            limit=limit,
            sources=sources,
            event_types=event_types,
            cursor=cursor,
        )

        return await (
            self.list_timeline_query(
                employee_id=(
                    employee.id
                ),
                query=query,
            )
        )

    async def list_timeline(
        self,
        *,
        employee_id: uuid.UUID,
        before: datetime | None,
        after: datetime | None,
        limit: int,
        sources: frozenset[
            TimelineSourceKey
        ],
        event_types: frozenset[
            TimelineEventType
        ],
        cursor: str | None,
    ) -> TimelineResponse:
        query = TimelineQuery(
            before=before,
            after=after,
            limit=limit,
            sources=sources,
            event_types=event_types,
            cursor=cursor,
        )

        return await (
            self.list_timeline_query(
                employee_id=(
                    employee_id
                ),
                query=query,
            )
        )

    async def list_timeline_query(
        self,
        *,
        employee_id: uuid.UUID,
        query: TimelineQuery,
    ) -> TimelineResponse:
        try:
            query.validate()

        except ValueError as exc:
            raise TimelineValidationError(
                str(exc)
            ) from exc

        decoded_cursor = None

        if query.cursor is not None:
            try:
                decoded_cursor = (
                    decode_timeline_cursor(
                        query.cursor
                    )
                )

            except TimelineCursorError as exc:
                raise TimelineValidationError(
                    str(exc)
                ) from exc

        await self.require_employee(
            employee_id
        )

        selected_sources = (
            self.registry.selected(
                query.sources
            )
        )

        fetch_limit = min(
            max(
                query.limit * 5,
                100,
            ),
            500,
        )

        # =================================================
        # IMPORTANT
        # =================================================
        #
        # All timeline sources share this AsyncSession.
        #
        # SQLAlchemy AsyncSession does not support concurrent
        # operations from asyncio.gather() on the same session.
        #
        # Query each source sequentially.
        # =================================================

        batches: list[
            list[
                TimelineEvent
            ]
        ] = []

        for registered in selected_sources:
            batch = await (
                registered.source
                .list_events(
                    employee_id=(
                        employee_id
                    ),
                    before=(
                        query.before
                    ),
                    after=(
                        query.after
                    ),
                    limit=(
                        fetch_limit
                    ),
                )
            )

            batches.append(
                batch
            )

        events: list[
            TimelineEvent
        ] = []

        for batch in batches:
            for event in batch:
                if (
                    query.event_types
                    and event.event_type
                    not in query.event_types
                ):
                    continue

                if (
                    decoded_cursor
                    is not None
                    and not (
                        self._comes_after_cursor(
                            event,
                            decoded_cursor,
                        )
                    )
                ):
                    continue

                events.append(
                    self._sanitize_event(
                        event
                    )
                )

        events.sort(
            key=self._sort_key,
            reverse=True,
        )

        has_more = (
            len(events)
            > query.limit
        )

        items = events[
            :query.limit
        ]

        next_cursor = None

        if (
            has_more
            and items
        ):
            last = items[
                -1
            ]

            next_cursor = (
                encode_timeline_cursor(
                    TimelineCursor(
                        occurred_at=(
                            last.occurred_at
                        ),
                        event_id=(
                            last.event_id
                        ),
                    )
                )
            )

        applied_sources = (
            sorted(
                query.sources,
                key=lambda item: (
                    item.value
                ),
            )
            if query.sources
            else []
        )

        applied_event_types = (
            sorted(
                query.event_types,
                key=lambda item: (
                    item.value
                ),
            )
            if query.event_types
            else []
        )

        return TimelineResponse(
            employee_id=employee_id,
            items=items,
            total=len(
                items
            ),
            limit=query.limit,
            before=query.before,
            after=query.after,
            next_cursor=next_cursor,
            has_more=has_more,
            applied_sources=(
                applied_sources
            ),
            applied_event_types=(
                applied_event_types
            ),
        )

    @staticmethod
    def _sanitize_event(
        event: TimelineEvent,
    ) -> TimelineEvent:
        return event.model_copy(
            update={
                "metadata": (
                    sanitize_timeline_metadata(
                        event.metadata
                    )
                )
            }
        )

    @staticmethod
    def _sort_key(
        event: TimelineEvent,
    ) -> tuple[
        datetime,
        str,
    ]:
        return (
            event.occurred_at,
            event.event_id,
        )

    @staticmethod
    def _comes_after_cursor(
        event: TimelineEvent,
        cursor: TimelineCursor,
    ) -> bool:
        if (
            event.occurred_at
            < cursor.occurred_at
        ):
            return True

        if (
            event.occurred_at
            > cursor.occurred_at
        ):
            return False

        return (
            event.event_id
            < cursor.event_id
        )

    @staticmethod
    def capabilities(
    ) -> TimelineCapabilities:
        return TimelineCapabilities(
            sources=[
                source_key
                for source_key
                in TimelineSourceKey
            ],
            event_types=[
                event_type
                for event_type
                in TimelineEventType
            ],
        )


__all__ = [
    "TimelineEmployeeNotFoundError",
    "TimelineValidationError",
    "TimelineService",
]