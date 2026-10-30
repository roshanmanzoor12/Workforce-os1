from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


# =========================================================
# PROVISIONING RESPONSE
# =========================================================


class WorkspaceProvisioningResponse(
    BaseModel
):
    """
    Public API response for workspace tenant provisioning.

    This model deliberately exposes only safe provisioning state.

    It never exposes:

    - database credentials
    - database URLs
    - database host
    - database port
    - PostgreSQL username
    - PostgreSQL password

    database_name is intentionally not exposed through this
    public API response. The physical tenant database identity
    remains a server-side routing concern.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    workspace_id: uuid.UUID
    cluster_key: str
    schema_version: str

    database_created: bool
    database_already_existed: bool
    metadata_created: bool

    workspace_ready: bool
    tenant_ready: bool


# =========================================================
# PROVISIONING STATUS RESPONSE
# =========================================================


class WorkspaceProvisioningStatusResponse(
    BaseModel
):
    """
    Safe public provisioning state for one workspace.

    This schema may later be used by:

        GET /workspaces/{workspace_id}/provisioning-status

    It is intentionally independent from the internal physical
    database identity.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    workspace_id: uuid.UUID

    workspace_status: str
    tenant_status: str

    schema_version: str | None = None

    provision_attempts: int

    workspace_ready: bool
    tenant_ready: bool

    failed: bool = False

    error_code: str | None = None


# =========================================================
# RETRY RESPONSE
# =========================================================


class WorkspaceProvisioningRetryResponse(
    WorkspaceProvisioningResponse
):
    """
    Response returned after retrying an existing tenant
    provisioning operation.
    """

    retried: bool = True


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "WorkspaceProvisioningResponse",
    "WorkspaceProvisioningStatusResponse",
    "WorkspaceProvisioningRetryResponse",
]