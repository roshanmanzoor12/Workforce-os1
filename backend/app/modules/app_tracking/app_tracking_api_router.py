from __future__ import annotations

from fastapi import (
    APIRouter,
    status,
)

from app.modules.app_tracking.agent_history_router import (
    get_device_app_history,
)
from app.modules.app_tracking.agent_router import (
    report_device_app_observation,
)
from app.modules.app_tracking.history_schemas import (
    AppUsageHistoryResponse,
)
from app.modules.app_tracking.schemas import (
    AppObservationResponse,
)
from app.modules.app_tracking.status_router import (
    get_device_current_app_status,
)
from app.modules.app_tracking.status_schemas import (
    CurrentAppStatusResponse,
)


__all__ = [
    "router",
]


router = APIRouter()


# =========================================================
# DEVICE AGENT — FOREGROUND APP OBSERVATION
# =========================================================

router.add_api_route(
    path="/device-agent/app-observation",
    endpoint=report_device_app_observation,
    methods=["POST"],
    response_model=AppObservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Report foreground application observation",
    name="report_device_app_observation",
)


# =========================================================
# DEVICE AGENT — CURRENT APP STATUS
# =========================================================

router.add_api_route(
    path="/device-agent/app-status",
    endpoint=get_device_current_app_status,
    methods=["GET"],
    response_model=CurrentAppStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated device foreground application status",
    name="get_device_current_app_status",
)


# =========================================================
# DEVICE AGENT — APP HISTORY
# =========================================================

router.add_api_route(
    path="/device-agent/app-history",
    endpoint=get_device_app_history,
    methods=["GET"],
    response_model=AppUsageHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated device application history",
    name="get_device_app_history",
)