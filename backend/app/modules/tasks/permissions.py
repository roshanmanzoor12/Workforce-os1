from app.db.tenant_dependency import TenantScope
from app.modules.workspace_permissions.service import WorkspacePermissionService

TASKS_VIEW = "tasks.view"
TASKS_MANAGE = "tasks.manage"


def require_task_permission(scope: TenantScope, *, manage: bool = False):
    permission = TASKS_MANAGE if manage else TASKS_VIEW
    WorkspacePermissionService(scope).require(permission)