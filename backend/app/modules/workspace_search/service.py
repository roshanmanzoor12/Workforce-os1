from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.exceptions import (
    ValidationError,
)
from app.modules.workspace_search.access import (
    SearchAccess,
)
from app.modules.workspace_search.enums import (
    SEARCH_ENTITY_TYPES,
    SearchEntityType,
)
from app.modules.workspace_search.ranking import (
    combined_score,
)
from app.modules.workspace_search.repository import (
    SearchCandidate,
    WorkspaceSearchRepository,
)
from app.modules.workspace_search.schemas import (
    SearchCapabilitiesResponse,
    SearchResult,
    WorkspaceSearchResponse,
)


class WorkspaceSearchService:
    MIN_QUERY_LENGTH = 2
    MAX_RESULTS = 100

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            WorkspaceSearchRepository(
                session
            )
        )

    @staticmethod
    def _normalize_query(
        query: str,
    ) -> str:
        return " ".join(
            query
            .strip()
            .split()
        )

    @classmethod
    def _validate_query(
        cls,
        query: str,
    ) -> str:
        normalized = (
            cls._normalize_query(
                query
            )
        )

        if (
            len(normalized)
            < cls.MIN_QUERY_LENGTH
        ):
            raise ValidationError(
                "Search query must contain "
                "at least 2 characters."
            )

        if len(normalized) > 200:
            raise ValidationError(
                "Search query cannot exceed "
                "200 characters."
            )

        return normalized

    @staticmethod
    def _requested_types(
        *,
        access: SearchAccess,
        requested: (
            list[SearchEntityType]
            | None
        ),
    ) -> list[
        SearchEntityType
    ]:
        allowed = set(
            access.available_types
        )

        if requested is None:
            return list(
                access.available_types
            )

        unique: list[
            SearchEntityType
        ] = []

        for item in requested:
            if (
                item in allowed
                and item not in unique
            ):
                unique.append(
                    item
                )

        return unique

    @staticmethod
    def _result(
        *,
        query: str,
        candidate: SearchCandidate,
    ) -> SearchResult | None:
        (
            score,
            matched_fields,
        ) = combined_score(
            query=query,
            fields=list(
                candidate
                .searchable_fields
            ),
        )

        if score <= 0:
            return None

        return SearchResult(
            entity_type=(
                candidate.entity_type
            ),
            entity_id=(
                candidate.entity_id
            ),
            title=(
                candidate.title
            ),
            subtitle=(
                candidate.subtitle
            ),
            matched_fields=(
                matched_fields
            ),
            score=score,
            resource_path=(
                candidate
                .resource_path
            ),
        )

    async def search(
        self,
        *,
        query: str,
        access: SearchAccess,
        requested_types: (
            list[SearchEntityType]
            | None
        ),
        limit: int,
    ) -> WorkspaceSearchResponse:
        normalized = (
            self._validate_query(
                query
            )
        )

        limit = min(
            max(
                limit,
                1,
            ),
            self.MAX_RESULTS,
        )

        types = (
            self._requested_types(
                access=access,
                requested=(
                    requested_types
                ),
            )
        )

        if not types:
            return WorkspaceSearchResponse(
                query=normalized,
                items=[],
                total=0,
                limit=limit,
                searched_types=[],
            )

        # We intentionally execute these sequentially.
        #
        # Every provider uses the same AsyncSession and
        # SQLAlchemy AsyncSession must not run concurrent
        # operations through asyncio.gather().
        provider_limit = min(
            max(
                limit,
                20,
            ),
            100,
        )

        candidates: list[
            SearchCandidate
        ] = []

        for entity_type in types:
            if (
                entity_type
                == SearchEntityType
                .EMPLOYEE
            ):
                candidates.extend(
                    await (
                        self.repository
                        .employees(
                            query=normalized,
                            access=access,
                            limit=provider_limit,
                        )
                    )
                )

            elif (
                entity_type
                == SearchEntityType
                .GOAL
            ):
                candidates.extend(
                    await (
                        self.repository
                        .goals(
                            query=normalized,
                            access=access,
                            limit=provider_limit,
                        )
                    )
                )

            elif (
                entity_type
                == SearchEntityType
                .NOTE
            ):
                candidates.extend(
                    await (
                        self.repository
                        .notes(
                            query=normalized,
                            access=access,
                            limit=provider_limit,
                        )
                    )
                )

            elif (
                entity_type
                == SearchEntityType
                .KNOWLEDGE
            ):
                candidates.extend(
                    await (
                        self.repository
                        .knowledge(
                            query=normalized,
                            access=access,
                            limit=provider_limit,
                        )
                    )
                )

            elif (
                entity_type
                == SearchEntityType
                .MEETING
            ):
                candidates.extend(
                    await (
                        self.repository
                        .meetings(
                            query=normalized,
                            access=access,
                            limit=provider_limit,
                        )
                    )
                )

        results: list[
            SearchResult
        ] = []

        seen: set[
            tuple[
                SearchEntityType,
                object,
            ]
        ] = set()

        for candidate in candidates:
            key = (
                candidate.entity_type,
                candidate.entity_id,
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            result = self._result(
                query=normalized,
                candidate=candidate,
            )

            if result is not None:
                results.append(
                    result
                )

        results.sort(
            key=lambda item: (
                -item.score,
                item.entity_type.value,
                item.title.casefold(),
                str(item.entity_id),
            )
        )

        results = results[
            :limit
        ]

        return WorkspaceSearchResponse(
            query=normalized,
            items=results,
            total=len(
                results
            ),
            limit=limit,
            searched_types=types,
        )

    @staticmethod
    def capabilities(
        *,
        access: SearchAccess,
    ) -> SearchCapabilitiesResponse:
        return SearchCapabilitiesResponse(
            available_types=(
                access.available_types
            ),
            min_query_length=2,
            max_results=100,
        )


__all__ = [
    "WorkspaceSearchService",
]