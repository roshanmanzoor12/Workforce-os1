from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.modules.website_tracking.models import (
    WEBSITE_USAGE_STATUS_CLOSED,
    WebsiteUsageInterval,
)
from app.modules.website_tracking.privacy import (
    WebsiteTrackingPrivacyPolicy,
)
from app.modules.website_tracking.repository import (
    WebsiteTrackingRepository,
)
from app.modules.website_tracking.schemas import (
    WebsiteObservationProcessingResult,
    WebsiteObservationRequest,
    WebsiteObservationResponse,
    WebsiteUsageIntervalResponse,
)


class WebsiteTrackingService:
    MAXIMUM_CONTINUOUS_GAP = timedelta(
        minutes=10
    )

    def __init__(
        self,
        repository: WebsiteTrackingRepository,
        privacy_policy: (
            WebsiteTrackingPrivacyPolicy
            | None
        ) = None,
    ) -> None:
        self._repository = repository

        self._privacy_policy = (
            privacy_policy
            or WebsiteTrackingPrivacyPolicy()
        )

    async def record_observation(
        self,
        *,
        device_id: uuid.UUID,
        employee_id: uuid.UUID | None,
        request: WebsiteObservationRequest,
    ) -> WebsiteObservationProcessingResult:
        observed_at = (
            request.observed_at.astimezone(
                timezone.utc
            )
        )

        normalized_domain = (
            self._privacy_policy
            .sanitize_domain(
                request.domain
            )
        )

        page_url = (
            self._privacy_policy
            .sanitize_page_url(
                request.page_url
            )
        )

        page_title = (
            self._privacy_policy
            .sanitize_page_title(
                request.page_title
            )
        )

        open_interval = (
            await self._repository
            .get_open_interval(
                device_id=device_id,
                for_update=True,
            )
        )

        if (
            open_interval is not None
            and observed_at
            <= open_interval.last_observed_at
        ):
            return (
                WebsiteObservationProcessingResult(
                    observation=(
                        WebsiteObservationResponse(
                            id=uuid.uuid4(),
                            device_id=device_id,
                            employee_id=employee_id,
                            browser_name=request.browser_name,
                            browser_process_name=(
                                request.browser_process_name
                            ),
                            domain=request.domain,
                            normalized_domain=normalized_domain,
                            page_url=page_url,
                            page_title=page_title,
                            observed_at=observed_at,
                            received_at=datetime.now(
                                timezone.utc
                            ),
                            created_at=datetime.now(
                                timezone.utc
                            ),
                        )
                    ),
                    current_interval=(
                        WebsiteUsageIntervalResponse
                        .model_validate(
                            open_interval
                        )
                    ),
                    previous_interval_closed=False,
                    ignored_as_old=True,
                )
            )

        observation = (
            await self._repository
            .create_observation(
                device_id=device_id,
                employee_id=employee_id,
                browser_name=request.browser_name,
                browser_process_name=(
                    request.browser_process_name
                ),
                domain=request.domain,
                normalized_domain=normalized_domain,
                page_url=page_url,
                page_title=page_title,
                observed_at=observed_at,
            )
        )

        previous_interval_closed = False

        if open_interval is None:
            current_interval = (
                await self._repository
                .create_interval(
                    device_id=device_id,
                    employee_id=employee_id,
                    browser_name=request.browser_name,
                    browser_process_name=(
                        request.browser_process_name
                    ),
                    domain=request.domain,
                    normalized_domain=normalized_domain,
                    started_at=observed_at,
                    page_url=page_url,
                    page_title=page_title,
                )
            )

        else:
            gap = (
                observed_at
                - open_interval.last_observed_at
            )

            same_website = (
                open_interval.normalized_domain
                == normalized_domain
                and (
                    open_interval
                    .browser_process_name
                    .strip()
                    .lower()
                    == request
                    .browser_process_name
                    .strip()
                    .lower()
                )
            )

            if gap > self.MAXIMUM_CONTINUOUS_GAP:
                self._close_interval(
                    open_interval,
                    ended_at=(
                        open_interval
                        .last_observed_at
                    ),
                )

                previous_interval_closed = True

                current_interval = (
                    await self._repository
                    .create_interval(
                        device_id=device_id,
                        employee_id=employee_id,
                        browser_name=(
                            request.browser_name
                        ),
                        browser_process_name=(
                            request.browser_process_name
                        ),
                        domain=request.domain,
                        normalized_domain=normalized_domain,
                        started_at=observed_at,
                        page_url=page_url,
                        page_title=page_title,
                    )
                )

            elif same_website:
                elapsed_seconds = max(
                    0,
                    int(
                        gap.total_seconds()
                    ),
                )

                open_interval.duration_seconds += (
                    elapsed_seconds
                )

                open_interval.last_observed_at = (
                    observed_at
                )

                open_interval.domain = (
                    request.domain
                )

                open_interval.browser_name = (
                    request.browser_name
                )

                open_interval.last_page_url = (
                    page_url
                )

                open_interval.last_page_title = (
                    page_title
                )

                current_interval = (
                    open_interval
                )

            else:
                self._close_interval(
                    open_interval,
                    ended_at=observed_at,
                )

                previous_interval_closed = True

                current_interval = (
                    await self._repository
                    .create_interval(
                        device_id=device_id,
                        employee_id=employee_id,
                        browser_name=(
                            request.browser_name
                        ),
                        browser_process_name=(
                            request.browser_process_name
                        ),
                        domain=request.domain,
                        normalized_domain=normalized_domain,
                        started_at=observed_at,
                        page_url=page_url,
                        page_title=page_title,
                    )
                )

        await self._repository.commit()

        await self._repository.refresh(
            observation
        )

        await self._repository.refresh(
            current_interval
        )

        return WebsiteObservationProcessingResult(
            observation=(
                WebsiteObservationResponse
                .model_validate(
                    observation
                )
            ),
            current_interval=(
                WebsiteUsageIntervalResponse
                .model_validate(
                    current_interval
                )
            ),
            previous_interval_closed=(
                previous_interval_closed
            ),
            ignored_as_old=False,
        )

    @staticmethod
    def _close_interval(
        interval: WebsiteUsageInterval,
        *,
        ended_at: datetime,
    ) -> None:
        if ended_at < interval.last_observed_at:
            ended_at = (
                interval.last_observed_at
            )

        additional_seconds = max(
            0,
            int(
                (
                    ended_at
                    - interval.last_observed_at
                ).total_seconds()
            ),
        )

        interval.duration_seconds += (
            additional_seconds
        )

        interval.last_observed_at = (
            ended_at
        )

        interval.ended_at = (
            ended_at
        )

        interval.status = (
            WEBSITE_USAGE_STATUS_CLOSED
        )


__all__ = [
    "WebsiteTrackingService",
]