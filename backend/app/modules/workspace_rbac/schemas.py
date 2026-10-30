from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkspaceRBACSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


class PermissionCatalogResponse(WorkspaceRBACSchema):
    permissions: list[str]


class WorkspaceRoleCreateRequest(WorkspaceRBACSchema):
    role_key: str = Field(min_length=2, max_length=64)
    display_name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    permissions: list[str] = Field(default_factory=list)

    @field_validator("role_key")
    @classmethod
    def validate_role_key(cls, value: str) -> str:
        normalized = value.strip().lower()

        if not re.fullmatch("[a-z0-9_]+", normalized):
            raise ValueError(
                "role_key may contain only lowercase letters, "
                "numbers, and underscores."
            )

        return normalized


class WorkspaceRoleUpdateRequest(WorkspaceRBACSchema):
    display_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )
    description: str | None = Field(default=None, max_length=500)
    permissions: list[str] | None = None
    is_active: bool | None = None


class WorkspaceRolePublic(WorkspaceRBACSchema):
    id: uuid.UUID | None = None
    role_key: str
    display_name: str
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)
    is_builtin: bool
    is_immutable: bool
    is_active: bool = True


class WorkspaceRoleListResponse(WorkspaceRBACSchema):
    roles: list[WorkspaceRolePublic]


class WorkspaceMemberRoleUpdateRequest(WorkspaceRBACSchema):
    role_key: str = Field(min_length=1, max_length=64)


class WorkspaceMemberModerationPublic(WorkspaceRBACSchema):
    is_banned: bool = False
    is_muted: bool = False
    is_deafened: bool = False
    is_hidden: bool = False


class WorkspaceMemberPublic(WorkspaceRBACSchema):
    membership_id: uuid.UUID
    user_id: uuid.UUID
    email: str
    username: str
    role_key: str
    status: str
    moderation: WorkspaceMemberModerationPublic
    role_keys: list[str] = Field(default_factory=list)


class WorkspaceMemberListResponse(WorkspaceRBACSchema):
    workspace_id: uuid.UUID
    members: list[WorkspaceMemberPublic]


class WorkspaceMemberVisibilityRequest(WorkspaceRBACSchema):
    hidden: bool


class WorkspaceModerationActionResponse(WorkspaceRBACSchema):
    message: str
    membership_id: uuid.UUID
    moderation: WorkspaceMemberModerationPublic


class WorkspaceBootstrapResponse(WorkspaceRBACSchema):
    workspace_id: uuid.UUID
    membership_id: uuid.UUID
    role_key: str
    permissions: list[str]
    moderation: WorkspaceMemberModerationPublic
    available_roles: list[WorkspaceRolePublic]
    role_keys: list[str] = Field(default_factory=list)


class WorkspaceMemberRolesResponse(WorkspaceRBACSchema):
    workspace_id: uuid.UUID
    membership_id: uuid.UUID
    primary_role_key: str
    additional_role_keys: list[str]
    effective_role_keys: list[str]
    permissions: list[str]


__all__ = [
    "PermissionCatalogResponse",
    "WorkspaceRoleCreateRequest",
    "WorkspaceRoleUpdateRequest",
    "WorkspaceRolePublic",
    "WorkspaceRoleListResponse",
    "WorkspaceMemberRoleUpdateRequest",
    "WorkspaceMemberModerationPublic",
    "WorkspaceMemberPublic",
    "WorkspaceMemberListResponse",
    "WorkspaceMemberVisibilityRequest",
    "WorkspaceModerationActionResponse",
    "WorkspaceBootstrapResponse",
    "WorkspaceMemberRolesResponse",
]