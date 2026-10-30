from __future__ import annotations

import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# =========================================================
# BASE SCHEMA
# =========================================================


class DeviceAgentSchemaBase(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )


# =========================================================
# AUTHENTICATED DEVICE IDENTITY
# =========================================================


class DeviceAgentIdentityResponse(
    DeviceAgentSchemaBase
):
    """
    Safe identity returned to an authenticated endpoint agent.

    This response deliberately does not expose:

        workspace_id
        tenant database name
        database URL
        cluster key
        credential_id
        secret hash
        device secret
    """

    authenticated: bool = True

    device_uuid: uuid.UUID

    credential_version: int = Field(
        ge=1,
    )


# =========================================================
# BASIC AGENT ACKNOWLEDGEMENT
# =========================================================


class DeviceAgentAcknowledgement(
    DeviceAgentSchemaBase
):
    """
    Generic response that can later be reused by authenticated
    agent endpoints such as heartbeat or metadata refresh.
    """

    success: bool = True

    message: str


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DeviceAgentIdentityResponse",
    "DeviceAgentAcknowledgement",
]