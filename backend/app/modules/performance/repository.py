from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.performance.models import (
    PerformanceReview,
    PerformanceReviewCycle,
)


class PerformanceRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def add_cycle(
        self,
        value: PerformanceReviewCycle,
    ) -> PerformanceReviewCycle:
        self.session.add(value)
        await self.session.flush()
        return value

    async def add_review(
        self,
        value: PerformanceReview,
    ) -> PerformanceReview:
        self.session.add(value)
        await self.session.flush()
        return value

    async def list_reviews(
        self,
        employee_id: uuid.UUID | None = None,
    ) -> list[PerformanceReview]:
        statement = select(
            PerformanceReview
        ).order_by(
            PerformanceReview.created_at.desc()
        )

        if employee_id is not None:
            statement = statement.where(
                PerformanceReview.employee_id
                == employee_id
            )

        result = await self.session.scalars(
            statement
        )

        return list(result.all())


__all__ = [
    "PerformanceRepository",
]