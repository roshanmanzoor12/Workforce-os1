from __future__ import annotations

import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class WorkspacePermissionSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )


class WorkspacePermissionCheckResponse(
    WorkspacePermissionSchema
):
    permission: str = Field(
        min_length=1,
        max_length=128,
    )

    allowed: bool


class WorkspacePermissionListResponse(
    WorkspacePermissionSchema
):
    role_key: str = Field(
        min_length=1,
        max_length=64,
    )

    permissions: list[
        str
    ] = Field(
        default_factory=list,
    )

    total: int = Field(
        ge=0,
    )


class WorkspacePermissionCatalogResponse(
    WorkspacePermissionSchema
):
    permissions: list[
        str
    ] = Field(
        default_factory=list,
    )

    total: int = Field(
        ge=0,
    )


class WorkspacePermissionCheckRequest(
    WorkspacePermissionSchema
):
    permissions: list[
        str
    ] = Field(
        min_length=1,
        max_length=100,
    )


class WorkspacePermissionCheckManyResponse(
    WorkspacePermissionSchema
):
    workspace_id: uuid.UUID

    role_key: str = Field(
        min_length=1,
        max_length=64,
    )

    results: dict[
        str,
        bool,
    ] = Field(
        default_factory=dict,
    )

    allows_all: bool
    allows_any: bool


class WorkspaceRoleResponse(
    WorkspacePermissionSchema
):
    key: str = Field(
        min_length=1,
        max_length=64,
    )

    label: str = Field(
        min_length=1,
        max_length=128,
    )

    permissions: list[
        str
    ] = Field(
        default_factory=list,
    )


class WorkspaceRoleListResponse(
    WorkspacePermissionSchema
):
    workspace_id: uuid.UUID

    items: list[
        WorkspaceRoleResponse
    ] = Field(
        default_factory=list,
    )


class WorkspacePermissionWorkspaceListResponse(
    WorkspacePermissionSchema
):
    workspace_id: uuid.UUID

    role_key: str = Field(
        min_length=1,
        max_length=64,
    )

    permissions: list[
        str
    ] = Field(
        default_factory=list,
    )


__all__ = [
    "WorkspacePermissionSchema",
    "WorkspacePermissionCheckResponse",
    "WorkspacePermissionListResponse",
    "WorkspacePermissionCatalogResponse",
    "WorkspacePermissionCheckRequest",
    "WorkspacePermissionCheckManyResponse",
    "WorkspaceRoleResponse",
    "WorkspaceRoleListResponse",
    "WorkspacePermissionWorkspaceListResponse",
]