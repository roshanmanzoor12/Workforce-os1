from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.activity.repository import (
    ActivityRepository,
)
from app.modules.app_tracking.repository import (
    AppTrackingRepository,
)
from app.modules.desktop_agent.repository import (
    DesktopAgentRepository,
)
from app.modules.employee_monitoring_detail.access import (
    EmployeeMonitoringDetailAccess,
    require_employee_access,
)
from app.modules.employee_monitoring_detail.schemas import (
    EmployeeMonitoringActivity,
    EmployeeMonitoringAppItem,
    EmployeeMonitoringDetailResponse,
    EmployeeMonitoringDevice,
    EmployeeMonitoringEmployee,
    EmployeeMonitoringScreenshot,
    EmployeeMonitoringWebsiteItem,
    EmployeeMonitoringWorkSession,
)
from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.live_monitoring.repository import (
    LiveMonitoringRepository,
)
from app.modules.website_tracking.repository import (
    WebsiteTrackingRepository,
)
from app.modules.work_sessions.repository import (
    WorkSessionRepository,
)


# =========================================================
# ERRORS
# =========================================================


class EmployeeMonitoringDetailNotFoundError(
    LookupError
):
    pass


# =========================================================
# SERVICE
# =========================================================


class EmployeeMonitoringDetailService:
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

        self.activity = (
            ActivityRepository(
                session
            )
        )

        self.apps = (
            AppTrackingRepository(
                session
            )
        )

        self.websites = (
            WebsiteTrackingRepository(
                session
            )
        )

        self.work_sessions = (
            WorkSessionRepository(
                session
            )
        )

        self.devices = (
            DesktopAgentRepository(
                session
            )
        )

        self.live_monitoring = (
            LiveMonitoringRepository(
                session
            )
        )

    # =====================================================
    # EMPLOYEE
    # =====================================================

    @staticmethod
    def _employee_response(
        employee,
    ) -> EmployeeMonitoringEmployee:
        department = getattr(
            employee,
            "department",
            None,
        )

        team = getattr(
            employee,
            "team",
            None,
        )

        return (
            EmployeeMonitoringEmployee(
                id=employee.id,

                full_name=(
                    employee.full_name
                ),

                job_title=(
                    employee.job_title
                ),

                avatar_url=(
                    employee.avatar_url
                ),

                employment_status=(
                    employee
                    .employment_status
                ),

                department_id=(
                    employee
                    .department_id
                ),

                department_name=(
                    department.name
                    if department
                    is not None
                    else None
                ),

                team_id=(
                    employee.team_id
                ),

                team_name=(
                    team.name
                    if team is not None
                    else None
                ),
            )
        )

    # =====================================================
    # MAIN DETAIL
    # =====================================================

    async def get_detail(
        self,
        *,
        access: EmployeeMonitoringDetailAccess,
        employee_id: uuid.UUID,
        history_limit: int,
        screenshot_limit: int,
    ) -> EmployeeMonitoringDetailResponse:
        require_employee_access(
            access=access,
            employee_id=employee_id,
        )

        employee = await (
            self.employees
            .get_employee_by_id(
                employee_id
            )
        )

        if employee is None:
            raise (
                EmployeeMonitoringDetailNotFoundError(
                    "Employee not found."
                )
            )

        # -------------------------------------------------
        # CURRENT ACTIVITY
        # -------------------------------------------------

        latest_activity = await (
            self.activity
            .get_latest_for_employee(
                employee_id=employee_id
            )
        )

        activity_response = None

        if latest_activity is not None:
            activity_response = (
                EmployeeMonitoringActivity(
                    state=(
                        latest_activity.state
                    ),

                    idle_seconds=(
                        latest_activity
                        .idle_seconds
                    ),

                    observed_at=(
                        latest_activity
                        .observed_at
                    ),

                    received_at=(
                        latest_activity
                        .received_at
                    ),
                )
            )

        # -------------------------------------------------
        # APPLICATION HISTORY
        # -------------------------------------------------

        app_intervals = await (
            self.apps
            .list_intervals_for_employee(
                employee_id,
                limit=history_limit,
            )
        )

        application_items = [
            EmployeeMonitoringAppItem(
                id=item.id,

                device_id=item.device_id,

                app_key=item.app_key,

                process_name=(
                    item.process_name
                ),

                status=item.status,

                started_at=(
                    item.started_at
                ),

                ended_at=item.ended_at,

                last_observed_at=(
                    item.last_observed_at
                ),

                duration_seconds=(
                    item.duration_seconds
                ),
            )
            for item in app_intervals
        ]

        # -------------------------------------------------
        # WEBSITE HISTORY
        # -------------------------------------------------

        website_intervals = await (
            self.websites
            .list_employee_intervals(
                employee_id=employee_id,
                limit=history_limit,
            )
        )

        website_items = [
            EmployeeMonitoringWebsiteItem(
                id=item.id,

                device_id=item.device_id,

                browser_name=(
                    item.browser_name
                ),

                domain=item.domain,

                normalized_domain=(
                    item.normalized_domain
                ),

                status=item.status,

                started_at=(
                    item.started_at
                ),

                ended_at=item.ended_at,

                last_observed_at=(
                    item.last_observed_at
                ),

                duration_seconds=(
                    item.duration_seconds
                ),
            )
            for item in website_intervals
        ]

        # -------------------------------------------------
        # WORK SESSIONS
        # -------------------------------------------------

        sessions = await (
            self.work_sessions
            .list_for_employee(
                employee_id,
                limit=history_limit,
            )
        )

        work_session_items = [
            EmployeeMonitoringWorkSession(
                id=item.id,

                device_id=item.device_id,

                status=item.status,

                current_state=(
                    item.current_state
                ),

                started_at=(
                    item.started_at
                ),

                ended_at=item.ended_at,

                last_observed_at=(
                    item.last_observed_at
                ),

                active_seconds=(
                    item.active_seconds
                ),

                idle_seconds=(
                    item.idle_seconds
                ),

                total_seconds=(
                    item.total_seconds
                ),
            )
            for item in sessions
        ]

        # -------------------------------------------------
        # LINKED DESKTOP DEVICES
        # -------------------------------------------------

        (
            devices,
            device_total,
        ) = await self.devices.list(
            employee_ids=frozenset(
                {
                    employee_id,
                }
            ),
            status=None,
            limit=500,
            offset=0,
        )

        device_items = [
            EmployeeMonitoringDevice(
                id=item.id,

                device_name=(
                    item.device_name
                ),

                platform=item.platform,

                os_version=(
                    item.os_version
                ),

                agent_version=(
                    item.agent_version
                ),

                status=item.status,

                is_disabled=(
                    item.is_disabled
                ),

                last_seen_at=(
                    item.last_seen_at
                ),

                registered_at=(
                    item.registered_at
                ),

                capabilities=(
                    dict(
                        item.capabilities
                        or {}
                    )
                ),
            )
            for item in devices
        ]

        # -------------------------------------------------
        # SCREENSHOT HISTORY
        # -------------------------------------------------

        screenshot_items: list[
            EmployeeMonitoringScreenshot
        ] = []

        screenshot_total = 0

        if access.can_view_screens:
            (
                screenshots,
                screenshot_total,
            ) = await (
                self.live_monitoring
                .list_screenshots(
                    employee_ids=(
                        frozenset(
                            {
                                employee_id,
                            }
                        )
                    ),
                    limit=(
                        screenshot_limit
                    ),
                    offset=0,
                )
            )

            screenshot_items = [
                EmployeeMonitoringScreenshot(
                    id=item.id,

                    device_id=(
                        item.device_id
                    ),

                    status=item.status,

                    reason=item.reason,

                    consent_required=(
                        item
                        .consent_required
                    ),

                    visible_indicator_required=(
                        item
                        .visible_indicator_required
                    ),

                    consent_confirmed_at=(
                        item
                        .consent_confirmed_at
                    ),

                    requested_at=(
                        item.requested_at
                    ),

                    expires_at=(
                        item.expires_at
                    ),

                    completed_at=(
                        item.completed_at
                    ),

                    width=item.width,

                    height=item.height,
                )
                for item in screenshots
            ]

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return (
            EmployeeMonitoringDetailResponse(
                employee=(
                    self._employee_response(
                        employee
                    )
                ),

                current_activity=(
                    activity_response
                ),

                devices=device_items,

                applications=(
                    application_items
                ),

                websites=(
                    website_items
                ),

                work_sessions=(
                    work_session_items
                ),

                screenshots=(
                    screenshot_items
                ),

                screens_allowed=(
                    access
                    .can_view_screens
                ),

                device_count=(
                    device_total
                ),

                application_count=len(
                    application_items
                ),

                website_count=len(
                    website_items
                ),

                work_session_count=len(
                    work_session_items
                ),

                screenshot_count=(
                    screenshot_total
                    if access
                    .can_view_screens
                    else 0
                ),
            )
        )


__all__ = [
    "EmployeeMonitoringDetailNotFoundError",
    "EmployeeMonitoringDetailService",
]