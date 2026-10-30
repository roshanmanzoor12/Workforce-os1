from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_productivity.enums import (
    AIProductivitySource,
)
from app.modules.ai_productivity.schemas import (
    AIContextItem,
    AIProductivityContext,
)
from app.modules.employees.models import (
    Employee,
)
from app.modules.goals.models import Goal
from app.modules.knowledge.models import (
    KnowledgeEntry,
)
from app.modules.notes.models import Note


class AIActorEmployeeNotFoundError(
    LookupError
):
    pass


class AIProductivityContextService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def resolve_actor_employee(
        self,
        actor_user_id: uuid.UUID,
    ) -> Employee:
        result = await self.session.execute(
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

        employee = (
            result.scalar_one_or_none()
        )

        if employee is None:
            raise (
                AIActorEmployeeNotFoundError(
                    "Active employee profile "
                    "for current user was not found."
                )
            )

        return employee

    async def build_context(
        self,
        *,
        actor_user_id: uuid.UUID,
        sources: list[
            AIProductivitySource
        ],
        max_items_per_source: int,
    ) -> AIProductivityContext:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        items: list[
            AIContextItem
        ] = []

        unique_sources = list(
            dict.fromkeys(
                sources
            )
        )

        if (
            AIProductivitySource.GOALS
            in unique_sources
        ):
            items.extend(
                await self._goal_items(
                    employee.id,
                    max_items_per_source,
                )
            )

        if (
            AIProductivitySource.NOTES
            in unique_sources
        ):
            items.extend(
                await self._note_items(
                    employee.id,
                    max_items_per_source,
                )
            )

        if (
            AIProductivitySource.KNOWLEDGE
            in unique_sources
        ):
            items.extend(
                await self._knowledge_items(
                    employee.id,
                    max_items_per_source,
                )
            )

        return AIProductivityContext(
            employee_id=employee.id,
            items=items,
            total_items=len(items),
        )

    async def _goal_items(
        self,
        employee_id: uuid.UUID,
        limit: int,
    ) -> list[AIContextItem]:
        result = await self.session.execute(
            select(
                Goal
            )
            .where(
                Goal.owner_employee_id
                == employee_id,
                Goal.status
                != "archived",
            )
            .order_by(
                Goal.updated_at.desc()
            )
            .limit(
                limit
            )
        )

        goals = list(
            result.scalars().all()
        )

        return [
            AIContextItem(
                source=(
                    AIProductivitySource
                    .GOALS
                ),
                id=goal.id,
                title=goal.title,
                content=(
                    self._goal_content(
                        goal
                    )
                ),
            )
            for goal in goals
        ]

    async def _note_items(
        self,
        employee_id: uuid.UUID,
        limit: int,
    ) -> list[AIContextItem]:
        result = await self.session.execute(
            select(
                Note
            )
            .where(
                Note.owner_employee_id
                == employee_id,
                Note.is_archived.is_(
                    False
                ),
            )
            .order_by(
                Note.updated_at.desc()
            )
            .limit(
                limit
            )
        )

        notes = list(
            result.scalars().all()
        )

        return [
            AIContextItem(
                source=(
                    AIProductivitySource
                    .NOTES
                ),
                id=note.id,
                title=note.title,
                content=note.content,
            )
            for note in notes
        ]

    async def _knowledge_items(
        self,
        employee_id: uuid.UUID,
        limit: int,
    ) -> list[AIContextItem]:
        result = await self.session.execute(
            select(
                KnowledgeEntry
            )
            .where(
                KnowledgeEntry
                .owner_employee_id
                == employee_id,
                KnowledgeEntry.status
                != "archived",
            )
            .order_by(
                KnowledgeEntry
                .updated_at
                .desc()
            )
            .limit(
                limit
            )
        )

        entries = list(
            result.scalars().all()
        )

        return [
            AIContextItem(
                source=(
                    AIProductivitySource
                    .KNOWLEDGE
                ),
                id=entry.id,
                title=entry.title,
                content=entry.content,
            )
            for entry in entries
        ]

    @staticmethod
    def _goal_content(
        goal: Goal,
    ) -> str:
        pieces = [
            (
                f"Status: "
                f"{goal.status}"
            ),
            (
                f"Priority: "
                f"{goal.priority}"
            ),
            (
                f"Progress: "
                f"{goal.progress_percent}%"
            ),
        ]

        if goal.description:
            pieces.append(
                goal.description
            )

        if goal.due_date:
            pieces.append(
                (
                    "Due: "
                    f"{goal.due_date.isoformat()}"
                )
            )

        return "\n".join(
            pieces
        )


__all__ = [
    "AIProductivityContextService",
    "AIActorEmployeeNotFoundError",
]