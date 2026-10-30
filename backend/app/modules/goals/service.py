from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.goals.enums import (
    GoalStatus,
)
from app.modules.goals.models import Goal
from app.modules.goals.repository import (
    GoalRepository,
)
from app.modules.goals.schemas import (
    GoalCreateRequest,
    GoalListResponse,
    GoalPublic,
    GoalUpdateRequest,
)


class GoalNotFoundError(
    LookupError
):
    pass


class GoalValidationError(
    ValueError
):
    pass


class GoalService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            GoalRepository(
                session
            )
        )

        self.employees = (
            EmployeeRepository(
                session
            )
        )

    async def create_goal(
        self,
        request: GoalCreateRequest,
    ) -> GoalPublic:
        employee = await (
            self.employees
            .get_employee_by_id(
                request.owner_employee_id
            )
        )

        if employee is None:
            raise GoalValidationError(
                "Employee not found."
            )

        if not employee.is_active:
            raise GoalValidationError(
                "Employee is not active."
            )

        goal = Goal(
            owner_employee_id=(
                request.owner_employee_id
            ),
            title=request.title,
            description=request.description,
            priority=request.priority.value,
            status=(
                GoalStatus.ACTIVE.value
            ),
            progress_percent=0,
            start_date=request.start_date,
            due_date=request.due_date,
        )

        try:
            await self.repository.create(
                goal
            )

            await self.session.commit()

            await self.session.refresh(
                goal
            )
        except Exception:
            await self.session.rollback()
            raise

        return self._to_public(
            goal
        )

    async def get_goal(
        self,
        goal_id: uuid.UUID,
    ) -> GoalPublic:
        goal = await self._require_goal(
            goal_id
        )

        return self._to_public(
            goal
        )

    async def list_employee_goals(
        self,
        employee_id: uuid.UUID,
    ) -> GoalListResponse:
        goals = await (
            self.repository
            .list_for_employee(
                employee_id
            )
        )

        items = [
            self._to_public(
                goal
            )
            for goal in goals
        ]

        return GoalListResponse(
            items=items,
            total=len(items),
        )

    async def update_goal(
        self,
        goal_id: uuid.UUID,
        request: GoalUpdateRequest,
    ) -> GoalPublic:
        goal = await self._require_goal(
            goal_id
        )

        values = request.model_dump(
            exclude_unset=True
        )

        if "priority" in values:
            values["priority"] = (
                values["priority"].value
            )

        if "status" in values:
            values["status"] = (
                values["status"].value
            )

        for key, value in values.items():
            setattr(
                goal,
                key,
                value,
            )

        if (
            goal.status
            == GoalStatus.COMPLETED.value
        ):
            goal.progress_percent = 100

            if goal.completed_at is None:
                goal.completed_at = (
                    datetime.now(
                        timezone.utc
                    )
                )
        else:
            goal.completed_at = None

        if (
            goal.start_date is not None
            and goal.due_date is not None
            and goal.due_date
            < goal.start_date
        ):
            raise GoalValidationError(
                "due_date cannot be before "
                "start_date"
            )

        try:
            await self.session.commit()

            await self.session.refresh(
                goal
            )
        except Exception:
            await self.session.rollback()
            raise

        return self._to_public(
            goal
        )

    async def delete_goal(
        self,
        goal_id: uuid.UUID,
    ) -> None:
        goal = await self._require_goal(
            goal_id
        )

        try:
            await self.repository.delete(
                goal
            )

            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def _require_goal(
        self,
        goal_id: uuid.UUID,
    ) -> Goal:
        goal = await (
            self.repository
            .get_by_id(
                goal_id
            )
        )

        if goal is None:
            raise GoalNotFoundError(
                "Goal not found."
            )

        return goal

    @staticmethod
    def _to_public(
        goal: Goal,
    ) -> GoalPublic:
        return GoalPublic.model_validate(
            goal
        )


__all__ = [
    "GoalService",
    "GoalNotFoundError",
    "GoalValidationError",
]