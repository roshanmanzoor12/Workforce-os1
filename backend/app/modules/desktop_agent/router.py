from __future__ import annotations

import uuid
from typing import (
    Annotated,
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)

from app.core.exceptions import ValidationError
from app.modules.desktop_agent.access import (
    resolve_desktop_agent_access,
)
from app.modules.desktop_agent.schemas import (
    DesktopAgentCapabilitiesResponse,
    DesktopAgentDeviceListResponse,
    DesktopAgentDeviceResponse,
    DesktopAgentHeartbeatRequest,
    DesktopAgentHeartbeatResponse,
    DesktopAgentRegisterRequest,
)
from app.modules.desktop_agent.service import (
    DesktopAgentNotFoundError,
    DesktopAgentPermissionError,
    DesktopAgentService,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)



from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from app.modules.devices.models import Device
from app.modules.desktop_agent.models import DesktopAgentDevice

router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/desktop-agent"
    ),
    tags=[
        "desktop-agent",
    ],
)


TenantContext = Annotated[
    Any,
    Depends(
        get_authorized_tenant_context
    ),
]


def _client_ip(
    request: Request,
) -> str | None:
    forwarded = request.headers.get(
        "x-forwarded-for"
    )

    if forwarded:
        return (
            forwarded
            .split(",")[0]
            .strip()
        )[:64]

    if request.client is None:
        return None

    return (
        request.client.host
    )[:64]


async def _access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
):
    try:
        return await (
            resolve_desktop_agent_access(
                workspace_id=workspace_id,
                context=context,
            )
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(
                exc
            ),
        ) from exc


def _service(
    context: Any,
) -> DesktopAgentService:
    return DesktopAgentService(
        context.tenant_session
    )


def _translate_error(
    exc: Exception,
) -> HTTPException:
    if isinstance(
        exc,
        DesktopAgentNotFoundError,
    ):
        return HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(
                exc
            ),
        )

    if isinstance(
        exc,
        DesktopAgentPermissionError,
    ):
        return HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(
                exc
            ),
        )

    if isinstance(
        exc,
        ValidationError,
    ):
        return HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(
                exc
            ),
        )

    raise exc


@router.post(
    "/register",
    response_model=(
        DesktopAgentDeviceResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
)
async def register_desktop_agent(
    workspace_id: uuid.UUID,
    payload: DesktopAgentRegisterRequest,
    request: Request,
    context: TenantContext,
) -> DesktopAgentDeviceResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .register(
                access=access,
                payload=payload,
                ip_address=(
                    _client_ip(
                        request
                    )
                ),
            )
        )

    except (
        ValidationError,
        DesktopAgentPermissionError,
        DesktopAgentNotFoundError,
    ) as exc:
        raise _translate_error(
            exc
        ) from exc


@router.post(
    "/devices/{device_id}/heartbeat",
    response_model=(
        DesktopAgentHeartbeatResponse
    ),
)
async def desktop_agent_heartbeat(
    workspace_id: uuid.UUID,
    device_id: uuid.UUID,
    payload: DesktopAgentHeartbeatRequest,
    request: Request,
    context: TenantContext,
) -> DesktopAgentHeartbeatResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .heartbeat(
                access=access,
                device_id=device_id,
                payload=payload,
                ip_address=(
                    _client_ip(
                        request
                    )
                ),
            )
        )

    except (
        ValidationError,
        DesktopAgentPermissionError,
        DesktopAgentNotFoundError,
    ) as exc:
        raise _translate_error(
            exc
        ) from exc


@router.get(
    "/devices",
    response_model=(
        DesktopAgentDeviceListResponse
    ),
)
async def list_desktop_agent_devices(
    workspace_id: uuid.UUID,
    context: TenantContext,

    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),

    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> DesktopAgentDeviceListResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .list(
                access=access,
                status=status_filter,
                limit=limit,
                offset=offset,
            )
        )

    except (
        ValidationError,
        DesktopAgentPermissionError,
    ) as exc:
        raise _translate_error(
            exc
        ) from exc


@router.get(
    "/devices/{device_id}",
    response_model=(
        DesktopAgentDeviceResponse
    ),
)
async def get_desktop_agent_device(
    workspace_id: uuid.UUID,
    device_id: uuid.UUID,
    context: TenantContext,
) -> DesktopAgentDeviceResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .get(
                access=access,
                device_id=device_id,
            )
        )

    except (
        DesktopAgentNotFoundError,
        DesktopAgentPermissionError,
    ) as exc:
        raise _translate_error(
            exc
        ) from exc


