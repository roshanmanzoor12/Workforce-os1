from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.models import (
    Employee,
)
from app.modules.goals.schemas import (
    GoalCreateRequest,
    GoalListResponse,
    GoalPublic,
    GoalUpdateRequest,
)
from app.modules.goals.service import (
    GoalNotFoundError,
    GoalService,
    GoalValidationError,
)


class GoalActorEmployeeNotFoundError(
    LookupError
):
    pass


class GoalSelfService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.goals = GoalService(
            session
        )

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
                GoalActorEmployeeNotFoundError(
                    "Active employee profile "
                    "for current user was "
                    "not found."
                )
            )

        return employee

    async def create_my_goal(
        self,
        actor_user_id: uuid.UUID,
        request: GoalCreateRequest,
    ) -> GoalPublic:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        trusted_request = (
            GoalCreateRequest(
                owner_employee_id=(
                    employee.id
                ),
                title=request.title,
                description=(
                    request.description
                ),
                priority=request.priority,
                start_date=(
                    request.start_date
                ),
                due_date=request.due_date,
            )
        )

        return await (
            self.goals.create_goal(
                trusted_request
            )
        )

    async def list_my_goals(
        self,
        actor_user_id: uuid.UUID,
    ) -> GoalListResponse:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        return await (
            self.goals
            .list_employee_goals(
                employee.id
            )
        )

    async def get_my_goal(
        self,
        actor_user_id: uuid.UUID,
        goal_id: uuid.UUID,
    ) -> GoalPublic:
        employee = await (
            self.resolve_actor_employee(
                actor_user_id
            )
        )

        goal = await (
            self.goals.get_goal(
                goal_id
            )
        )

        if (
            goal.owner_employee_id
            != employee.id
        ):
            raise GoalNotFoundError(
                "Goal not found."
            )

        return goal

    async def update_my_goal(
        self,
        actor_user_id: uuid.UUID,
        goal_id: uuid.UUID,
        request: GoalUpdateRequest,
    ) -> GoalPublic:
        await self.get_my_goal(
            actor_user_id,
            goal_id,
        )

        return await (
            self.goals.update_goal(
                goal_id,
                request,
            )
        )

    async def delete_my_goal(
        self,
        actor_user_id: uuid.UUID,
        goal_id: uuid.UUID,
    ) -> None:
        await self.get_my_goal(
            actor_user_id,
            goal_id,
        )

        await self.goals.delete_goal(
            goal_id
        )


__all__ = [
    "GoalSelfService",
    "GoalActorEmployeeNotFoundError",
    "GoalNotFoundError",
    "GoalValidationError",
]