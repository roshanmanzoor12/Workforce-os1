from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class WorkspaceCreationAccessResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    allowed: bool

    reason: str | None = None

    workspace_limit: int | None = Field(
        ge=0
    )

    workspace_count: int = Field(
        ge=0
    )
