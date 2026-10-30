from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.goals.models import Goal


class GoalRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        goal: Goal,
    ) -> Goal:
        self.session.add(goal)

        await self.session.flush()

        return goal

    async def get_by_id(
        self,
        goal_id: uuid.UUID,
    ) -> Goal | None:
        result = await self.session.execute(
            select(
                Goal
            ).where(
                Goal.id == goal_id
            )
        )

        return result.scalar_one_or_none()

    async def list_for_employee(
        self,
        employee_id: uuid.UUID,
    ) -> list[Goal]:
        result = await self.session.execute(
            select(
                Goal
            )
            .where(
                Goal.owner_employee_id
                == employee_id
            )
            .order_by(
                Goal.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    async def delete(
        self,
        goal: Goal,
    ) -> None:
        await self.session.delete(
            goal
        )

        await self.session.flush()


def get_goal_repository(
    session: AsyncSession,
) -> GoalRepository:
    return GoalRepository(
        session
    )


__all__ = [
    "GoalRepository",
    "get_goal_repository",
]