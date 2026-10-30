from __future__ import annotations

import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.ai_productivity.enums import (
    AIProductivityAction,
    AIProductivitySource,
    AIProviderStatus,
)


class AIProductivitySchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )


class AIProductivityRequest(
    AIProductivitySchema
):
    action: AIProductivityAction

    instruction: str | None = Field(
        default=None,
        max_length=4000,
    )

    sources: list[
        AIProductivitySource
    ] = Field(
        default_factory=lambda: [
            AIProductivitySource.GOALS,
            AIProductivitySource.NOTES,
            AIProductivitySource.KNOWLEDGE,
        ],
        max_length=3,
    )

    max_items_per_source: int = Field(
        default=20,
        ge=1,
        le=100,
    )


class AIContextItem(
    AIProductivitySchema
):
    source: AIProductivitySource

    id: uuid.UUID

    title: str

    content: str | None = None


class AIProductivityContext(
    AIProductivitySchema
):
    employee_id: uuid.UUID

    items: list[
        AIContextItem
    ]

    total_items: int = Field(
        ge=0,
    )


class AIProviderInfo(
    AIProductivitySchema
):
    status: AIProviderStatus

    provider_key: str

    model_key: str | None = None

    external_processing_enabled: bool


class AIProductivityResponse(
    AIProductivitySchema
):
    action: AIProductivityAction

    output: str

    context_items_used: int = Field(
        ge=0,
    )

    provider: AIProviderInfo


class AIProductivityCapability(
    AIProductivitySchema
):
    action: AIProductivityAction

    enabled: bool


class AIProductivityCapabilitiesResponse(
    AIProductivitySchema
):
    provider: AIProviderInfo

    capabilities: list[
        AIProductivityCapability
    ]


__all__ = [
    "AIProductivityRequest",
    "AIContextItem",
    "AIProductivityContext",
    "AIProviderInfo",
    "AIProductivityResponse",
    "AIProductivityCapability",
    "AIProductivityCapabilitiesResponse",
]