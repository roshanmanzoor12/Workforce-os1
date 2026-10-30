from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.exceptions import (
    ResourceNotFound,
    ValidationError,
)
from app.modules.attendance.calculator import (
    AttendanceCalculationError,
    calculate_attendance_totals,
)
from app.modules.attendance.enums import (
    AttendanceStatus,
)
from app.modules.attendance.models import (
    AttendanceDay,
)
from app.modules.attendance.repository import (
    AttendanceRepository,
)
from app.modules.attendance.schemas import (
    AttendanceDayDetailResponse,
    AttendanceDayPublic,
    AttendanceDayResponse,
    AttendanceDayUpdateRequest,
    AttendanceEventCreateRequest,
    AttendanceEventPublic,
    AttendanceEventResponse,
    AttendanceListResponse,
    AttendanceSummaryResponse,
)
from app.modules.employees.models import (
    EMPLOYMENT_STATUS_TERMINATED,
)
from app.modules.employees.repository import (
    EmployeeRepository,
)


class AttendanceService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            AttendanceRepository(
                session
            )
        )

        self.employees = (
            EmployeeRepository(
                session
            )
        )

    async def record_event(
        self,
        *,
        employee_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        request: AttendanceEventCreateRequest,
    ) -> AttendanceEventResponse:
        employee = (
            await self.employees
            .get_employee_by_id(
                employee_id
            )
        )

        if employee is None:
            raise ResourceNotFound(
                "Employee was not found."
            )

        if not employee.is_active:
            raise ValidationError(
                "Attendance cannot be recorded "
                "for an inactive employee."
            )

        if (
            employee.employment_status
            == EMPLOYMENT_STATUS_TERMINATED
        ):
            raise ValidationError(
                "Attendance cannot be recorded "
                "for a terminated employee."
            )

        work_date = (
            request.occurred_at.date()
        )

        day = (
            await self.repository.get_day(
                employee_id=employee_id,
                work_date=work_date,
            )
        )

        if day is None:
            day = (
                await self.repository.create_day(
                    employee_id=employee_id,
                    work_date=work_date,
                    status=(
                        AttendanceStatus.PRESENT.value
                    ),
                )
            )

        try:
            event = (
                await self.repository.create_event(
                    attendance_day_id=day.id,
                    employee_id=employee_id,
                    event_type=(
                        request.event_type.value
                    ),
                    source=(
                        request.source.value
                    ),
                    occurred_at=(
                        request.occurred_at
                    ),
                    actor_user_id=(
                        actor_user_id
                    ),
                    note=request.note,
                )
            )

            events = list(
                await self.repository.list_events(
                    attendance_day_id=day.id
                )
            )

            (
                first_check_in,
                last_check_out,
                worked_seconds,
                break_seconds,
            ) = calculate_attendance_totals(
                events
            )

            await self.repository.update_day(
                day,
                values={
                    "first_check_in_at": (
                        first_check_in
                    ),
                    "last_check_out_at": (
                        last_check_out
                    ),
                    "worked_seconds": (
                        worked_seconds
                    ),
                    "break_seconds": (
                        break_seconds
                    ),
                },
            )

            await self.session.commit()

        except AttendanceCalculationError as exc:
            await self.session.rollback()

            raise ValidationError(
                str(exc)
            ) from exc

        except Exception:
            await self.session.rollback()
            raise

        return AttendanceEventResponse(
            message=(
                "Attendance event recorded."
            ),
            event=(
                AttendanceEventPublic
                .model_validate(
                    event
                )
            ),
        )

    async def get_day(
        self,
        *,
        attendance_day_id: uuid.UUID,
    ) -> AttendanceDayDetailResponse:
        day = (
            await self.repository
            .get_day_by_id(
                attendance_day_id
            )
        )

        if day is None:
            raise ResourceNotFound(
                "Attendance day was not found."
            )

        return (
            AttendanceDayDetailResponse(
                attendance=(
                    self._day_public(
                        day
                    )
                ),
                events=[
                    AttendanceEventPublic
                    .model_validate(
                        event
                    )
                    for event
                    in day.events
                ],
            )
        )

    async def update_day(
        self,
        request: AttendanceDayUpdateRequest,
        *,
        attendance_day_id: uuid.UUID,
    ) -> AttendanceDayResponse:
        day = (
            await self.repository
            .get_day_by_id(
                attendance_day_id
            )
        )

        if day is None:
            raise ResourceNotFound(
                "Attendance day was not found."
            )

        fields = request.model_fields_set

        if not fields:
            return AttendanceDayResponse(
                message="Attendance unchanged.",
                attendance=(
                    self._day_public(
                        day
                    )
                ),
            )

        values: dict[
            str,
            object,
        ] = {}

        if "status" in fields:
            if request.status is None:
                raise ValidationError(
                    "Attendance status "
                    "cannot be null."
                )

            values["status"] = (
                request.status.value
            )

        if "note" in fields:
            values["note"] = (
                request.note
            )

        try:
            day = (
                await self.repository.update_day(
                    day,
                    values=values,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return AttendanceDayResponse(
            message="Attendance updated.",
            attendance=self._day_public(
                day
            ),
        )

    async def list_days(
        self,
        *,
        employee_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        status: (
            AttendanceStatus | None
        ) = None,
    ) -> AttendanceListResponse:
        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):
            raise ValidationError(
                "end_date cannot be "
                "before start_date."
            )

        records = (
            await self.repository.list_days(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                status=(
                    status.value
                    if status is not None
                    else None
                ),
            )
        )

        items = [
            self._day_public(
                item
            )
            for item in records
        ]

        return AttendanceListResponse(
            attendance=items,
            total=len(items),
        )

    async def employee_summary(
        self,
        *,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> AttendanceSummaryResponse:
        if end_date < start_date:
            raise ValidationError(
                "end_date cannot be "
                "before start_date."
            )

        employee = (
            await self.employees
            .get_employee_by_id(
                employee_id
            )
        )

        if employee is None:
            raise ResourceNotFound(
                "Employee was not found."
            )

        records = list(
            await self.repository.list_days(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
            )
        )

        counts = {
            item.value: 0
            for item in AttendanceStatus
        }

        worked_seconds = 0
        break_seconds = 0

        for record in records:
            if record.status in counts:
                counts[
                    record.status
                ] += 1

            worked_seconds += (
                record.worked_seconds
            )

            break_seconds += (
                record.break_seconds
            )

        return AttendanceSummaryResponse(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            present_days=counts[
                AttendanceStatus.PRESENT.value
            ],
            absent_days=counts[
                AttendanceStatus.ABSENT.value
            ],
            late_days=counts[
                AttendanceStatus.LATE.value
            ],
            half_days=counts[
                AttendanceStatus.HALF_DAY.value
            ],
            leave_days=counts[
                AttendanceStatus.ON_LEAVE.value
            ],
            holiday_days=counts[
                AttendanceStatus.HOLIDAY.value
            ],
            worked_seconds=worked_seconds,
            break_seconds=break_seconds,
        )

    @staticmethod
    def _day_public(
        day: AttendanceDay,
    ) -> AttendanceDayPublic:
        return (
            AttendanceDayPublic
            .model_validate(
                day
            )
        )


def get_attendance_service(
    session: AsyncSession,
) -> AttendanceService:
    return AttendanceService(
        session
    )


__all__ = [
    "AttendanceService",
    "get_attendance_service",
]