from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import (
    delete,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.shifts.models import (
    ScheduleException,
    SchedulePublication,
    SchedulePublicationStatus,
    ShiftAssignment,
    ShiftAssignmentTargetType,
    ShiftTemplate,
    ShiftWorkingDay,
)


class ShiftRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # SHIFT TEMPLATES
    # =====================================================

    async def list_shifts(
        self,
        *,
        active_only: bool = False,
    ) -> list[ShiftTemplate]:
        statement = select(
            ShiftTemplate
        )

        if active_only:
            statement = statement.where(
                ShiftTemplate.is_active.is_(
                    True
                )
            )

        statement = statement.order_by(
            ShiftTemplate.name.asc()
        )

        result = await self.session.scalars(
            statement
        )

        return list(result)

    async def get_shift(
        self,
        *,
        shift_id: uuid.UUID,
    ) -> ShiftTemplate | None:
        return await self.session.scalar(
            select(
                ShiftTemplate
            ).where(
                ShiftTemplate.id
                == shift_id
            )
        )

    async def create_shift(
        self,
        shift: ShiftTemplate,
    ) -> ShiftTemplate:
        self.session.add(
            shift
        )

        await self.session.flush()

        return shift

    # =====================================================
    # WORKING DAYS
    # =====================================================

    async def list_working_days(
        self,
        *,
        shift_id: uuid.UUID,
    ) -> list[ShiftWorkingDay]:
        result = await self.session.scalars(
            select(
                ShiftWorkingDay
            )
            .where(
                ShiftWorkingDay.shift_id
                == shift_id
            )
            .order_by(
                ShiftWorkingDay.weekday.asc()
            )
        )

        return list(result)

    async def replace_working_days(
        self,
        *,
        shift_id: uuid.UUID,
        working_days: list[
            ShiftWorkingDay
        ],
    ) -> None:
        await self.session.execute(
            delete(
                ShiftWorkingDay
            ).where(
                ShiftWorkingDay.shift_id
                == shift_id
            )
        )

        for item in working_days:
            self.session.add(
                item
            )

        await self.session.flush()

    # =====================================================
    # ASSIGNMENTS
    # =====================================================

    async def list_assignments(
        self,
        *,
        target_type: (
            ShiftAssignmentTargetType
            | None
        ) = None,
        target_id: (
            uuid.UUID | None
        ) = None,
    ) -> list[ShiftAssignment]:
        statement = select(
            ShiftAssignment
        )

        if target_type is not None:
            statement = statement.where(
                ShiftAssignment.target_type
                == target_type
            )

        if target_id is not None:
            statement = statement.where(
                ShiftAssignment.target_id
                == target_id
            )

        statement = statement.order_by(
            ShiftAssignment
            .effective_from
            .desc(),
            ShiftAssignment
            .priority
            .desc(),
        )

        result = await self.session.scalars(
            statement
        )

        return list(result)

    async def get_assignment(
        self,
        *,
        assignment_id: uuid.UUID,
    ) -> ShiftAssignment | None:
        return await self.session.scalar(
            select(
                ShiftAssignment
            ).where(
                ShiftAssignment.id
                == assignment_id
            )
        )

    async def active_assignments_for_target(
        self,
        *,
        target_type: (
            ShiftAssignmentTargetType
        ),
        target_id: uuid.UUID,
        on_date: date,
    ) -> list[ShiftAssignment]:
        result = await self.session.scalars(
            select(
                ShiftAssignment
            )
            .where(
                ShiftAssignment.target_type
                == target_type,
                ShiftAssignment.target_id
                == target_id,
                ShiftAssignment.effective_from
                <= on_date,
                or_(
                    ShiftAssignment.effective_to
                    .is_(None),
                    ShiftAssignment.effective_to
                    >= on_date,
                ),
            )
            .order_by(
                ShiftAssignment
                .priority
                .desc(),
                ShiftAssignment
                .effective_from
                .desc(),
            )
        )

        return list(result)

    async def active_assignments_for_employee(
        self,
        *,
        employee_id: uuid.UUID,
        team_id: uuid.UUID | None,
        on_date: date,
    ) -> list[ShiftAssignment]:
        """
        Load candidate assignments from both possible sources:

        - direct employee assignment
        - employee's current team assignment

        Final precedence is resolved in ShiftService.
        """

        conditions = [
            (
                ShiftAssignment.target_type
                == (
                    ShiftAssignmentTargetType
                    .EMPLOYEE
                )
            )
            & (
                ShiftAssignment.target_id
                == employee_id
            )
        ]

        if team_id is not None:
            conditions.append(
                (
                    ShiftAssignment.target_type
                    == (
                        ShiftAssignmentTargetType
                        .TEAM
                    )
                )
                & (
                    ShiftAssignment.target_id
                    == team_id
                )
            )

        result = await self.session.scalars(
            select(
                ShiftAssignment
            )
            .where(
                or_(
                    *conditions
                ),
                ShiftAssignment.effective_from
                <= on_date,
                or_(
                    ShiftAssignment.effective_to
                    .is_(None),
                    ShiftAssignment.effective_to
                    >= on_date,
                ),
            )
            .order_by(
                ShiftAssignment
                .priority
                .desc(),
                ShiftAssignment
                .effective_from
                .desc(),
            )
        )

        return list(result)

    # =====================================================
    # EXCEPTIONS
    # =====================================================

    async def list_exceptions(
        self,
        *,
        employee_id: (
            uuid.UUID | None
        ) = None,
        start_date: (
            date | None
        ) = None,
        end_date: (
            date | None
        ) = None,
    ) -> list[ScheduleException]:
        statement = select(
            ScheduleException
        )

        if employee_id is not None:
            statement = statement.where(
                ScheduleException.employee_id
                == employee_id
            )

        if start_date is not None:
            statement = statement.where(
                ScheduleException.exception_date
                >= start_date
            )

        if end_date is not None:
            statement = statement.where(
                ScheduleException.exception_date
                <= end_date
            )

        statement = statement.order_by(
            ScheduleException
            .exception_date
            .asc()
        )

        result = await self.session.scalars(
            statement
        )

        return list(result)

    async def get_exception(
        self,
        *,
        exception_id: uuid.UUID,
    ) -> ScheduleException | None:
        return await self.session.scalar(
            select(
                ScheduleException
            ).where(
                ScheduleException.id
                == exception_id
            )
        )

    async def exception_for_day(
        self,
        *,
        employee_id: uuid.UUID,
        on_date: date,
    ) -> ScheduleException | None:
        return await self.session.scalar(
            select(
                ScheduleException
            ).where(
                ScheduleException.employee_id
                == employee_id,
                ScheduleException.exception_date
                == on_date,
            )
        )

    # =====================================================
    # PUBLICATIONS
    # =====================================================

    async def list_publications(
        self,
    ) -> list[SchedulePublication]:
        result = await self.session.scalars(
            select(
                SchedulePublication
            )
            .order_by(
                SchedulePublication
                .period_start
                .desc()
            )
        )

        return list(result)

    async def publication_for_day(
        self,
        *,
        on_date: date,
    ) -> SchedulePublication | None:
        return await self.session.scalar(
            select(
                SchedulePublication
            )
            .where(
                SchedulePublication.status
                == (
                    SchedulePublicationStatus
                    .PUBLISHED
                ),
                SchedulePublication.period_start
                <= on_date,
                SchedulePublication.period_end
                >= on_date,
            )
            .order_by(
                SchedulePublication
                .published_at
                .desc()
            )
        )


__all__ = [
    "ShiftRepository",
]