from __future__ import annotations

from dataclasses import (
    dataclass,
)

from app.core.exceptions import (
    ValidationError,
)
from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.reports.schemas import (
    ReportScope,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


@dataclass(
    frozen=True,
    slots=True,
)
class ReportsAccess:
    can_read_self: bool

    can_read_team: bool

    can_read_workspace: bool

    can_export: bool

    @property
    def effective_scopes(
        self,
    ) -> list[
        ReportScope
    ]:
        scopes: list[
            ReportScope
        ] = []

        if self.can_read_self:
            scopes.append(
                ReportScope.SELF
            )

        if self.can_read_team:
            scopes.append(
                ReportScope.TEAM
            )

        if self.can_read_workspace:
            scopes.append(
                ReportScope.WORKSPACE
            )

        return scopes


def resolve_reports_access(
    scope: TenantScope,
) -> ReportsAccess:
    permissions = (
        WorkspacePermissionService(
            scope
        )
    )

    can_read_self = (
        permissions.has(
            WorkspacePermission
            .REPORTS_SELF_READ
            .value
        )
    )

    can_read_team = (
        permissions.has(
            WorkspacePermission
            .REPORTS_TEAM_READ
            .value
        )
    )

    can_read_workspace = (
        permissions.has(
            WorkspacePermission
            .REPORTS_ALL_READ
            .value
        )
    )

    can_export = (
        permissions.has(
            WorkspacePermission
            .REPORTS_EXPORT
            .value
        )
    )

    if not (
        can_read_self
        or can_read_team
        or can_read_workspace
    ):
        permissions.require_any(
            {
                WorkspacePermission
                .REPORTS_SELF_READ
                .value,

                WorkspacePermission
                .REPORTS_TEAM_READ
                .value,

                WorkspacePermission
                .REPORTS_ALL_READ
                .value,
            }
        )

    return ReportsAccess(
        can_read_self=(
            can_read_self
        ),
        can_read_team=(
            can_read_team
        ),
        can_read_workspace=(
            can_read_workspace
        ),
        can_export=(
            can_export
        ),
    )


def require_report_scope(
    access: ReportsAccess,
    requested_scope: ReportScope,
) -> None:
    allowed = set(
        access.effective_scopes
    )

    if (
        requested_scope
        not in allowed
    ):
        raise ValidationError(
            "Requested report scope is "
            "not permitted."
        )


def require_report_export(
    access: ReportsAccess,
) -> None:
    if not access.can_export:
        raise ValidationError(
            "Report export permission "
            "required."
        )


__all__ = [
    "ReportsAccess",
    "resolve_reports_access",
    "require_report_scope",
    "require_report_export",
]