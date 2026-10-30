from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TaskCreated:
    workspace_id: UUID
    task_id: UUID
    actor_user_id: UUID


@dataclass(frozen=True, slots=True)
class TaskAssigned:
    workspace_id: UUID
    task_id: UUID
    assignee_employee_id: UUID | None
    actor_user_id: UUID


@dataclass(frozen=True, slots=True)
class TaskStatusChanged:
    workspace_id: UUID
    task_id: UUID
    status: str
    actor_user_id: UUID