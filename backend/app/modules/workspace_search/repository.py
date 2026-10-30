from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import (
    or_,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.employees.models import (
    Employee,
)
from app.modules.goals.models import (
    Goal,
)
from app.modules.knowledge.models import (
    KnowledgeEntry,
)
from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)
from app.modules.notes.models import (
    Note,
)
from app.modules.workspace_search.access import (
    SearchAccess,
)
from app.modules.workspace_search.enums import (
    SearchEntityType,
)


@dataclass(
    frozen=True,
    slots=True,
)
class SearchCandidate:
    entity_type: SearchEntityType

    entity_id: uuid.UUID

    title: str

    subtitle: str | None

    searchable_fields: tuple[
        tuple[
            str,
            str | None,
            float,
        ],
        ...
    ]

    resource_path: str


class WorkspaceSearchRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    @staticmethod
    def _pattern(
        query: str,
    ) -> str:
        escaped = (
            query
            .replace(
                "\\",
                "\\\\",
            )
            .replace(
                "%",
                "\\%",
            )
            .replace(
                "_",
                "\\_",
            )
        )

        return (
            "%"
            + escaped
            + "%"
        )

    @staticmethod
    def _apply_employee_scope(
        statement,
        *,
        column,
        access: SearchAccess,
    ):
        if access.employee_ids is None:
            return statement

        if not access.employee_ids:
            return statement.where(
                column.in_(
                    []
                )
            )

        return statement.where(
            column.in_(
                tuple(
                    access.employee_ids
                )
            )
        )

    # =====================================================
    # EMPLOYEES
    # =====================================================

    async def employees(
        self,
        *,
        query: str,
        access: SearchAccess,
        limit: int,
    ) -> list[
        SearchCandidate
    ]:
        if not access.can_search_employees:
            return []

        pattern = self._pattern(
            query
        )

        statement = (
            select(
                Employee
            )
            .where(
                Employee.is_active.is_(
                    True
                ),
                or_(
                    Employee.first_name.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Employee.last_name.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Employee.work_email.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Employee.job_title.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Employee.employee_code.ilike(
                        pattern,
                        escape="\\",
                    ),
                ),
            )
            .order_by(
                Employee.first_name.asc(),
                Employee.last_name.asc(),
            )
            .limit(
                limit
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                column=Employee.id,
                access=access,
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        employees = list(
            result
            .scalars()
            .all()
        )

        items: list[
            SearchCandidate
        ] = []

        for employee in employees:
            full_name = (
                f"{employee.first_name} "
                f"{employee.last_name}"
            ).strip()

            subtitle_parts = [
                value
                for value in (
                    employee.job_title,
                    employee.work_email,
                )
                if value
            ]

            subtitle = (
                " • ".join(
                    subtitle_parts
                )
                if subtitle_parts
                else None
            )

            items.append(
                SearchCandidate(
                    entity_type=(
                        SearchEntityType
                        .EMPLOYEE
                    ),
                    entity_id=employee.id,
                    title=full_name,
                    subtitle=subtitle,
                    searchable_fields=(
                        (
                            "name",
                            full_name,
                            1.30,
                        ),
                        (
                            "email",
                            employee.work_email,
                            1.10,
                        ),
                        (
                            "job_title",
                            employee.job_title,
                            0.90,
                        ),
                        (
                            "employee_code",
                            employee.employee_code,
                            1.00,
                        ),
                    ),
                    resource_path=(
                        "/employees/"
                        f"{employee.id}"
                    ),
                )
            )

        return items

    # =====================================================
    # GOALS
    # =====================================================

    async def goals(
        self,
        *,
        query: str,
        access: SearchAccess,
        limit: int,
    ) -> list[
        SearchCandidate
    ]:
        if not access.can_search_goals:
            return []

        pattern = self._pattern(
            query
        )

        statement = (
            select(
                Goal
            )
            .where(
                or_(
                    Goal.title.ilike(
                        pattern,
                        escape="\\",
                    ),
                    Goal.description.ilike(
                        pattern,
                        escape="\\",
                    ),
                )
            )
            .order_by(
                Goal.created_at.desc()
            )
            .limit(
                limit
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                column=(
                    Goal.owner_employee_id
                ),
                access=access,
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        goals = list(
            result
            .scalars()
            .all()
        )

        return [
            SearchCandidate(
                entity_type=(
                    SearchEntityType.GOAL
                ),
                entity_id=goal.id,
                title=goal.title,
                subtitle=(
                    f"{goal.status} • "
                    f"{goal.progress_percent}%"
                ),
                searchable_fields=(
                    (
                        "title",
                        goal.title,
                        1.30,
                    ),
                    (
                        "description",
                        goal.description,
                        0.80,
                    ),
                ),
                resource_path=(
                    "/goals/"
                    f"{goal.id}"
                ),
            )
            for goal in goals
        ]

    # =====================================================
    # NOTES
    # =====================================================

    async def notes(
        self,
        *,
        query: str,
        access: SearchAccess,
        limit: int,
    ) -> list[
        SearchCandidate
    ]:
        if not access.can_search_notes:
            return []

        pattern = self._pattern(
            query
        )

        statement = (
            select(
                Note
            )
            .where(
                Note.title.ilike(
                    pattern,
                    escape="\\",
                )
            )
            .order_by(
                Note.created_at.desc()
            )
            .limit(
                limit
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                column=(
                    Note.owner_employee_id
                ),
                access=access,
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        notes = list(
            result
            .scalars()
            .all()
        )

        return [
            SearchCandidate(
                entity_type=(
                    SearchEntityType.NOTE
                ),
                entity_id=note.id,
                title=note.title,
                subtitle=(
                    "Pinned"
                    if getattr(
                        note,
                        "is_pinned",
                        False,
                    )
                    else None
                ),
                searchable_fields=(
                    (
                        "title",
                        note.title,
                        1.30,
                    ),
                ),
                resource_path=(
                    "/notes/"
                    f"{note.id}"
                ),
            )
            for note in notes
        ]

    # =====================================================
    # KNOWLEDGE
    # =====================================================

    async def knowledge(
        self,
        *,
        query: str,
        access: SearchAccess,
        limit: int,
    ) -> list[
        SearchCandidate
    ]:
        if not access.can_search_knowledge:
            return []

        pattern = self._pattern(
            query
        )

        statement = (
            select(
                KnowledgeEntry
            )
            .where(
                KnowledgeEntry.title.ilike(
                    pattern,
                    escape="\\",
                )
            )
            .order_by(
                KnowledgeEntry
                .created_at
                .desc()
            )
            .limit(
                limit
            )
        )

        statement = (
            self._apply_employee_scope(
                statement,
                column=(
                    KnowledgeEntry
                    .owner_employee_id
                ),
                access=access,
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        entries = list(
            result
            .scalars()
            .all()
        )

        items: list[
            SearchCandidate
        ] = []

        for entry in entries:
            status = getattr(
                entry,
                "status",
                None,
            )

            visibility = getattr(
                entry,
                "visibility",
                None,
            )

            subtitle_parts = [
                str(value)
                for value in (
                    status,
                    visibility,
                )
                if value is not None
            ]

            items.append(
                SearchCandidate(
                    entity_type=(
                        SearchEntityType
                        .KNOWLEDGE
                    ),
                    entity_id=entry.id,
                    title=entry.title,
                    subtitle=(
                        " • ".join(
                            subtitle_parts
                        )
                        if subtitle_parts
                        else None
                    ),
                    searchable_fields=(
                        (
                            "title",
                            entry.title,
                            1.30,
                        ),
                    ),
                    resource_path=(
                        "/knowledge/"
                        f"{entry.id}"
                    ),
                )
            )

        return items

    # =====================================================
    # MEETINGS
    # =====================================================

    async def meetings(
        self,
        *,
        query: str,
        access: SearchAccess,
        limit: int,
    ) -> list[
        SearchCandidate
    ]:
        if not access.can_search_meetings:
            return []

        pattern = self._pattern(
            query
        )

        if access.can_search_all_meetings:
            statement = (
                select(
                    Meeting
                )
                .where(
                    Meeting.title.ilike(
                        pattern,
                        escape="\\",
                    )
                )
            )

        else:
            if (
                access.actor_employee_id
                is None
            ):
                return []

            statement = (
                select(
                    Meeting
                )
                .join(
                    MeetingParticipant,
                    MeetingParticipant
                    .meeting_id
                    == Meeting.id,
                )
                .where(
                    MeetingParticipant
                    .employee_id
                    == (
                        access
                        .actor_employee_id
                    ),
                    Meeting.title.ilike(
                        pattern,
                        escape="\\",
                    ),
                )
                .distinct()
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
            result
            .scalars()
            .all()
        )

        return [
            SearchCandidate(
                entity_type=(
                    SearchEntityType
                    .MEETING
                ),
                entity_id=meeting.id,
                title=meeting.title,
                subtitle=(
                    meeting
                    .scheduled_start_at
                    .isoformat()
                    if (
                        meeting
                        .scheduled_start_at
                        is not None
                    )
                    else None
                ),
                searchable_fields=(
                    (
                        "title",
                        meeting.title,
                        1.30,
                    ),
                ),
                resource_path=(
                    "/meetings/"
                    f"{meeting.id}"
                ),
            )
            for meeting in meetings
        ]


__all__ = [
    "SearchCandidate",
    "WorkspaceSearchRepository",
]