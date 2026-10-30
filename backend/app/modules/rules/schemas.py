from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RuleCondition(BaseModel):
    field: str = Field(..., min_length=1, max_length=100)
    operator: str = Field(
        ...,
        pattern=r"^(equals|not_equals|contains|greater_than|less_than)$",
    )
    value: Any


class RuleAction(BaseModel):
    action_type: str = Field(
        ...,
        pattern=r"^(notify|block|challenge|tag|webhook)$",
    )
    parameters: dict[str, Any] = Field(default_factory=dict)


class RuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    event_type: str = Field(..., min_length=1, max_length=100)
    conditions: list[RuleCondition] = Field(default_factory=list)
    actions: list[RuleAction] = Field(..., min_length=1)


class RuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    event_type: str | None = Field(default=None, min_length=1, max_length=100)
    conditions: list[RuleCondition] | None = None
    actions: list[RuleAction] | None = None
    is_enabled: bool | None = None


class RulePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    event_type: str
    conditions: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    is_enabled: bool
    created_at: datetime
    updated_at: datetime