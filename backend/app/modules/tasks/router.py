from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.db.tenant_dependency import TenantScope
from app.modules.tasks.permissions import require_task_permission
from app.modules.tasks.schemas import (
    TaskCreate,
    TaskList,
    TaskPublic,
    TaskStatus,
    TaskUpdate,
)
from app.modules.tasks.service import TaskService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/tasks",
    tags=["tasks"],
)


@router.post("", response_model=TaskPublic, status_code=201)
async def create_task(request: TaskCreate, scope: TenantScope):
    require_task_permission(scope, manage=True)
    result = await TaskService(scope.session).create(request)
    await scope.session.commit()
    return result


@router.get("", response_model=TaskList)
async def list_tasks(
    scope: TenantScope,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    project_id: UUID | None = None,
    assignee_employee_id: UUID | None = None,
    status: TaskStatus | None = None,
):
    require_task_permission(scope)
    items, total = await TaskService(scope.session).list(
        offset=offset,
        limit=limit,
        project_id=project_id,
        assignee_employee_id=assignee_employee_id,
        status=status,
    )
    return TaskList(
        items=[TaskPublic.model_validate(item) for item in items],
        total=total,
    )


@router.get("/{task_id}", response_model=TaskPublic)
async def get_task(task_id: UUID, scope: TenantScope):
    require_task_permission(scope)
    return await TaskService(scope.session).get(task_id)


@router.patch("/{task_id}", response_model=TaskPublic)
async def update_task(
    task_id: UUID,
    request: TaskUpdate,
    scope: TenantScope,
):
    require_task_permission(scope, manage=True)
    result = await TaskService(scope.session).update(task_id, request)
    await scope.session.commit()
    return result


@router.delete("/{task_id}", status_code=204, response_class=Response)
async def delete_task(task_id: UUID, scope: TenantScope):
    require_task_permission(scope, manage=True)
    await TaskService(scope.session).delete(task_id)
    await scope.session.commit()
    return Response(status_code=204)