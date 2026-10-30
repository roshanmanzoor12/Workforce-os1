from __future__ import annotations

import uuid

from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import (
    select,
)

from app.core.exceptions import (
    ValidationError,
)
from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.analytics.access import (
    AnalyticsAccess,
    AnalyticsScope,
)
from app.modules.analytics.service import (
    AnalyticsService,
)
from app.modules.audit_log.service import (
    AuditLogService,
)
from app.modules.devices.readiness_access import (
    resolve_device_readiness_access,
)
from app.modules.devices.readiness_service import (
    DeviceReadinessService,
)
from app.modules.employees.models import (
    Employee,
)
from app.modules.payroll.service import (
    PayrollService,
)
from app.modules.reports.permissions import (
    ReportsAccess,
    require_report_scope,
)
from app.modules.reports.schemas import (
    ReportKey,
    ReportParametersResponse,
    ReportRunRequest,
    ReportRunResponse,
    ReportScope,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


def _now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def _enum_value(
    value,
):
    return getattr(
        value,
        "value",
        value,
    )


class ReportExecutionService:
    def __init__(
        self,
        *,
        workspace_id: uuid.UUID,
        scope: TenantScope,
        reports_access: ReportsAccess,
    ) -> None:
        self.workspace_id = (
            workspace_id
        )

        self.scope = scope

        self.session = scope.session

        self.reports_access = (
            reports_access
        )

        self.permissions = (
            WorkspacePermissionService(
                scope
            )
        )

    # =====================================================
    # PERMISSIONS
    # =====================================================

    def _require_domain_permission(
        self,
        *,
        request: ReportRunRequest,
    ) -> None:
        report = request.report

        report_scope = request.scope

        if report == ReportKey.ATTENDANCE:
            permission = {
                ReportScope.SELF: (
                    WorkspacePermission
                    .ATTENDANCE_SELF_READ
                    .value
                ),
                ReportScope.TEAM: (
                    WorkspacePermission
                    .ATTENDANCE_TEAM_READ
                    .value
                ),
                ReportScope.WORKSPACE: (
                    WorkspacePermission
                    .ATTENDANCE_ALL_READ
                    .value
                ),
            }[
                report_scope
            ]

        elif (
            report
            == ReportKey.PRODUCTIVITY
        ):
            permission = {
                ReportScope.SELF: (
                    WorkspacePermission
                    .PRODUCTIVITY_INSIGHTS_SELF_READ
                    .value
                ),
                ReportScope.TEAM: (
                    WorkspacePermission
                    .PRODUCTIVITY_INSIGHTS_TEAM_READ
                    .value
                ),
                ReportScope.WORKSPACE: (
                    WorkspacePermission
                    .PRODUCTIVITY_INSIGHTS_ALL_READ
                    .value
                ),
            }[
                report_scope
            ]

        elif report == ReportKey.GOALS:
            permission = (
                WorkspacePermission
                .GOALS_SELF
                .value
                if (
                    report_scope
                    == ReportScope.SELF
                )
                else (
                    WorkspacePermission
                    .GOALS_VIEW
                    .value
                )
            )

        elif (
            report
            == ReportKey.DEVICE_HEALTH
        ):
            permission = {
                ReportScope.SELF: (
                    WorkspacePermission
                    .DEVICES_SELF_READ
                    .value
                ),
                ReportScope.TEAM: (
                    WorkspacePermission
                    .DEVICES_TEAM_READ
                    .value
                ),
                ReportScope.WORKSPACE: (
                    WorkspacePermission
                    .DEVICES_ALL_READ
                    .value
                ),
            }[
                report_scope
            ]

        elif (
            report
            == ReportKey.MONITORING_SUMMARY
        ):
            permission = {
                ReportScope.SELF: (
                    WorkspacePermission
                    .MONITORING_SELF_READ
                    .value
                ),
                ReportScope.TEAM: (
                    WorkspacePermission
                    .MONITORING_TEAM_READ
                    .value
                ),
                ReportScope.WORKSPACE: (
                    WorkspacePermission
                    .MONITORING_ALL_READ
                    .value
                ),
            }[
                report_scope
            ]

        elif report == ReportKey.PAYROLL:
            permission = (
                WorkspacePermission
                .COMPENSATION_SELF_READ
                .value
                if (
                    report_scope
                    == ReportScope.SELF
                )
                else (
                    WorkspacePermission
                    .PAYROLL_READ
                    .value
                )
            )

        elif report == ReportKey.AUDIT:
            if (
                report_scope
                != ReportScope.WORKSPACE
            ):
                raise ValidationError(
                    "Audit reports require "
                    "workspace scope."
                )

            permission = (
                WorkspacePermission
                .AUDIT_READ
                .value
            )

        else:
            raise ValidationError(
                "Unsupported report."
            )

        self.permissions.require_any(
            {
                permission,
            }
        )

    # =====================================================
    # EMPLOYEE SCOPE
    # =====================================================

    async def _actor_employee(
        self,
    ) -> Employee | None:
        result = await (
            self.session.execute(
                select(
                    Employee
                ).where(
                    Employee.user_id
                    == self.scope.user_id,

                    Employee.is_active
                    .is_(
                        True
                    ),
                )
            )
        )

        return (
            result.scalar_one_or_none()
        )

    async def _base_employee_ids(
        self,
        report_scope: ReportScope,
    ) -> (
        frozenset[uuid.UUID]
        | None
    ):
        if (
            report_scope
            == ReportScope.WORKSPACE
        ):
            return None

        actor = await (
            self._actor_employee()
        )

        if actor is None:
            return frozenset()

        if (
            report_scope
            == ReportScope.SELF
        ):
            return frozenset(
                {
                    actor.id,
                }
            )

        if actor.team_id is None:
            return frozenset(
                {
                    actor.id,
                }
            )

        result = await (
            self.session.execute(
                select(
                    Employee.id
                ).where(
                    Employee.team_id
                    == actor.team_id,

                    Employee.is_active
                    .is_(
                        True
                    ),
                )
            )
        )

        return frozenset(
            result.scalars().all()
        )

    async def _filtered_employee_ids(
        self,
        request: ReportRunRequest,
    ) -> (
        frozenset[uuid.UUID]
        | None
    ):
        base = await (
            self._base_employee_ids(
                request.scope
            )
        )

        has_filter = any(
            value is not None
            for value in (
                request.employee_id,
                request.team_id,
                request.department_id,
            )
        )

        if not has_filter:
            return base

        statement = select(
            Employee.id
        ).where(
            Employee.is_active.is_(
                True
            )
        )

        if (
            request.employee_id
            is not None
        ):
            statement = (
                statement.where(
                    Employee.id
                    == request.employee_id
                )
            )

        if request.team_id is not None:
            statement = (
                statement.where(
                    Employee.team_id
                    == request.team_id
                )
            )

        if (
            request.department_id
            is not None
        ):
            statement = (
                statement.where(
                    Employee.department_id
                    == request.department_id
                )
            )

        result = await (
            self.session.execute(
                statement
            )
        )

        filtered = frozenset(
            result.scalars().all()
        )

        if base is None:
            return filtered

        return frozenset(
            filtered.intersection(
                base
            )
        )

    # =====================================================
    # ANALYTICS ADAPTER
    # =====================================================

    async def _analytics_access(
        self,
        request: ReportRunRequest,
    ) -> AnalyticsAccess:
        employee_ids = await (
            self._filtered_employee_ids(
                request
            )
        )

        analytics_scope = {
            ReportScope.SELF: (
                AnalyticsScope.SELF
            ),
            ReportScope.TEAM: (
                AnalyticsScope.TEAM
            ),
            ReportScope.WORKSPACE: (
                AnalyticsScope.ALL
            ),
        }[
            request.scope
        ]

        return AnalyticsAccess(
            workspace_id=(
                self.workspace_id
            ),
            actor_user_id=(
                self.scope.user_id
            ),
            role_key=(
                self.scope.role_key
            ),
            scope=analytics_scope,
            employee_ids=employee_ids,
        )

    def _window(
        self,
        request: ReportRunRequest,
    ):
        return (
            AnalyticsService
            .resolve_window(
                start_at=(
                    request.start_at
                ),
                end_at=(
                    request.end_at
                ),
            )
        )

    async def _attendance(
        self,
        request: ReportRunRequest,
    ) -> dict:
        access = await (
            self._analytics_access(
                request
            )
        )

        payload = await (
            AnalyticsService(
                self.session
            )
            .attendance(
                workspace_id=(
                    self.workspace_id
                ),
                access=access,
                window=self._window(
                    request
                ),
            )
        )

        return payload.model_dump(
            mode="json"
        )

    async def _productivity(
        self,
        request: ReportRunRequest,
    ) -> dict:
        access = await (
            self._analytics_access(
                request
            )
        )

        payload = await (
            AnalyticsService(
                self.session
            )
            .productivity(
                workspace_id=(
                    self.workspace_id
                ),
                access=access,
                window=self._window(
                    request
                ),
            )
        )

        return payload.model_dump(
            mode="json"
        )

    async def _goals(
        self,
        request: ReportRunRequest,
    ) -> dict:
        access = await (
            self._analytics_access(
                request
            )
        )

        payload = await (
            AnalyticsService(
                self.session
            )
            .goals(
                workspace_id=(
                    self.workspace_id
                ),
                access=access,
                window=self._window(
                    request
                ),
            )
        )

        return payload.model_dump(
            mode="json"
        )

    async def _monitoring_summary(
        self,
        request: ReportRunRequest,
    ) -> dict:
        access = await (
            self._analytics_access(
                request
            )
        )

        payload = await (
            AnalyticsService(
                self.session
            )
            .overview(
                workspace_id=(
                    self.workspace_id
                ),
                access=access,
                window=self._window(
                    request
                ),
            )
        )

        data = payload.model_dump(
            mode="json"
        )

        return {
            "workspace_id": data[
                "workspace_id"
            ],
            "scope": data["scope"],
            "window": data[
                "window"
            ],
            "employees": data[
                "employees"
            ],
            "activity_events": data[
                "activity_events"
            ],
            "active_events": data[
                "active_events"
            ],
            "idle_events": data[
                "idle_events"
            ],
            "app_seconds": data[
                "app_seconds"
            ],
            "website_seconds": data[
                "website_seconds"
            ],
        }

    # =====================================================
    # DEVICE HEALTH
    # =====================================================

    async def _device_health(
        self,
        request: ReportRunRequest,
    ) -> dict:
        domain_access = await (
            resolve_device_readiness_access(
                workspace_id=(
                    self.workspace_id
                ),
                context=self.scope,
            )
        )

        payload = await (
            DeviceReadinessService(
                self.session
            )
            .get_readiness(
                access=domain_access
            )
        )

        data = payload.model_dump(
            mode="json"
        )

        allowed_ids = await (
            self._filtered_employee_ids(
                request
            )
        )

        devices = data.get(
            "devices",
            [],
        )

        if allowed_ids is not None:
            allowed_text = {
                str(
                    employee_id
                )
                for employee_id
                in allowed_ids
            }

            devices = [
                item
                for item
                in devices
                if (
                    item.get(
                        "employee_id"
                    )
                    in allowed_text
                )
            ]

        if request.status:
            expected = (
                request.status
                .strip()
                .lower()
            )

            devices = [
                item
                for item
                in devices
                if (
                    str(
                        item.get(
                            "status",
                            "",
                        )
                    )
                    .lower()
                    == expected
                )
            ]

        summary = {
            "total": len(
                devices
            ),
            "online": sum(
                1
                for item
                in devices
                if item.get(
                    "status"
                )
                == "online"
            ),
            "offline": sum(
                1
                for item
                in devices
                if item.get(
                    "status"
                )
                == "offline"
            ),
            "disabled": sum(
                1
                for item
                in devices
                if item.get(
                    "status"
                )
                == "disabled"
            ),
            "monitoring_ready": sum(
                1
                for item
                in devices
                if item.get(
                    "monitoring_ready"
                )
                is True
            ),
            "live_ready": sum(
                1
                for item
                in devices
                if item.get(
                    "live_ready"
                )
                is True
            ),
            "needs_setup": sum(
                1
                for item
                in devices
                if item.get(
                    "needs_setup"
                )
                is True
            ),
        }

        return {
            "summary": summary,
            "devices": devices[
                : request.limit
            ],
        }

    # =====================================================
    # PAYROLL
    # =====================================================

    async def _payroll(
        self,
        request: ReportRunRequest,
    ) -> dict:
        employee_ids = await (
            self._filtered_employee_ids(
                request
            )
        )

        service = PayrollService(
            self.session
        )

        runs = await service.list_runs()

        items: list[dict] = []

        start_date = (
            request.start_at.date()
            if request.start_at
            is not None
            else None
        )

        end_date = (
            request.end_at.date()
            if request.end_at
            is not None
            else None
        )

        for run in runs:
            if (
                start_date is not None
                and run.period_end
                < start_date
            ):
                continue

            if (
                end_date is not None
                and run.period_start
                >= end_date
            ):
                continue

            if (
                request.status
                is not None
                and str(
                    _enum_value(
                        run.status
                    )
                ).lower()
                != (
                    request.status
                    .strip()
                    .lower()
                )
            ):
                continue

            calculations = await (
                service
                .list_calculations(
                    run_id=run.id
                )
            )

            rows = []

            for calculation in (
                calculations
            ):
                if (
                    employee_ids
                    is not None
                    and (
                        calculation
                        .employee_id
                        not in employee_ids
                    )
                ):
                    continue

                rows.append(
                    {
                        "employee_id": str(
                            calculation
                            .employee_id
                        ),
                        "status": str(
                            _enum_value(
                                calculation
                                .status
                            )
                        ),
                        "currency": (
                            calculation
                            .currency
                        ),
                        "payable_minutes": (
                            calculation
                            .payable_minutes
                        ),
                        "gross_pay": str(
                            calculation
                            .gross_pay
                        ),
                        "net_pay": str(
                            calculation
                            .net_pay
                        ),
                    }
                )

            if (
                employee_ids is not None
                and not rows
            ):
                continue

            items.append(
                {
                    "run_id": str(
                        run.id
                    ),
                    "period_start": (
                        run.period_start
                        .isoformat()
                    ),
                    "period_end": (
                        run.period_end
                        .isoformat()
                    ),
                    "currency": (
                        run.currency
                    ),
                    "status": str(
                        _enum_value(
                            run.status
                        )
                    ),
                    "policy_version": (
                        run.policy_version
                    ),
                    "calculations": rows,
                }
            )

            if (
                len(
                    items
                )
                >= request.limit
            ):
                break

        return {
            "runs": items,
            "total": len(
                items
            ),
        }

    # =====================================================
    # AUDIT
    # =====================================================

    async def _audit(
        self,
        request: ReportRunRequest,
    ) -> dict:
        outcome = None

        if request.status:
            candidate = (
                request.status
                .strip()
                .lower()
            )

            if candidate in {
                "success",
                "failure",
            }:
                outcome = candidate

        payload = await (
            AuditLogService(
                self.session
            )
            .list_events(
                workspace_id=(
                    self.workspace_id
                ),
                category=None,
                action=None,
                actor_user_id=None,
                target_type=None,
                target_id=None,
                outcome=outcome,
                severity=None,
                start_at=(
                    request.start_at
                ),
                end_at=(
                    request.end_at
                ),
                limit=min(
                    request.limit,
                    5000,
                ),
                offset=0,
            )
        )

        return payload.model_dump(
            mode="json"
        )

    # =====================================================
    # EXECUTE
    # =====================================================

    async def run(
        self,
        request: ReportRunRequest,
    ) -> ReportRunResponse:
        require_report_scope(
            self.reports_access,
            request.scope,
        )

        self._require_domain_permission(
            request=request
        )

        if (
            request.report
            == ReportKey.ATTENDANCE
        ):
            data = await self._attendance(
                request
            )

        elif (
            request.report
            == ReportKey.PRODUCTIVITY
        ):
            data = await self._productivity(
                request
            )

        elif (
            request.report
            == ReportKey.GOALS
        ):
            data = await self._goals(
                request
            )

        elif (
            request.report
            == ReportKey.DEVICE_HEALTH
        ):
            data = await self._device_health(
                request
            )

        elif (
            request.report
            == ReportKey.MONITORING_SUMMARY
        ):
            data = await (
                self._monitoring_summary(
                    request
                )
            )

        elif (
            request.report
            == ReportKey.PAYROLL
        ):
            data = await self._payroll(
                request
            )

        elif (
            request.report
            == ReportKey.AUDIT
        ):
            data = await self._audit(
                request
            )

        else:
            raise ValidationError(
                "Unsupported report."
            )

        return ReportRunResponse(
            workspace_id=(
                self.workspace_id
            ),
            report=request.report,
            scope=request.scope,
            generated_at=_now(),
            parameters=(
                ReportParametersResponse(
                    start_at=(
                        request.start_at
                    ),
                    end_at=(
                        request.end_at
                    ),
                    employee_id=(
                        request.employee_id
                    ),
                    team_id=(
                        request.team_id
                    ),
                    department_id=(
                        request.department_id
                    ),
                    status=(
                        request.status
                    ),
                    limit=request.limit,
                )
            ),
            data=data,
        )


__all__ = [
    "ReportExecutionService",
]