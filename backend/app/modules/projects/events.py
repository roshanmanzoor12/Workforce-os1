from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProjectCreated:
    workspace_id: UUID
    project_id: UUID
    actor_user_id: UUID


@dataclass(frozen=True, slots=True)
class ProjectUpdated:
    workspace_id: UUID
    project_id: UUID
    actor_user_id: UUID


@dataclass(frozen=True, slots=True)
class ProjectDeleted:
    workspace_id: UUID
    project_id: UUID
    actor_user_id: UUID