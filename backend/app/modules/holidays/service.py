from __future__ import annotations

import uuid
from datetime import date

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.holidays.models import (
    Holiday,
)
from app.modules.holidays.repository import (
    HolidayRepository,
)
from app.modules.holidays.schemas import (
    HolidayCreateRequest,
    HolidayUpdateRequest,
)


class HolidayService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = HolidayRepository(
            session
        )

    # =====================================================
    # LIST
    # =====================================================

    async def list_holidays(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        active_only: bool = False,
    ) -> list[Holiday]:
        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "end_date cannot be "
                    "before start_date."
                ),
            )

        if (
            start_date is not None
            and end_date is not None
            and (
                end_date
                - start_date
            ).days > 3660
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Holiday query range "
                    "cannot exceed 3660 days."
                ),
            )

        return await (
            self.repository.list(
                start_date=start_date,
                end_date=end_date,
                active_only=active_only,
            )
        )

    # =====================================================
    # GET
    # =====================================================

    async def get_holiday(
        self,
        *,
        holiday_id: uuid.UUID,
    ) -> Holiday:
        holiday = await (
            self.repository.get(
                holiday_id=holiday_id
            )
        )

        if holiday is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Holiday not found."
                ),
            )

        return holiday

    # =====================================================
    # CREATE
    # =====================================================

    async def create_holiday(
        self,
        *,
        actor_user_id: uuid.UUID,
        request: HolidayCreateRequest,
    ) -> Holiday:
        holiday = Holiday(
            holiday_date=(
                request.holiday_date
            ),
            name=(
                request.name.strip()
            ),
            treatment=(
                request.treatment
            ),
            region=(
                request.region.strip()
                if request.region
                else None
            ),
            description=(
                request.description.strip()
                if request.description
                else None
            ),
            is_active=True,
            created_by_user_id=(
                actor_user_id
            ),
        )

        self.session.add(
            holiday
        )

        try:
            await self.session.commit()

        except IntegrityError as exc:
            await self.session.rollback()

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "A holiday with the same "
                    "date and name already exists."
                ),
            ) from exc

        await self.session.refresh(
            holiday
        )

        return holiday

    # =====================================================
    # UPDATE
    # =====================================================

    async def update_holiday(
        self,
        *,
        holiday_id: uuid.UUID,
        request: HolidayUpdateRequest,
    ) -> Holiday:
        holiday = await self.get_holiday(
            holiday_id=holiday_id
        )

        patch = request.model_dump(
            exclude_unset=True
        )

        for (
            field_name,
            value,
        ) in patch.items():
            if (
                field_name in {
                    "name",
                    "region",
                    "description",
                }
                and isinstance(
                    value,
                    str,
                )
            ):
                value = value.strip()

            setattr(
                holiday,
                field_name,
                value,
            )

        try:
            await self.session.commit()

        except IntegrityError as exc:
            await self.session.rollback()

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "A holiday with the same "
                    "date and name already exists."
                ),
            ) from exc

        await self.session.refresh(
            holiday
        )

        return holiday

    # =====================================================
    # DEACTIVATE
    # =====================================================

    async def deactivate_holiday(
        self,
        *,
        holiday_id: uuid.UUID,
    ) -> None:
        holiday = await self.get_holiday(
            holiday_id=holiday_id
        )

        holiday.is_active = False

        await self.session.commit()

    # =====================================================
    # RESOLUTION
    # =====================================================

    async def resolve_holiday_for_date(
        self,
        *,
        holiday_date: date,
    ) -> Holiday | None:
        """
        Generic lookup.

        May include a regional holiday.
        """

        return await (
            self.repository.for_date(
                holiday_date=(
                    holiday_date
                )
            )
        )

    async def resolve_workspace_holiday_for_date(
        self,
        *,
        holiday_date: date,
    ) -> Holiday | None:
        """
        Resolve a holiday safe to apply to every employee
        in the tenant.

        Regional holidays are deliberately excluded until
        Employee has an explicit region/location policy.
        """

        return await (
            self.repository
            .workspace_for_date(
                holiday_date=(
                    holiday_date
                )
            )
        )


__all__ = [
    "HolidayService",
]