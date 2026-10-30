from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import Field, field_validator, model_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user
from app.modules.goals.enums import GoalPriority
from app.modules.goals.schemas import (
    GoalPublic,
    GoalSchema,
    GoalUpdateRequest,
)


router = APIRouter(
    prefix="/personal/goals",
    tags=["personal-goals"],
)


class PersonalGoalCreate(GoalSchema):
    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
    )

    priority: GoalPriority = GoalPriority.MEDIUM
    start_date: date | None = None
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Title cannot be empty.")

        return value

    @model_validator(mode="after")
    def validate_dates(self) -> "PersonalGoalCreate":
        if (
            self.start_date is not None
            and self.due_date is not None
            and self.due_date < self.start_date
        ):
            raise ValueError(
                "due_date cannot be before start_date."
            )

        return self


class PersonalGoalPublic(GoalPublic):
    owner_employee_id: uuid.UUID | None = None
    owner_user_id: uuid.UUID


class PersonalGoalList(GoalSchema):
    items: list[PersonalGoalPublic]
    total: int


async def require_goal(
    session: AsyncSession,
    goal_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    lock: bool = False,
) -> dict:
    query = """
        SELECT *
        FROM personal_goals
        WHERE id = :goal_id
          AND owner_user_id = :user_id
    """

    if lock:
        query += " FOR UPDATE"

    result = await session.execute(
        text(query),
        {
            "goal_id": goal_id,
            "user_id": user_id,
        },
    )

    row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found.",
        )

    return dict(row)


@router.get(
    "",
    response_model=PersonalGoalList,
)
async def list_personal_goals(
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    result = await session.execute(
        text("""
            SELECT *
            FROM personal_goals
            WHERE owner_user_id = :user_id
            ORDER BY updated_at DESC, id DESC
        """),
        {
            "user_id": user.id,
        },
    )

    items = [
        dict(row)
        for row in result.mappings().all()
    ]

    return {
        "items": items,
        "total": len(items),
    }


@router.post(
    "",
    response_model=PersonalGoalPublic,
    status_code=201,
)
async def create_personal_goal(
    payload: PersonalGoalCreate,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    result = await session.execute(
        text("""
            INSERT INTO personal_goals (
                id,
                owner_user_id,
                title,
                description,
                priority,
                start_date,
                due_date
            )
            VALUES (
                :id,
                :owner_user_id,
                :title,
                :description,
                :priority,
                :start_date,
                :due_date
            )
            RETURNING *
        """),
        {
            "id": uuid.uuid4(),
            "owner_user_id": user.id,
            "title": payload.title,
            "description": payload.description,
            "priority": payload.priority.value,
            "start_date": payload.start_date,
            "due_date": payload.due_date,
        },
    )

    goal = dict(result.mappings().one())

    await session.commit()

    return goal


@router.get(
    "/{goal_id}",
    response_model=PersonalGoalPublic,
)
async def get_personal_goal(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    return await require_goal(
        session,
        goal_id,
        user.id,
    )


@router.patch(
    "/{goal_id}",
    response_model=PersonalGoalPublic,
)
async def update_personal_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdateRequest,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    goal = await require_goal(
        session,
        goal_id,
        user.id,
        lock=True,
    )

    changes = payload.model_dump(
        exclude_unset=True,
    )

    for field in (
        "title",
        "status",
        "priority",
        "progress_percent",
    ):
        if field in changes and changes[field] is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null.",
            )

    if "title" in changes:
        changes["title"] = changes["title"].strip()

        if not changes["title"]:
            raise HTTPException(
                status_code=422,
                detail="Title cannot be empty.",
            )

    for field in ("status", "priority"):
        if field in changes:
            changes[field] = changes[field].value

    goal.update(changes)

    if (
        goal["start_date"] is not None
        and goal["due_date"] is not None
        and goal["due_date"] < goal["start_date"]
    ):
        raise HTTPException(
            status_code=422,
            detail="due_date cannot be before start_date.",
        )

    if goal["status"] == "completed":
        goal["progress_percent"] = 100

        if goal["completed_at"] is None:
            goal["completed_at"] = datetime.now(
                timezone.utc,
            )
    else:
        goal["completed_at"] = None

    result = await session.execute(
        text("""
            UPDATE personal_goals
            SET title = :title,
                description = :description,
                status = :status,
                priority = :priority,
                progress_percent = :progress_percent,
                start_date = :start_date,
                due_date = :due_date,
                completed_at = :completed_at,
                updated_at = NOW()
            WHERE id = :goal_id
              AND owner_user_id = :user_id
            RETURNING *
        """),
        {
            "goal_id": goal_id,
            "user_id": user.id,
            "title": goal["title"],
            "description": goal["description"],
            "status": goal["status"],
            "priority": goal["priority"],
            "progress_percent": goal["progress_percent"],
            "start_date": goal["start_date"],
            "due_date": goal["due_date"],
            "completed_at": goal["completed_at"],
        },
    )

    updated = dict(result.mappings().one())

    await session.commit()

    return updated


@router.delete(
    "/{goal_id}",
    status_code=204,
)
async def delete_personal_goal(
    goal_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    result = await session.execute(
        text("""
            DELETE FROM personal_goals
            WHERE id = :goal_id
              AND owner_user_id = :user_id
            RETURNING id
        """),
        {
            "goal_id": goal_id,
            "user_id": user.id,
        },
    )

    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found.",
        )

    await session.commit()

    return Response(status_code=204)