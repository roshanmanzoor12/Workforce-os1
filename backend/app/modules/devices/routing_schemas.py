from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
)


# =========================================================
# DEVICE ROUTE STATUS TYPE
# =========================================================

DeviceRouteStatus = Literal[
    "active",
    "revoked",
]


# =========================================================
# BASE SCHEMA
# =========================================================


class DeviceRoutingSchemaBase(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


# =========================================================
# PUBLIC ROUTE METADATA
# =========================================================


class DeviceRoutePublic(
    DeviceRoutingSchemaBase
):
    """
    Safe control-plane routing metadata.

    This schema intentionally does not contain:

        database_name
        database_url
        cluster_key
        credentials
        secrets

    It may be used internally or by authenticated admin APIs later.
    """

    id: uuid.UUID

    workspace_id: uuid.UUID

    device_uuid: uuid.UUID

    tenant_device_id: uuid.UUID

    status: DeviceRouteStatus

    is_active: bool

    registered_at: datetime | None

    revoked_at: datetime | None

    created_at: datetime

    updated_at: datetime


# =========================================================
# ROUTE DETAIL RESPONSE
# =========================================================


class DeviceRouteResponse(
    DeviceRoutingSchemaBase
):
    route: DeviceRoutePublic


# =========================================================
# TRUSTED ROUTE RESOLUTION
# =========================================================


class ResolvedDeviceRouteSchema(
    DeviceRoutingSchemaBase
):
    """
    Internal trusted result after resolving device_uuid through
    workforce_control.

    This result still does not expose physical tenant DB routing
    details.

    TenantDatabaseRegistry remains the authoritative source for
    database_name and cluster_key.
    """

    route_id: uuid.UUID

    workspace_id: uuid.UUID

    device_uuid: uuid.UUID

    tenant_device_id: uuid.UUID


# =========================================================
# ROUTE CREATION RESULT
# =========================================================


class DeviceRouteCreateResult(
    DeviceRoutingSchemaBase
):
    route: DeviceRoutePublic


# =========================================================
# ROUTE REVOCATION RESPONSE
# =========================================================


class DeviceRouteRevokeResponse(
    DeviceRoutingSchemaBase
):
    message: str

    success: bool


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DeviceRouteStatus",
    "DeviceRoutePublic",
    "DeviceRouteResponse",
    "ResolvedDeviceRouteSchema",
    "DeviceRouteCreateResult",
    "DeviceRouteRevokeResponse",
]