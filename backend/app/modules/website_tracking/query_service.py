from __future__ import annotations

import uuid

from app.modules.website_tracking.repository import (
    WebsiteTrackingRepository,
)
from app.modules.website_tracking.status_schemas import (
    CurrentWebsiteStatusResponse,
)


class WebsiteTrackingQueryService:
    def __init__(
        self,
        repository: WebsiteTrackingRepository,
    ) -> None:
        self._repository = repository

    async def get_current_status(
        self,
        *,
        device_id: uuid.UUID,
    ) -> CurrentWebsiteStatusResponse:
        interval = (
            await self._repository
            .get_open_interval(
                device_id=device_id,
                for_update=False,
            )
        )

        if interval is None:
            return CurrentWebsiteStatusResponse(
                device_id=device_id,
                has_active_website=False,
                duration_seconds=0,
            )

        return CurrentWebsiteStatusResponse(
            device_id=device_id,
            has_active_website=True,
            interval_id=interval.id,
            employee_id=interval.employee_id,
            browser_name=interval.browser_name,
            browser_process_name=(
                interval.browser_process_name
            ),
            domain=interval.domain,
            normalized_domain=(
                interval.normalized_domain
            ),
            started_at=interval.started_at,
            last_observed_at=(
                interval.last_observed_at
            ),
            duration_seconds=(
                interval.duration_seconds
            ),
            page_url=interval.last_page_url,
            page_title=interval.last_page_title,
        )


__all__ = [
    "WebsiteTrackingQueryService",
]