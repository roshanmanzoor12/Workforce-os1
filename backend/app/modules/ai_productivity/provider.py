from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.modules.ai_productivity.config import (
    get_ai_productivity_settings,
)
from app.modules.ai_productivity.enums import (
    AIProductivityAction,
    AIProviderStatus,
)
from app.modules.ai_productivity.schemas import (
    AIProductivityContext,
    AIProviderInfo,
)


class AIProductivityProvider(
    Protocol
):
    def info(
        self,
    ) -> AIProviderInfo:
        ...

    async def generate(
        self,
        *,
        action: AIProductivityAction,
        instruction: str | None,
        context: AIProductivityContext,
    ) -> str:
        ...


class AIProviderUnavailableError(
    RuntimeError
):
    pass


@dataclass(
    slots=True,
)
class DisabledAIProductivityProvider:
    provider_key: str = "disabled"

    def info(
        self,
    ) -> AIProviderInfo:
        return AIProviderInfo(
            status=(
                AIProviderStatus.DISABLED
            ),
            provider_key=(
                self.provider_key
            ),
            model_key=None,
            external_processing_enabled=False,
        )

    async def generate(
        self,
        *,
        action: AIProductivityAction,
        instruction: str | None,
        context: AIProductivityContext,
    ) -> str:
        raise AIProviderUnavailableError(
            "AI productivity provider "
            "is not configured."
        )


def get_ai_productivity_provider(
) -> AIProductivityProvider:
    settings = (
        get_ai_productivity_settings()
    )

    if not settings.enabled:
        return (
            DisabledAIProductivityProvider()
        )

    if (
        not settings
        .allow_external_processing
    ):
        return (
            DisabledAIProductivityProvider(
                provider_key=(
                    "external_processing_disabled"
                )
            )
        )

    if (
        settings.provider_key
        == "http_json"
    ):
        if not settings.endpoint:
            return (
                DisabledAIProductivityProvider(
                    provider_key=(
                        "http_json_unconfigured"
                    )
                )
            )

        from app.modules.ai_productivity.http_provider import (
            HTTPJSONAIProductivityProvider,
        )

        return (
            HTTPJSONAIProductivityProvider(
                settings=settings
            )
        )

    return (
        DisabledAIProductivityProvider(
            provider_key=(
                settings.provider_key
                or "disabled"
            )
        )
    )


__all__ = [
    "AIProductivityProvider",
    "AIProviderUnavailableError",
    "DisabledAIProductivityProvider",
    "get_ai_productivity_provider",
]