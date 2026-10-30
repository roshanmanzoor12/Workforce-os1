from __future__ import annotations

import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.workspace_search.enums import (
    SearchEntityType,
)


class SearchSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )


class SearchResult(
    SearchSchema
):
    entity_type: SearchEntityType

    entity_id: uuid.UUID

    title: str

    subtitle: str | None = None

    matched_fields: list[str] = Field(
        default_factory=list
    )

    score: float = Field(
        ge=0.0,
    )

    resource_path: str


class WorkspaceSearchResponse(
    SearchSchema
):
    query: str

    items: list[
        SearchResult
    ] = Field(
        default_factory=list
    )

    total: int

    limit: int

    searched_types: list[
        SearchEntityType
    ] = Field(
        default_factory=list
    )


class SearchCapabilitiesResponse(
    SearchSchema
):
    available_types: list[
        SearchEntityType
    ] = Field(
        default_factory=list
    )

    min_query_length: int = 2

    max_results: int = 100


__all__ = [
    "SearchResult",
    "WorkspaceSearchResponse",
    "SearchCapabilitiesResponse",
]