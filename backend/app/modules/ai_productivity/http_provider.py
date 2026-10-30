from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from app.modules.ai_productivity.config import (
    AIProductivitySettings,
)
from app.modules.ai_productivity.enums import (
    AIProductivityAction,
    AIProviderStatus,
)
from app.modules.ai_productivity.provider import (
    AIProviderUnavailableError,
)
from app.modules.ai_productivity.schemas import (
    AIProductivityContext,
    AIProviderInfo,
)


@dataclass(
    slots=True,
)
class HTTPJSONAIProductivityProvider:
    settings: AIProductivitySettings

    def info(
        self,
    ) -> AIProviderInfo:
        return AIProviderInfo(
            status=(
                AIProviderStatus.READY
            ),
            provider_key=(
                self.settings.provider_key
            ),
            model_key=(
                self.settings.model_key
            ),
            external_processing_enabled=True,
        )

    async def generate(
        self,
        *,
        action: AIProductivityAction,
        instruction: str | None,
        context: AIProductivityContext,
    ) -> str:
        return await asyncio.to_thread(
            self._generate_sync,
            action,
            instruction,
            context,
        )

    def _generate_sync(
        self,
        action: AIProductivityAction,
        instruction: str | None,
        context: AIProductivityContext,
    ) -> str:
        endpoint = (
            self.settings.endpoint
        )

        if not endpoint:
            raise (
                AIProviderUnavailableError(
                    "AI provider endpoint "
                    "is not configured."
                )
            )

        payload = {
            "model": (
                self.settings.model_key
            ),
            "action": action.value,
            "instruction": instruction,
            "context": (
                context.model_dump(
                    mode="json"
                )
            ),
        }

        body = json.dumps(
            payload
        ).encode(
            "utf-8"
        )

        headers = {
            "Content-Type": (
                "application/json"
            ),
            "Accept": (
                "application/json"
            ),
        }

        if (
            self.settings
            .bearer_token
        ):
            headers[
                "Authorization"
            ] = (
                "Bearer "
                + self.settings
                .bearer_token
            )

        request = urllib.request.Request(
            endpoint,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=(
                    self.settings
                    .request_timeout_seconds
                ),
            ) as response:
                raw = response.read()

        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
        ) as exc:
            raise (
                AIProviderUnavailableError(
                    "AI provider request "
                    "failed."
                )
            ) from exc

        try:
            decoded = json.loads(
                raw.decode(
                    "utf-8"
                )
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise (
                AIProviderUnavailableError(
                    "AI provider returned "
                    "an invalid JSON response."
                )
            ) from exc

        output = decoded.get(
            "output"
        )

        if (
            not isinstance(
                output,
                str,
            )
            or not output.strip()
        ):
            raise (
                AIProviderUnavailableError(
                    "AI provider response "
                    "did not contain output."
                )
            )

        return output.strip()


__all__ = [
    "HTTPJSONAIProductivityProvider",
]