from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    monthly_price_cents: int = Field(default=0, ge=0)
    features: dict[str, Any] = Field(default_factory=dict)
    limits: dict[str, int | float | None] = Field(default_factory=dict)


class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    monthly_price_cents: int | None = Field(default=None, ge=0)
    features: dict[str, Any] | None = None
    limits: dict[str, int | float | None] | None = None


class PlanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None
    monthly_price_cents: int
    features: dict[str, Any]
    limits: dict[str, int | float | None]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LimitCheckRequest(BaseModel):
    feature: str = Field(min_length=1, max_length=120)
    current_usage: int | float = Field(default=0, ge=0)


class LimitCheckResponse(BaseModel):
    plan_id: UUID
    feature: str
    current_usage: int | float
    configured_limit: int | float | None
    allowed: bool