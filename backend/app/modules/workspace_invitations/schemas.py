from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.modules.workspace_invitations.enums import (
    WorkspaceInvitationStatus,
)
from app.modules.workspace_invitations.security import (
    normalize_invitation_email,
)
from app.modules.workspace_permissions.roles import (
    BUILT_IN_ROLE_KEYS,
    MEMBER_ROLE,
)


# =========================================================
# BASE
# =========================================================


class InvitationSchema(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
    )


# =========================================================
# CREATE REQUEST
# =========================================================


class WorkspaceInvitationCreateRequest(
    InvitationSchema
):
    email: EmailStr | None = None

    identifier: str | None = Field(default=None, min_length=3, max_length=320)

    employee_id: (
        uuid.UUID
        | None
    ) = None

    role_key: str = Field(
        default=MEMBER_ROLE,
        min_length=1,
        max_length=64,
    )

    department_id: (
        uuid.UUID
        | None
    ) = None

    team_id: (
        uuid.UUID
        | None
    ) = None

    manager_membership_id: (
        uuid.UUID
        | None
    ) = None

    expires_at: (
        datetime
        | None
    ) = None

    @field_validator(
        "email",
    )
    @classmethod
    def normalize_email(
        cls,
        value: EmailStr | None,
    ) -> str | None:
        if value is None:
            return None
        return (
            normalize_invitation_email(
                str(value)
            )
        )

    @field_validator(
        "role_key",
    )
    @classmethod
    def validate_role_key(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value
            .strip()
            .lower()
        )

        return normalized


# =========================================================
# PUBLIC INVITATION
# =========================================================


class WorkspaceInvitationPublic(
    InvitationSchema
):
    workspace_name: str | None = None

    id: uuid.UUID

    workspace_id: uuid.UUID

    employee_id: (
        uuid.UUID
        | None
    ) = None

    email: EmailStr

    invited_user_id: (
        uuid.UUID
        | None
    ) = None

    role_key: str

    department_id: (
        uuid.UUID
        | None
    ) = None

    team_id: (
        uuid.UUID
        | None
    ) = None

    manager_membership_id: (
        uuid.UUID
        | None
    ) = None

    invited_by_user_id: uuid.UUID

    status: WorkspaceInvitationStatus

    expires_at: datetime

    accepted_at: (
        datetime
        | None
    ) = None

    declined_at: (
        datetime
        | None
    ) = None

    revoked_at: (
        datetime
        | None
    ) = None

    created_at: datetime
    updated_at: datetime


# =========================================================
# LIST RESPONSE
# =========================================================


class IncomingWorkspaceInvitationListResponse(InvitationSchema):
    items: list[WorkspaceInvitationPublic] = Field(default_factory=list)
    total: int = Field(ge=0)


class WorkspaceInvitationListResponse(
    InvitationSchema
):
    workspace_id: uuid.UUID

    items: list[
        WorkspaceInvitationPublic
    ] = Field(
        default_factory=list,
    )

    total: int = Field(
        ge=0,
    )


# =========================================================
# CREATE / RESEND RESPONSE
# =========================================================


class WorkspaceInvitationCreateResponse(
    InvitationSchema
):
    invitation: (
        WorkspaceInvitationPublic
    )

    invitation_token: str = Field(
        min_length=20,
        max_length=512,
    )


class WorkspaceInvitationSecretResponse(
    WorkspaceInvitationCreateResponse
):
    """
    Canonical create/resend response.

    Kept separate for newer imports while preserving the
    older WorkspaceInvitationCreateResponse name.
    """

    pass


# =========================================================
# TOKEN PREVIEW
# =========================================================


class WorkspaceInvitationTokenPublic(
    InvitationSchema
):
    invitation_id: (
        uuid.UUID
        | None
    ) = None

    workspace_id: uuid.UUID

    workspace_name: (
        str
        | None
    ) = None

    email: EmailStr

    role_key: str

    status: WorkspaceInvitationStatus

    expires_at: datetime


# =========================================================
# ACTION RESPONSE
# =========================================================


class WorkspaceInvitationActionResponse(
    InvitationSchema
):
    message: str

    success: bool = True

    workspace_id: (
        uuid.UUID
        | None
    ) = None

    membership_id: (
        uuid.UUID
        | None
    ) = None


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "InvitationSchema",
    "WorkspaceInvitationCreateRequest",
    "WorkspaceInvitationPublic",
    "WorkspaceInvitationListResponse",
    "WorkspaceInvitationCreateResponse",
    "WorkspaceInvitationSecretResponse",
    "WorkspaceInvitationTokenPublic",
    "WorkspaceInvitationActionResponse",
]
