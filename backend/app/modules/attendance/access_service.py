from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attendance.enums import (
    AttendanceStatus,
)
from app.modules.attendance.schemas import (
    AttendanceDayDetailResponse,
    AttendanceDayResponse,
    AttendanceDayUpdateRequest,
    AttendanceEventCreateRequest,
    AttendanceEventResponse,
    AttendanceListResponse,
    AttendanceSummaryResponse,
)
from app.modules.attendance.service import (
    AttendanceService,
)
from app.modules.employees.membership_bridge import (
    EmployeeMembershipBridge,
)


class AttendanceAccessService:
    """
    Control-plane authorization wrapper around AttendanceService.

    Authorization order:

        verified User
        -> WorkspaceMembership
        -> authorized tenant session
        -> AttendanceService

    AttendanceService itself remains tenant-domain only.
    """

    def __init__(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        control_session: AsyncSession,
        tenant_session: AsyncSession,
    ) -> None:
        self.workspace_id = workspace_id
        self.actor_user_id = actor_user_id

        self.access = EmployeeMembershipBridge(
            control_session
        )

        self.attendance = AttendanceService(
            tenant_session
        )

    async def record_event(
        self,
        *,
        employee_id: uuid.UUID,
        request: AttendanceEventCreateRequest,
    ) -> AttendanceEventResponse:
        await self.access.require_active_member(
            workspace_id=self.workspace_id,
            user_id=self.actor_user_id,
        )

        return await self.attendance.record_event(
            employee_id=employee_id,
            actor_user_id=self.actor_user_id,
            request=request,
        )

    async def get_day(
        self,
        *,
        attendance_day_id: uuid.UUID,
    ) -> AttendanceDayDetailResponse:
        await self.access.require_active_member(
            workspace_id=self.workspace_id,
            user_id=self.actor_user_id,
        )

        return await self.attendance.get_day(
            attendance_day_id=attendance_day_id,
        )

    async def update_day(
        self,
        request: AttendanceDayUpdateRequest,
        *,
        attendance_day_id: uuid.UUID,
    ) -> AttendanceDayResponse:
        await self.access.require_manager(
            workspace_id=self.workspace_id,
            user_id=self.actor_user_id,
        )

        return await self.attendance.update_day(
            request,
            attendance_day_id=attendance_day_id,
        )

    async def list_days(
        self,
        *,
        employee_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        status: AttendanceStatus | None = None,
    ) -> AttendanceListResponse:
        await self.access.require_active_member(
            workspace_id=self.workspace_id,
            user_id=self.actor_user_id,
        )

        return await self.attendance.list_days(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )

    async def employee_summary(
        self,
        *,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> AttendanceSummaryResponse:
        await self.access.require_active_member(
            workspace_id=self.workspace_id,
            user_id=self.actor_user_id,
        )

        return await self.attendance.employee_summary(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )


__all__ = [
    "AttendanceAccessService",
]