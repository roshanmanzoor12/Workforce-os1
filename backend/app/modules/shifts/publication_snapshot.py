from __future__ import annotations

import uuid
from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.holidays.models import (
    HolidayTreatment,
)
from app.modules.shifts.holiday_context import (
    ShiftHolidayContextService,
)
from app.modules.shifts.models import (
    SchedulePublication,
    SchedulePublicationStatus,
)
from app.modules.shifts.publication_models import (
    SchedulePublicationDay,
)
from app.modules.shifts.schemas import (
    ResolvedScheduleDayResponse,
    SchedulePublishRequest,
)
from app.modules.shifts.service import (
    ShiftService,
)


class SchedulePublicationSnapshotService:
    """
    Materialize and read immutable published schedules.

    Live schedule configuration may continue changing after
    publication, but published rows remain stable.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.employees = (
            EmployeeRepository(
                session
            )
        )

        self.live = ShiftService(
            session
        )

        self.holiday_context = (
            ShiftHolidayContextService(
                session
            )
        )

    # =====================================================
    # READ SNAPSHOT
    # =====================================================

    async def get_published_day(
        self,
        *,
        employee_id: uuid.UUID,
        schedule_date: date,
    ) -> SchedulePublicationDay | None:
        return await self.session.scalar(
            select(
                SchedulePublicationDay
            )
            .join(
                SchedulePublication,
                SchedulePublication.id
                == (
                    SchedulePublicationDay
                    .publication_id
                ),
            )
            .where(
                (
                    SchedulePublicationDay
                    .employee_id
                    == employee_id
                ),
                (
                    SchedulePublicationDay
                    .schedule_date
                    == schedule_date
                ),
                (
                    SchedulePublication.status
                    == (
                        SchedulePublicationStatus
                        .PUBLISHED
                    )
                ),
            )
            .order_by(
                (
                    SchedulePublication
                    .published_at
                    .desc()
                ),
                (
                    SchedulePublication
                    .created_at
                    .desc()
                ),
            )
        )

    # =====================================================
    # RESOLVE
    # =====================================================

    async def resolve_day(
        self,
        *,
        employee_id: uuid.UUID,
        schedule_date: date,
    ) -> ResolvedScheduleDayResponse:
        snapshot = await (
            self.get_published_day(
                employee_id=employee_id,
                schedule_date=(
                    schedule_date
                ),
            )
        )

        if snapshot is not None:
            return self._response_from_snapshot(
                snapshot
            )

        live_day = await (
            self.live.resolve_employee_day(
                employee_id=employee_id,
                on_date=schedule_date,
            )
        )

        return await (
            self.holiday_context.apply(
                live_day
            )
        )

    # =====================================================
    # PUBLISH
    # =====================================================

    async def publish(
        self,
        *,
        actor_user_id: uuid.UUID,
        request: SchedulePublishRequest,
    ) -> SchedulePublication:
        publication = (
            SchedulePublication(
                period_start=(
                    request.period_start
                ),
                period_end=(
                    request.period_end
                ),
                status=(
                    SchedulePublicationStatus
                    .PUBLISHED
                ),
                published_by_user_id=(
                    actor_user_id
                ),
                published_at=(
                    datetime.now(
                        timezone.utc
                    )
                ),
                note=request.note,
            )
        )

        self.session.add(
            publication
        )

        try:
            await self.session.flush()

            employees = list(
                await (
                    self.employees
                    .list_employees()
                )
            )

            for employee in employees:
                current_date = (
                    request.period_start
                )

                while (
                    current_date
                    <= request.period_end
                ):
                    # Deliberately calculate from current
                    # mutable configuration while publishing.
                    #
                    # Future reads use the immutable row below.
                    live_day = await (
                        self.live
                        .resolve_employee_day(
                            employee_id=(
                                employee.id
                            ),
                            on_date=(
                                current_date
                            ),
                        )
                    )

                    live_day = await (
                        self.holiday_context
                        .apply(
                            live_day
                        )
                    )

                    holiday_treatment = (
                        live_day
                        .holiday_treatment
                    )

                    if (
                        holiday_treatment
                        is not None
                    ):
                        holiday_treatment = (
                            holiday_treatment.value
                        )

                    self.session.add(
                        SchedulePublicationDay(
                            publication_id=(
                                publication.id
                            ),
                            employee_id=(
                                employee.id
                            ),
                            schedule_date=(
                                current_date
                            ),
                            source=(
                                live_day.source
                            ),
                            shift_id=(
                                live_day.shift_id
                            ),
                            timezone=(
                                live_day.timezone
                            ),
                            start_time=(
                                live_day.start_time
                            ),
                            end_time=(
                                live_day.end_time
                            ),
                            break_minutes=(
                                live_day.break_minutes
                            ),
                            scheduled_minutes=(
                                live_day
                                .scheduled_minutes
                            ),
                            payable_minutes=(
                                live_day
                                .payable_minutes
                            ),
                            is_working_day=(
                                live_day
                                .is_working_day
                            ),
                            exception_id=(
                                live_day
                                .exception_id
                            ),
                            is_holiday=(
                                live_day
                                .is_holiday
                            ),
                            holiday_id=(
                                live_day
                                .holiday_id
                            ),
                            holiday_name=(
                                live_day
                                .holiday_name
                            ),
                            holiday_treatment=(
                                holiday_treatment
                            ),
                        )
                    )

                    current_date += (
                        timedelta(
                            days=1
                        )
                    )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        await self.session.refresh(
            publication
        )

        return publication

    # =====================================================
    # SERIALIZE
    # =====================================================

    @staticmethod
    def _response_from_snapshot(
        snapshot: SchedulePublicationDay,
    ) -> ResolvedScheduleDayResponse:
        holiday_treatment = None

        if (
            snapshot.holiday_treatment
            is not None
        ):
            holiday_treatment = (
                HolidayTreatment(
                    snapshot
                    .holiday_treatment
                )
            )

        return (
            ResolvedScheduleDayResponse(
                employee_id=(
                    snapshot.employee_id
                ),
                schedule_date=(
                    snapshot.schedule_date
                ),
                source=(
                    snapshot.source
                ),
                shift_id=(
                    snapshot.shift_id
                ),
                timezone=(
                    snapshot.timezone
                ),
                start_time=(
                    snapshot.start_time
                ),
                end_time=(
                    snapshot.end_time
                ),
                break_minutes=(
                    snapshot.break_minutes
                ),
                scheduled_minutes=(
                    snapshot
                    .scheduled_minutes
                ),
                payable_minutes=(
                    snapshot
                    .payable_minutes
                ),
                is_working_day=(
                    snapshot
                    .is_working_day
                ),
                is_published=True,
                exception_id=(
                    snapshot.exception_id
                ),
                is_holiday=(
                    snapshot.is_holiday
                ),
                holiday_id=(
                    snapshot.holiday_id
                ),
                holiday_name=(
                    snapshot.holiday_name
                ),
                holiday_treatment=(
                    holiday_treatment
                ),
            )
        )


__all__ = [
    "SchedulePublicationSnapshotService",
]