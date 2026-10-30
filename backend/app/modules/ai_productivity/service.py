from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_productivity.config import (
    get_ai_productivity_settings,
)
from app.modules.ai_productivity.context_service import (
    AIProductivityContextService,
)
from app.modules.ai_productivity.enums import (
    AIProductivityAction,
)
from app.modules.ai_productivity.privacy import (
    sanitize_ai_context,
)
from app.modules.ai_productivity.provider import (
    AIProductivityProvider,
    get_ai_productivity_provider,
)
from app.modules.ai_productivity.schemas import (
    AIProductivityCapabilitiesResponse,
    AIProductivityCapability,
    AIProductivityRequest,
    AIProductivityResponse,
)


class AIProductivityService:
    def __init__(
        self,
        session: AsyncSession,
        provider: (
            AIProductivityProvider
            | None
        ) = None,
    ) -> None:
        self.session = session

        self.context_service = (
            AIProductivityContextService(
                session
            )
        )

        self.provider = (
            provider
            or get_ai_productivity_provider()
        )

        self.settings = (
            get_ai_productivity_settings()
        )

    def capabilities(
        self,
    ) -> AIProductivityCapabilitiesResponse:
        provider_info = (
            self.provider.info()
        )

        enabled = (
            provider_info
            .external_processing_enabled
        )

        return (
            AIProductivityCapabilitiesResponse(
                provider=provider_info,
                capabilities=[
                    AIProductivityCapability(
                        action=action,
                        enabled=enabled,
                    )
                    for action
                    in AIProductivityAction
                ],
            )
        )

    async def execute(
        self,
        *,
        actor_user_id: uuid.UUID,
        request: AIProductivityRequest,
    ) -> AIProductivityResponse:
        raw_context = await (
            self.context_service
            .build_context(
                actor_user_id=(
                    actor_user_id
                ),
                sources=request.sources,
                max_items_per_source=(
                    request
                    .max_items_per_source
                ),
            )
        )

        safe_context = sanitize_ai_context(
            raw_context,
            max_item_characters=(
                self.settings
                .max_item_characters
            ),
            max_context_characters=(
                self.settings
                .max_context_characters
            ),
        )

        output = await (
            self.provider.generate(
                action=request.action,
                instruction=(
                    request.instruction
                ),
                context=safe_context,
            )
        )

        return AIProductivityResponse(
            action=request.action,
            output=output,
            context_items_used=(
                safe_context.total_items
            ),
            provider=(
                self.provider.info()
            ),
        )


__all__ = [
    "AIProductivityService",
]