@router.post(
    "/devices/{device_id}/disable",
    response_model=(
        DesktopAgentDeviceResponse
    ),
)
async def disable_desktop_agent_device(
    workspace_id: uuid.UUID,
    device_id: uuid.UUID,
    context: TenantContext,
) -> DesktopAgentDeviceResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .disable(
                access=access,
                device_id=device_id,
            )
        )

    except (
        DesktopAgentNotFoundError,
        DesktopAgentPermissionError,
    ) as exc:
        raise _translate_error(
            exc
        ) from exc


@router.get(
    "/capabilities",
    response_model=(
        DesktopAgentCapabilitiesResponse
    ),
)
async def desktop_agent_capabilities(
    workspace_id: uuid.UUID,
    context: TenantContext,
) -> DesktopAgentCapabilitiesResponse:
    await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return (
        DesktopAgentService
        .capabilities()
    )



# WFOS_DEVICE_IDENTITY_AUDIT_V1
@router.get("/identity-audit")
async def desktop_agent_identity_audit(
    workspace_id: uuid.UUID,
    context: TenantContext,
):
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    if not access.can_manage:
        raise HTTPException(
            status_code=403,
            detail="Device management permission required.",
        )

    session = context.tenant_session

    general_result = await session.execute(
        select(Device).order_by(Device.hostname)
    )

    desktop_result = await session.execute(
        select(DesktopAgentDevice).order_by(
            DesktopAgentDevice.device_name
        )
    )

    general_devices = list(general_result.scalars().all())
    desktop_devices = list(desktop_result.scalars().all())

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=120)

    def fresh(value):
        if value is None:
            return False

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return cutoff <= value <= now

    general_rows = [
        {
            "general_device_id": str(item.id),
            "device_uuid": str(item.device_uuid),
            "employee_id": (
                str(item.employee_id)
                if item.employee_id is not None
                else None
            ),
            "hostname": item.hostname,
            "status": item.status,
            "heartbeat_fresh": (
                item.is_active
                and item.status not in ("disabled", "revoked")
                and fresh(item.last_seen_at)
            ),
        }
        for item in general_devices
    ]

    desktop_rows = [
        {
            "desktop_agent_id": str(item.id),
            "employee_id": str(item.employee_id),
            "device_name": item.device_name,
            "status": item.status,
            "heartbeat_fresh": (
                not item.is_disabled
                and item.status == "online"
                and fresh(item.last_seen_at)
            ),
            "live_screen_capability": bool(
                (item.capabilities or {}).get("live_screen", False)
            ),
        }
        for item in desktop_devices
    ]

    employee_ids = sorted({
        item["employee_id"]
        for item in general_rows + desktop_rows
        if item["employee_id"] is not None
    })

    employees = []

    for employee_id in employee_ids:
        assigned = [
            item for item in general_rows
            if item["employee_id"] == employee_id
        ]

        enrolled = [
            item for item in desktop_rows
            if item["employee_id"] == employee_id
        ]

        employees.append({
            "employee_id": employee_id,
            "assigned_devices": assigned,
            "desktop_agents": enrolled,
            "assigned_count": len(assigned),
            "enrolled_count": len(enrolled),
            "has_desktop_enrollment": bool(enrolled),
            "has_fresh_desktop_heartbeat": any(
                item["heartbeat_fresh"] for item in enrolled
            ),
            "identity_link_verified": False,
        })

    return {
        "workspace_id": str(workspace_id),
        "generated_at": now.isoformat(),
        "summary": {
            "general_device_count": len(general_rows),
            "desktop_agent_count": len(desktop_rows),
            "fresh_general_devices": sum(
                item["heartbeat_fresh"] for item in general_rows
            ),
            "fresh_desktop_agents": sum(
                item["heartbeat_fresh"] for item in desktop_rows
            ),
        },
        "employees": employees,
        "unassigned_general_devices": [
            item for item in general_rows
            if item["employee_id"] is None
        ],
        "note": (
            "Employee grouping is not proof that two device "
            "records represent the same installation. "
            "Authenticated identity binding is still required."
        ),
    }


__all__ = [
    "router",
]