from __future__ import annotations

import uuid
from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from zoneinfo import (
    ZoneInfo,
)

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.shifts.models import (
    ScheduleException,
    ScheduleExceptionType,
    SchedulePublication,
    SchedulePublicationStatus,
    ShiftAssignment,
    ShiftAssignmentTargetType,
    ShiftTemplate,
    ShiftWorkingDay,
)
from app.modules.shifts.repository import (
    ShiftRepository,
)
from app.modules.shifts.schemas import (
    ResolvedScheduleDayResponse,
    ScheduleExceptionCreateRequest,
    ScheduleExceptionUpdateRequest,
    SchedulePublishRequest,
    ShiftAssignmentCreateRequest,
    ShiftAssignmentUpdateRequest,
    ShiftCreateRequest,
    ShiftUpdateRequest,
)


def minutes_between(
    start_time,
    end_time,
    *,
    overnight: bool,
) -> int:
    base = date(
        2000,
        1,
        1,
    )

    start_datetime = (
        datetime.combine(
            base,
            start_time,
        )
    )

    end_datetime = (
        datetime.combine(
            base,
            end_time,
        )
    )

    if (
        overnight
        or end_datetime
        <= start_datetime
    ):
        end_datetime += timedelta(
            days=1
        )

    return max(
        0,
        int(
            (
                end_datetime
                - start_datetime
            ).total_seconds()
            // 60
        ),
    )


