from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.devices.registration_service import (
    DeviceRegistrationService,
)
from app.modules.devices.schemas import (
    DeviceRegistrationRequest,
    DeviceRegistrationResponse,
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/device-registration",
    tags=["Device Registration"],
)


# =========================================================
# CONTROL DATABASE DEPENDENCY
# =========================================================

ControlDB = Annotated[
    AsyncSession,
    Depends(get_control_db),
]


# =========================================================
# REGISTRATION SERVICE
# =========================================================


def get_device_registration_service(
    db: ControlDB,
) -> DeviceRegistrationService:
    """
    Build the cross-plane registration orchestrator from the
    trusted control database session.

    The service itself resolves:

        activation code
        workspace
        tenant registry
        tenant database
        device
        device credential
        device route
    """

    return DeviceRegistrationService(
        db
    )


DeviceRegistrationServiceDependency = Annotated[
    DeviceRegistrationService,
    Depends(
        get_device_registration_service
    ),
]


# =========================================================
# PUBLIC AGENT REGISTRATION
# =========================================================


@router.post(
    "/register",
    response_model=DeviceRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register endpoint device",
)
async def register_device(
    payload: DeviceRegistrationRequest,
    service: DeviceRegistrationServiceDependency,
) -> DeviceRegistrationResponse:
    """
    First-time endpoint enrollment endpoint.

    Expected client payload:

        activation_code
        hostname
        os_name
        os_version
        architecture
        agent_version
        agent_identifier

    The endpoint deliberately accepts no:

        workspace_id
        tenant_id
        database_name
        database_url
        cluster_key
        device_uuid
        employee_id
        monitoring_profile_id

    Successful registration returns:

        Device information
        server-generated device_uuid
        one-time device_secret

    The plaintext device_secret is generated during enrollment,
    returned once, and is not stored plaintext by the backend.
    """

    return await service.register_device(
        payload
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "ControlDB",
    "DeviceRegistrationServiceDependency",
    "get_device_registration_service",
    "register_device",
    "router",
]