from app.db.tenant_dependency import TenantScope
from app.modules.workspace_permissions.service import WorkspacePermissionService

PROJECTS_VIEW = "projects.view"
PROJECTS_MANAGE = "projects.manage"


def require_project_permission(scope: TenantScope, *, manage: bool = False):
    permission = PROJECTS_MANAGE if manage else PROJECTS_VIEW
    WorkspacePermissionService(scope).require(permission)