class ShiftService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            ShiftRepository(
                session
            )
        )

        self.employees = (
            EmployeeRepository(
                session
            )
        )

    # =====================================================
    # SHIFT TEMPLATE
    # =====================================================

    async def list_shifts(
        self,
        *,
        active_only: bool = False,
    ):
        return await (
            self.repository
            .list_shifts(
                active_only=active_only
            )
        )

    async def create_shift(
        self,
        request: ShiftCreateRequest,
    ) -> ShiftTemplate:
        self._validate_timezone(
            request.timezone
        )

        self._validate_shift_times(
            start_time=request.start_time,
            end_time=request.end_time,
            is_overnight=(
                request.is_overnight
            ),
        )

        weekdays = [
            item.weekday
            for item
            in request.working_days
        ]

        if (
            len(weekdays)
            != len(
                set(weekdays)
            )
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "working_days cannot "
                    "contain duplicate weekdays."
                ),
            )

        shift = ShiftTemplate(
            name=request.name.strip(),
            timezone=(
                request.timezone.strip()
            ),
            start_time=(
                request.start_time
            ),
            end_time=request.end_time,
            break_minutes=(
                request.break_minutes
            ),
            standard_paid_minutes=(
                request
                .standard_paid_minutes
            ),
            grace_before_minutes=(
                request
                .grace_before_minutes
            ),
            grace_after_minutes=(
                request
                .grace_after_minutes
            ),
            overtime_after_minutes=(
                request
                .overtime_after_minutes
            ),
            is_overnight=(
                request.is_overnight
            ),
            is_active=True,
        )

        await self.repository.create_shift(
            shift
        )

        working_days = [
            ShiftWorkingDay(
                shift_id=shift.id,
                weekday=item.weekday,
                is_working_day=(
                    item.is_working_day
                ),
            )
            for item
            in request.working_days
        ]

        await (
            self.repository
            .replace_working_days(
                shift_id=shift.id,
                working_days=(
                    working_days
                ),
            )
        )

        await self.session.commit()

        await self.session.refresh(
            shift
        )

        return shift

    async def update_shift(
        self,
        *,
        shift_id: uuid.UUID,
        request: ShiftUpdateRequest,
    ) -> ShiftTemplate:
        shift = await (
            self.repository
            .get_shift(
                shift_id=shift_id
            )
        )

        if shift is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Shift not found.",
            )

        patch = request.model_dump(
            exclude_unset=True,
            exclude={
                "working_days"
            },
        )

        if (
            "timezone" in patch
            and patch["timezone"]
            is not None
        ):
            self._validate_timezone(
                patch["timezone"]
            )

        for (
            field_name,
            value,
        ) in patch.items():
            if (
                field_name == "name"
                and isinstance(
                    value,
                    str,
                )
            ):
                value = value.strip()

            if (
                field_name
                == "timezone"
                and isinstance(
                    value,
                    str,
                )
            ):
                value = value.strip()

            setattr(
                shift,
                field_name,
                value,
            )

        self._validate_shift_times(
            start_time=(
                shift.start_time
            ),
            end_time=(
                shift.end_time
            ),
            is_overnight=(
                shift.is_overnight
            ),
        )

        if (
            request.working_days
            is not None
        ):
            weekdays = [
                item.weekday
                for item
                in request.working_days
            ]

            if (
                len(weekdays)
                != len(
                    set(weekdays)
                )
            ):
                raise HTTPException(
                    status_code=(
                        status
                        .HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "working_days cannot "
                        "contain duplicate weekdays."
                    ),
                )

            await (
                self.repository
                .replace_working_days(
                    shift_id=shift.id,
                    working_days=[
                        ShiftWorkingDay(
                            shift_id=(
                                shift.id
                            ),
                            weekday=(
                                item.weekday
                            ),
                            is_working_day=(
                                item
                                .is_working_day
                            ),
                        )
                        for item
                        in request
                        .working_days
                    ],
                )
            )

        await self.session.commit()

        await self.session.refresh(
            shift
        )

        return shift

    async def deactivate_shift(
        self,
        *,
        shift_id: uuid.UUID,
    ) -> None:
        shift = await (
            self.repository
            .get_shift(
                shift_id=shift_id
            )
        )

        if shift is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Shift not found.",
            )

        shift.is_active = False

        await self.session.commit()

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
    ):
        return await (
            self.repository
            .list_assignments(
                target_type=target_type,
                target_id=target_id,
            )
        )

    async def create_assignment(
        self,
        request: (
            ShiftAssignmentCreateRequest
        ),
    ) -> ShiftAssignment:
        shift = await (
            self.repository
            .get_shift(
                shift_id=request.shift_id
            )
        )

        if (
            shift is None
            or not shift.is_active
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Active shift not found."
                ),
            )

        await self._require_assignment_target(
            target_type=(
                request.target_type
            ),
            target_id=(
                request.target_id
            ),
        )

        assignment = ShiftAssignment(
            shift_id=request.shift_id,
            target_type=(
                request.target_type
            ),
            target_id=request.target_id,
            effective_from=(
                request.effective_from
            ),
            effective_to=(
                request.effective_to
            ),
            priority=request.priority,
        )

        self.session.add(
            assignment
        )

        await self.session.commit()

        await self.session.refresh(
            assignment
        )

        return assignment

    async def update_assignment(
        self,
        *,
        assignment_id: uuid.UUID,
        request: (
            ShiftAssignmentUpdateRequest
        ),
    ) -> ShiftAssignment:
        assignment = await (
            self.repository
            .get_assignment(
                assignment_id=(
                    assignment_id
                )
            )
        )

        if assignment is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Shift assignment "
                    "not found."
                ),
            )

        patch = request.model_dump(
            exclude_unset=True
        )

        if (
            "shift_id" in patch
            and patch["shift_id"]
            is not None
        ):
            shift = await (
                self.repository
                .get_shift(
                    shift_id=(
                        patch["shift_id"]
                    )
                )
            )

            if (
                shift is None
                or not shift.is_active
            ):
                raise HTTPException(
                    status_code=(
                        status
                        .HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "Active shift "
                        "not found."
                    ),
                )

        final_target_type = (
            patch.get(
                "target_type",
                assignment.target_type,
            )
        )

        final_target_id = (
            patch.get(
                "target_id",
                assignment.target_id,
            )
        )

        if (
            final_target_type is None
            or final_target_id is None
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Assignment target_type "
                    "and target_id are required."
                ),
            )

        await self._require_assignment_target(
            target_type=(
                final_target_type
            ),
            target_id=(
                final_target_id
            ),
        )

        for (
            field_name,
            value,
        ) in patch.items():
            setattr(
                assignment,
                field_name,
                value,
            )

        if (
            assignment.effective_to
            is not None
            and assignment.effective_to
            < assignment.effective_from
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "effective_to cannot "
                    "be before effective_from."
                ),
            )

        await self.session.commit()

        await self.session.refresh(
            assignment
        )

        return assignment

    async def delete_assignment(
        self,
        *,
        assignment_id: uuid.UUID,
    ) -> None:
        assignment = await (
            self.repository
            .get_assignment(
                assignment_id=(
                    assignment_id
                )
            )
        )

        if assignment is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Shift assignment "
                    "not found."
                ),
            )

        await self.session.delete(
            assignment
        )

        await self.session.commit()

    # =====================================================
    # EXCEPTIONS
    # =====================================================

    async def create_exception(
        self,
        *,
        actor_user_id: uuid.UUID,
        request: (
            ScheduleExceptionCreateRequest
        ),
    ) -> ScheduleException:
        employee = await (
            self.employees
            .get_employee_by_id(
                request.employee_id
            )
        )

        if (
            employee is None
            or not employee.is_active
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Active employee "
                    "not found."
                ),
            )

        existing = await (
            self.repository
            .exception_for_day(
                employee_id=(
                    request.employee_id
                ),
                on_date=(
                    request.exception_date
                ),
            )
        )

        if existing is not None:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "A schedule exception "
                    "already exists for this "
                    "employee and date."
                ),
            )

        exception = ScheduleException(
            employee_id=(
                request.employee_id
            ),
            exception_date=(
                request.exception_date
            ),
            exception_type=(
                request.exception_type
            ),
            custom_start_time=(
                request.custom_start_time
            ),
            custom_end_time=(
                request.custom_end_time
            ),
            break_minutes=(
                request.break_minutes
            ),
            reason=request.reason,
            created_by_user_id=(
                actor_user_id
            ),
        )

        self.session.add(
            exception
        )

        await self.session.commit()

        await self.session.refresh(
            exception
        )

        return exception

    async def update_exception(
        self,
        *,
        exception_id: uuid.UUID,
        request: (
            ScheduleExceptionUpdateRequest
        ),
    ) -> ScheduleException:
        exception = await (
            self.repository
            .get_exception(
                exception_id=(
                    exception_id
                )
            )
        )

        if exception is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Schedule exception "
                    "not found."
                ),
            )

        patch = request.model_dump(
            exclude_unset=True
        )

        if (
            "employee_id" in patch
            and patch["employee_id"]
            is not None
        ):
            employee = await (
                self.employees
                .get_employee_by_id(
                    patch["employee_id"]
                )
            )

            if (
                employee is None
                or not employee.is_active
            ):
                raise HTTPException(
                    status_code=(
                        status
                        .HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "Active employee "
                        "not found."
                    ),
                )

        for (
            field_name,
            value,
        ) in patch.items():
            setattr(
                exception,
                field_name,
                value,
            )

        if (
            exception.exception_type
            == (
                ScheduleExceptionType
                .CUSTOM_SHIFT
            )
            and (
                exception.custom_start_time
                is None
                or exception.custom_end_time
                is None
            )
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Custom shift exception "
                    "requires start and "
                    "end time."
                ),
            )

        await self.session.commit()

        await self.session.refresh(
            exception
        )

        return exception

    async def delete_exception(
        self,
        *,
        exception_id: uuid.UUID,
    ) -> None:
        exception = await (
            self.repository
            .get_exception(
                exception_id=(
                    exception_id
                )
            )
        )

        if exception is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Schedule exception "
                    "not found."
                ),
            )

        await self.session.delete(
            exception
        )

        await self.session.commit()

    # =====================================================
    # PUBLICATION
    # =====================================================

    async def publish_schedule(
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

        await self.session.commit()

        await self.session.refresh(
            publication
        )

        return publication

    # =====================================================
    # RESOLUTION
    # =====================================================

    async def resolve_employee_day(
        self,
        *,
        employee_id: uuid.UUID,
        on_date: date,
    ) -> ResolvedScheduleDayResponse:
        employee = await (
            self.employees
            .get_employee_by_id(
                employee_id
            )
        )

        if employee is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Employee not found.",
            )

        publication = await (
            self.repository
            .publication_for_day(
                on_date=on_date
            )
        )

        is_published = (
            publication is not None
        )

        exception = await (
            self.repository
            .exception_for_day(
                employee_id=(
                    employee_id
                ),
                on_date=on_date,
            )
        )

        if (
            exception is not None
            and exception.exception_type
            == (
                ScheduleExceptionType
                .OFF_DAY
            )
        ):
            return (
                ResolvedScheduleDayResponse(
                    employee_id=(
                        employee_id
                    ),
                    schedule_date=(
                        on_date
                    ),
                    source=(
                        "exception_off_day"
                    ),
                    is_published=(
                        is_published
                    ),
                    exception_id=(
                        exception.id
                    ),
                )
            )

        if (
            exception is not None
            and exception.exception_type
            == (
                ScheduleExceptionType
                .CUSTOM_SHIFT
            )
        ):
            assert (
                exception.custom_start_time
                is not None
            )

            assert (
                exception.custom_end_time
                is not None
            )

            overnight = (
                exception.custom_end_time
                <= (
                    exception
                    .custom_start_time
                )
            )

            total_minutes = (
                minutes_between(
                    exception
                    .custom_start_time,
                    exception
                    .custom_end_time,
                    overnight=overnight,
                )
            )

            break_minutes = (
                exception.break_minutes
                or 0
            )

            scheduled_minutes = max(
                0,
                total_minutes
                - break_minutes,
            )

            return (
                ResolvedScheduleDayResponse(
                    employee_id=(
                        employee_id
                    ),
                    schedule_date=(
                        on_date
                    ),
                    source=(
                        "exception_custom_shift"
                    ),
                    start_time=(
                        exception
                        .custom_start_time
                    ),
                    end_time=(
                        exception
                        .custom_end_time
                    ),
                    break_minutes=(
                        break_minutes
                    ),
                    scheduled_minutes=(
                        scheduled_minutes
                    ),
                    payable_minutes=(
                        scheduled_minutes
                    ),
                    is_working_day=True,
                    is_published=(
                        is_published
                    ),
                    exception_id=(
                        exception.id
                    ),
                )
            )

        assignments = await (
            self.repository
            .active_assignments_for_employee(
                employee_id=(
                    employee_id
                ),
                team_id=(
                    employee.team_id
                ),
                on_date=on_date,
            )
        )

        if not assignments:
            return (
                ResolvedScheduleDayResponse(
                    employee_id=(
                        employee_id
                    ),
                    schedule_date=(
                        on_date
                    ),
                    source="unscheduled",
                    is_published=(
                        is_published
                    ),
                )
            )

        assignment = sorted(
            assignments,
            key=(
                self
                ._assignment_precedence
            ),
            reverse=True,
        )[0]

        shift = await (
            self.repository
            .get_shift(
                shift_id=(
                    assignment.shift_id
                )
            )
        )

        if (
            shift is None
            or not shift.is_active
        ):
            return (
                ResolvedScheduleDayResponse(
                    employee_id=(
                        employee_id
                    ),
                    schedule_date=(
                        on_date
                    ),
                    source=(
                        "inactive_shift"
                    ),
                    is_published=(
                        is_published
                    ),
                )
            )

        working_days = {
            item.weekday:
            item.is_working_day
            for item
            in await (
                self.repository
                .list_working_days(
                    shift_id=(
                        shift.id
                    )
                )
            )
        }

        source = (
            "employee_assignment"
            if (
                assignment.target_type
                == (
                    ShiftAssignmentTargetType
                    .EMPLOYEE
                )
            )
            else "team_assignment"
        )

        if not working_days.get(
            on_date.weekday(),
            False,
        ):
            return (
                ResolvedScheduleDayResponse(
                    employee_id=(
                        employee_id
                    ),
                    schedule_date=(
                        on_date
                    ),
                    source=(
                        f"{source}_off_day"
                    ),
                    shift_id=shift.id,
                    timezone=(
                        shift.timezone
                    ),
                    is_published=(
                        is_published
                    ),
                )
            )

        total_minutes = (
            minutes_between(
                shift.start_time,
                shift.end_time,
                overnight=(
                    shift.is_overnight
                ),
            )
        )

        scheduled_minutes = (
            shift.standard_paid_minutes
        )

        if scheduled_minutes is None:
            scheduled_minutes = max(
                0,
                total_minutes
                - shift.break_minutes,
            )

        return (
            ResolvedScheduleDayResponse(
                employee_id=(
                    employee_id
                ),
                schedule_date=on_date,
                source=source,
                shift_id=shift.id,
                timezone=shift.timezone,
                start_time=(
                    shift.start_time
                ),
                end_time=(
                    shift.end_time
                ),
                break_minutes=(
                    shift.break_minutes
                ),
                scheduled_minutes=(
                    scheduled_minutes
                ),
                payable_minutes=(
                    scheduled_minutes
                ),
                is_working_day=True,
                is_published=(
                    is_published
                ),
            )
        )

    # =====================================================
    # ASSIGNMENT TARGET VALIDATION
    # =====================================================

    async def _require_assignment_target(
        self,
        *,
        target_type: (
            ShiftAssignmentTargetType
        ),
        target_id: uuid.UUID,
    ) -> None:
        if (
            target_type
            == (
                ShiftAssignmentTargetType
                .EMPLOYEE
            )
        ):
            employee = await (
                self.employees
                .get_employee_by_id(
                    target_id
                )
            )

            if (
                employee is None
                or not employee.is_active
            ):
                raise HTTPException(
                    status_code=(
                        status
                        .HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "Active employee "
                        "assignment target "
                        "not found."
                    ),
                )

            return

        if (
            target_type
            == (
                ShiftAssignmentTargetType
                .TEAM
            )
        ):
            team = await (
                self.employees
                .get_team_by_id(
                    target_id
                )
            )

            if (
                team is None
                or not team.is_active
            ):
                raise HTTPException(
                    status_code=(
                        status
                        .HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "Active team assignment "
                        "target not found."
                    ),
                )

            return

        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Unsupported shift "
                "assignment target type."
            ),
        )

    # =====================================================
    # PRECEDENCE
    # =====================================================

    @staticmethod
    def _assignment_precedence(
        assignment: ShiftAssignment,
    ):
        """
        Higher priority wins.

        On equal priority:
        - direct employee assignment beats team assignment
        - newer effective_from wins
        """

        direct_employee = (
            1
            if (
                assignment.target_type
                == (
                    ShiftAssignmentTargetType
                    .EMPLOYEE
                )
            )
            else 0
        )

        return (
            assignment.priority,
            direct_employee,
            assignment.effective_from,
        )

    # =====================================================
    # VALIDATION
    # =====================================================

    @staticmethod
    def _validate_timezone(
        timezone_name: str,
    ) -> None:
        try:
            ZoneInfo(
                timezone_name
            )

        except Exception as exc:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Invalid IANA timezone."
                ),
            ) from exc

    @staticmethod
    def _validate_shift_times(
        *,
        start_time,
        end_time,
        is_overnight: bool,
    ) -> None:
        if (
            not is_overnight
            and end_time <= start_time
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "end_time must be "
                    "after start_time unless "
                    "is_overnight=true."
                ),
            )


__all__ = [
    "ShiftService",
    "minutes_between",
]