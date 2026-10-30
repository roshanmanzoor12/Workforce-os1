from __future__ import annotations

from fastapi import (
    APIRouter,
    status,
)

from app.modules.website_tracking.agent_history_router import (
    get_device_website_history,
)
from app.modules.website_tracking.agent_router import (
    report_device_website_observation,
)
from app.modules.website_tracking.history_schemas import (
    WebsiteUsageHistoryResponse,
)
from app.modules.website_tracking.schemas import (
    WebsiteObservationProcessingResult,
)
from app.modules.website_tracking.status_router import (
    get_device_current_website_status,
)
from app.modules.website_tracking.status_schemas import (
    CurrentWebsiteStatusResponse,
)


__all__ = [
    "router",
]


router = APIRouter()


router.add_api_route(
    path="/device-agent/website-observation",
    endpoint=report_device_website_observation,
    methods=[
        "POST",
    ],
    response_model=(
        WebsiteObservationProcessingResult
    ),
    status_code=status.HTTP_200_OK,
    tags=[
        "Device Agent Website Tracking",
    ],
    summary=(
        "Report foreground website observation"
    ),
    name=(
        "report_device_website_observation"
    ),
)


router.add_api_route(
    path="/device-agent/website-status",
    endpoint=get_device_current_website_status,
    methods=[
        "GET",
    ],
    response_model=(
        CurrentWebsiteStatusResponse
    ),
    status_code=status.HTTP_200_OK,
    tags=[
        "Device Agent Website Tracking",
    ],
    summary=(
        "Get authenticated device current website status"
    ),
    name=(
        "get_device_current_website_status"
    ),
)


router.add_api_route(
    path="/device-agent/website-history",
    endpoint=get_device_website_history,
    methods=[
        "GET",
    ],
    response_model=(
        WebsiteUsageHistoryResponse
    ),
    status_code=status.HTTP_200_OK,
    tags=[
        "Device Agent Website Tracking",
    ],
    summary=(
        "Get authenticated device website history"
    ),
    name=(
        "get_device_website_history"
    ),
)