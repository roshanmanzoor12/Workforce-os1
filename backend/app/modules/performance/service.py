from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.performance.models import (
    PerformanceReview,
    PerformanceReviewCycle,
)
from app.modules.performance.repository import (
    PerformanceRepository,
)
from app.modules.performance.schemas import (
    ReviewCreate,
    ReviewCycleCreate,
)


class PerformanceService:
    def __init__(
        self,
        session: AsyncSession,
        reviewer_user_id: uuid.UUID,
    ) -> None:
        self.session = session
        self.reviewer_user_id = reviewer_user_id
        self.repository = PerformanceRepository(
            session
        )

    async def create_cycle(
        self,
        request: ReviewCycleCreate,
    ) -> PerformanceReviewCycle:
        cycle = PerformanceReviewCycle(
            name=request.name,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        await self.repository.add_cycle(cycle)
        await self.session.commit()
        await self.session.refresh(cycle)

        return cycle

    async def create_review(
        self,
        request: ReviewCreate,
    ) -> PerformanceReview:
        review = PerformanceReview(
            cycle_id=request.cycle_id,
            employee_id=request.employee_id,
            reviewer_user_id=self.reviewer_user_id,
            rating=request.rating,
            strengths=request.strengths,
            improvements=request.improvements,
            feedback=request.feedback,
        )

        await self.repository.add_review(review)
        await self.session.commit()
        await self.session.refresh(review)

        return review

    async def list_reviews(
        self,
        employee_id: uuid.UUID | None = None,
    ) -> dict[str, object]:
        reviews = await self.repository.list_reviews(
            employee_id
        )

        return {
            "items": reviews,
            "total": len(reviews),
        }


__all__ = [
    "PerformanceService",
]