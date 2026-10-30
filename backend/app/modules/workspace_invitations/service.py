from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.auth.models import User
from app.modules.workspace_invitations.repository import (
    WorkspaceInvitationRepository,
)
from app.modules.workspace_invitations.schemas import (
    WorkspaceInvitationActionResponse,
    WorkspaceInvitationCreateRequest,
    WorkspaceInvitationListResponse,
    WorkspaceInvitationPublic,
    WorkspaceInvitationSecretResponse,
    WorkspaceInvitationTokenPublic,
)
from app.modules.workspace_invitations.security import (
    generate_invitation_token,
    hash_invitation_token,
    normalize_invitation_email,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.effective import resolve_membership_access
from app.modules.workspace_rbac.repository import WorkspaceRBACRepository
from app.modules.workspace_permissions.roles import BUILT_IN_ROLE_KEYS
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
    MEMBERSHIP_STATUS_INVITED,
    MEMBERSHIP_STATUS_REMOVED,
    MEMBERSHIP_STATUS_SUSPENDED,
    WorkspaceInvitation,
)


DEFAULT_INVITATION_TTL = timedelta(
    days=3
)


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


class WorkspaceInvitationService:
    """
    Workspace invitation application service.

    Security rules:

    - invitation token is stored only as a hash
    - authenticated account email must match invitation email
    - active duplicate memberships are rejected
    - suspended / removed membership states cannot silently
      reactivate through an invitation
    - browser never controls tenant database routing
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            WorkspaceInvitationRepository(
                session
            )
        )

    # =====================================================
    # ERRORS
    # =====================================================

    @staticmethod
    def _not_found(
        detail: str,
    ) -> HTTPException:
        return HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=detail,
        )

    @staticmethod
    def _forbidden(
        detail: str,
    ) -> HTTPException:
        return HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=detail,
        )

    @staticmethod
    def _conflict(
        detail: str,
    ) -> HTTPException:
        return HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=detail,
        )

    @staticmethod
    def _invalid(
        detail: str,
    ) -> HTTPException:
        return HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=detail,
        )

    # =====================================================
    # WORKSPACE AUTHORIZATION
    # =====================================================

    async def _require_invite_access(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ):
        workspace = await (
            self.repository.get_workspace(
                workspace_id
            )
        )

        if workspace is None:
            raise self._not_found(
                "Workspace was not found."
            )

        membership = await (
            self.repository
            .get_active_membership(
                workspace_id=workspace_id,
                user_id=user.id,
            )
        )

        if membership is None:
            raise self._not_found(
                "Workspace was not found."
            )

        access = await resolve_membership_access(
            self.session,
            workspace_id=workspace_id,
            membership=membership,
        )
        allowed = WorkspacePermission.MEMBERS_INVITE.value in access.permissions

        if not allowed:
            raise self._forbidden(
                "Workspace permission required: "
                "members.invite"
            )

        return (
            workspace,
            membership,
        )

    # =====================================================
    # CREATE
    # =====================================================

    async def create_invitation(
        self,
        request: WorkspaceInvitationCreateRequest,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceInvitationSecretResponse:
        await self._require_invite_access(
            workspace_id=workspace_id,
            user=user,
        )

        invited_user = None
        if request.identifier:
            invited_user = await self.repository.resolve_invitee(request.identifier)
            if invited_user is None:
                raise self._not_found("No verified user found for this Calling Number, username, or account ID.")
            if request.email and str(request.email).lower() != invited_user.email.lower():
                raise self._invalid("The supplied email does not match that account.")
            email = normalize_invitation_email(invited_user.email)
        elif request.email:
            email = normalize_invitation_email(str(request.email))
        else:
            raise self._invalid("Email, Calling Number, username, or account ID is required.")

        # Never allow invitations to grant ownership. Custom roles must
        # exist, be active, and belong to this workspace.
        if request.role_key == "owner":
            raise self._invalid("Ownership cannot be granted by invitation.")
        if request.role_key not in BUILT_IN_ROLE_KEYS:
            custom_role = await WorkspaceRBACRepository(
                self.session
            ).get_custom_role_by_key(
                workspace_id=workspace_id,
                role_key=request.role_key,
            )
            if custom_role is None or not custom_role.is_active:
                raise self._invalid("Workspace role does not exist or is inactive.")

        existing_pending = await (
            self.repository
            .get_pending_for_email(
                workspace_id=workspace_id,
                email=email,
            )
        )

        if existing_pending is not None:
            raise self._conflict(
                "A pending invitation already "
                "exists for this email."
            )

        if invited_user is None:
            invited_user = await self.repository.get_user_by_email(email)

        if invited_user is not None:
            membership = await (
                self.repository
                .get_membership(
                    workspace_id=workspace_id,
                    user_id=invited_user.id,
                )
            )

            if (
                membership is not None
                and membership.status
                == MEMBERSHIP_STATUS_ACTIVE
            ):
                raise self._conflict(
                    "This user is already an "
                    "active workspace member."
                )

        now = utc_now()

        expires_at = (
            request.expires_at
            or (
                now
                + DEFAULT_INVITATION_TTL
            )
        )

        if expires_at > now + DEFAULT_INVITATION_TTL:
            raise self._invalid("Invitation cannot expire more than 3 days from now.")

        if expires_at <= now:
            raise self._invalid(
                "Invitation expiry must "
                "be in the future."
            )

        token = (
            generate_invitation_token()
        )

        try:
            invitation = await (
                self.repository.create(
                    workspace_id=workspace_id,
                    employee_id=(
                        request.employee_id
                    ),
                    email=email,
                    invited_user_id=(
                        invited_user.id
                        if invited_user
                        is not None
                        else None
                    ),
                    role_key=(
                        request.role_key
                    ),
                    department_id=(
                        request.department_id
                    ),
                    team_id=(
                        request.team_id
                    ),
                    manager_membership_id=(
                        request
                        .manager_membership_id
                    ),
                    invited_by_user_id=(
                        user.id
                    ),
                    token_hash=(
                        hash_invitation_token(
                            token
                        )
                    ),
                    expires_at=(
                        expires_at
                    ),
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return (
            WorkspaceInvitationSecretResponse(
                invitation=(
                    self._public(
                        invitation
                    )
                ),
                invitation_token=token,
            )
        )

    # =====================================================
    # LIST
    # =====================================================

    async def list_invitations(
        self,
        *,
        workspace_id: uuid.UUID,
        user: User,
    ) -> WorkspaceInvitationListResponse:
        await self._require_invite_access(
            workspace_id=workspace_id,
            user=user,
        )

        invitations = await (
            self.repository
            .list_for_workspace(
                workspace_id
            )
        )

        return WorkspaceInvitationListResponse(
            workspace_id=workspace_id,
            items=[
                self._public(
                    invitation
                )
                for invitation
                in invitations
            ],
            total=len(
                invitations
            ),
        )

    # =====================================================
    # TOKEN PREVIEW
    # =====================================================

    async def get_token_invitation(
        self,
        *,
        token: str,
        user: User,
    ) -> WorkspaceInvitationTokenPublic:
        invitation = await (
            self._require_token(
                token
            )
        )

        self._require_email_match(
            invitation=invitation,
            user=user,
        )

        workspace = await (
            self.repository.get_workspace(
                invitation.workspace_id
            )
        )

        if workspace is None:
            raise self._not_found(
                "Workspace was not found."
            )

        return (
            WorkspaceInvitationTokenPublic(
                invitation_id=(
                    invitation.id
                ),
                workspace_id=(
                    invitation.workspace_id
                ),
                workspace_name=(
                    workspace.name
                ),
                email=(
                    invitation.email
                ),
                role_key=(
                    invitation.role_key
                ),
                status=(
                    invitation.status
                ),
                expires_at=(
                    invitation.expires_at
                ),
            )
        )

    # =====================================================
    # ACCEPT
    # =====================================================

    async def list_incoming(self, *, user: User):
        from app.modules.workspace_invitations.schemas import IncomingWorkspaceInvitationListResponse
        items = await self.repository.list_incoming(user)
        serialized = []
        workspace_names = {}
        for row in items:
            if row.workspace_id not in workspace_names:
                workspace = await self.repository.get_workspace(row.workspace_id)
                workspace_names[row.workspace_id] = workspace.name if workspace is not None else None
            serialized.append(self._public(row).model_copy(update={
                "workspace_name": workspace_names[row.workspace_id]
            }))
        return IncomingWorkspaceInvitationListResponse(items=serialized, total=len(items))

    async def accept(
        self,
        *,
        token: str,
        user: User,
    ) -> WorkspaceInvitationActionResponse:
        invitation = await self._require_token(token)
        return await self._accept_invitation(invitation, user)

    async def accept_by_id(self, *, invitation_id: uuid.UUID, user: User) -> WorkspaceInvitationActionResponse:
        invitation = await self.repository.get_incoming_by_id(invitation_id, user)
        if invitation is None:
            raise self._not_found("Invitation not found for your account.")
        return await self._accept_invitation(invitation, user)

    async def _accept_invitation(self, invitation: WorkspaceInvitation, user: User) -> WorkspaceInvitationActionResponse:
        self._require_email_match(
            invitation=invitation,
            user=user,
        )

        membership = await (
            self.repository.get_membership(
                workspace_id=(
                    invitation.workspace_id
                ),
                user_id=user.id,
            )
        )

        # Idempotent already-accepted response.
        if (
            invitation.status
            == "accepted"
        ):
            if membership is None:
                raise self._conflict(
                    "Accepted invitation has "
                    "no workspace membership."
                )

            return (
                WorkspaceInvitationActionResponse(
                    message=(
                        "Invitation already "
                        "accepted."
                    ),
                    success=True,
                    workspace_id=(
                        invitation.workspace_id
                    ),
                    membership_id=(
                        membership.id
                    ),
                )
            )

        if (
            invitation.status
            != "pending"
        ):
            raise self._conflict(
                "Invitation is no longer "
                "available."
            )

        now = utc_now()

        if invitation.expires_at <= now:
            try:
                await (
                    self.repository
                    .mark_expired(
                        invitation
                    )
                )

                await self.session.commit()

            except Exception:
                await self.session.rollback()
                raise

            raise self._conflict(
                "Invitation has expired."
            )

        if (
            invitation.invited_user_id
            is not None
            and invitation.invited_user_id
            != user.id
        ):
            raise self._forbidden(
                "Invitation belongs to "
                "another account."
            )

        if membership is not None:
            if (
                membership.status
                == MEMBERSHIP_STATUS_SUSPENDED
            ):
                raise self._conflict(
                    "Suspended membership "
                    "cannot be reactivated "
                    "through an invitation."
                )

            if (
                membership.status
                == MEMBERSHIP_STATUS_REMOVED
            ):
                raise self._conflict(
                    "Removed membership must "
                    "be restored by workspace "
                    "administration."
                )

        try:
            if membership is None:
                membership = await (
                    self.repository
                    .create_membership(
                        workspace_id=(
                            invitation
                            .workspace_id
                        ),
                        user_id=user.id,
                        role_key=(
                            invitation
                            .role_key
                        ),
                        status=(
                            MEMBERSHIP_STATUS_ACTIVE
                        ),
                        invited_by_user_id=(
                            invitation
                            .invited_by_user_id
                        ),
                        invited_at=(
                            invitation.created_at
                        ),
                        joined_at=now,
                    )
                )

            elif (
                membership.status
                == MEMBERSHIP_STATUS_INVITED
            ):
                membership.role_key = (
                    invitation.role_key
                )

                membership.status = (
                    MEMBERSHIP_STATUS_ACTIVE
                )

                membership.joined_at = now
                membership.suspended_at = None
                membership.removed_at = None

                await self.session.flush()

            await (
                self.repository
                .mark_accepted(
                    invitation,
                    user_id=user.id,
                    accepted_at=now,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return (
            WorkspaceInvitationActionResponse(
                message=(
                    "Workspace invitation "
                    "accepted."
                ),
                success=True,
                workspace_id=(
                    invitation.workspace_id
                ),
                membership_id=(
                    membership.id
                ),
            )
        )

    # =====================================================
    # DECLINE
    # =====================================================

    async def decline(
        self,
        *,
        token: str,
        user: User,
    ) -> WorkspaceInvitationActionResponse:
        invitation = await self._require_token(token)
        return await self._decline_invitation(invitation, user)

    async def decline_by_id(self, *, invitation_id: uuid.UUID, user: User) -> WorkspaceInvitationActionResponse:
        invitation = await self.repository.get_incoming_by_id(invitation_id, user)
        if invitation is None:
            raise self._not_found("Invitation not found for your account.")
        return await self._decline_invitation(invitation, user)

    async def _decline_invitation(self, invitation: WorkspaceInvitation, user: User) -> WorkspaceInvitationActionResponse:
        self._require_email_match(
            invitation=invitation,
            user=user,
        )

        if (
            invitation.status
            == "declined"
        ):
            return (
                WorkspaceInvitationActionResponse(
                    message=(
                        "Invitation already "
                        "declined."
                    ),
                    success=True,
                    workspace_id=(
                        invitation.workspace_id
                    ),
                )
            )

        if (
            invitation.status
            != "pending"
        ):
            raise self._conflict(
                "Invitation cannot be "
                "declined."
            )

        if (
            invitation.expires_at
            <= utc_now()
        ):
            try:
                await (
                    self.repository
                    .mark_expired(
                        invitation
                    )
                )

                await self.session.commit()

            except Exception:
                await self.session.rollback()
                raise

            raise self._conflict(
                "Invitation has expired."
            )

        try:
            await (
                self.repository
                .mark_declined(
                    invitation,
                    declined_at=utc_now(),
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return (
            WorkspaceInvitationActionResponse(
                message=(
                    "Workspace invitation "
                    "declined."
                ),
                success=True,
                workspace_id=(
                    invitation.workspace_id
                ),
            )
        )

    # =====================================================
    # RESEND
    # =====================================================

    async def resend(
        self,
        *,
        workspace_id: uuid.UUID,
        invitation_id: uuid.UUID,
        user: User,
    ) -> WorkspaceInvitationSecretResponse:
        await self._require_invite_access(
            workspace_id=workspace_id,
            user=user,
        )

        invitation = await (
            self.repository.get_by_id(
                workspace_id=workspace_id,
                invitation_id=(
                    invitation_id
                ),
            )
        )

        if invitation is None:
            raise self._not_found(
                "Workspace invitation "
                "was not found."
            )

        if invitation.status not in {
            "pending",
            "expired",
        }:
            raise self._conflict(
                "Only pending or expired "
                "invitations can be resent."
            )

        token = (
            generate_invitation_token()
        )

        try:
            invitation = await (
                self.repository.rotate_token(
                    invitation,
                    token_hash=(
                        hash_invitation_token(
                            token
                        )
                    ),
                    expires_at=(
                        utc_now()
                        + DEFAULT_INVITATION_TTL
                    ),
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return (
            WorkspaceInvitationSecretResponse(
                invitation=(
                    self._public(
                        invitation
                    )
                ),
                invitation_token=token,
            )
        )

    # =====================================================
    # REVOKE
    # =====================================================

    async def revoke(
        self,
        *,
        workspace_id: uuid.UUID,
        invitation_id: uuid.UUID,
        user: User,
    ) -> WorkspaceInvitationActionResponse:
        await self._require_invite_access(
            workspace_id=workspace_id,
            user=user,
        )

        invitation = await (
            self.repository.get_by_id(
                workspace_id=workspace_id,
                invitation_id=(
                    invitation_id
                ),
            )
        )

        if invitation is None:
            raise self._not_found(
                "Workspace invitation "
                "was not found."
            )

        if (
            invitation.status
            == "revoked"
        ):
            return (
                WorkspaceInvitationActionResponse(
                    message=(
                        "Invitation already "
                        "revoked."
                    ),
                    success=True,
                    workspace_id=workspace_id,
                )
            )

        if (
            invitation.status
            == "accepted"
        ):
            raise self._conflict(
                "Accepted invitations cannot "
                "be revoked."
            )

        try:
            await (
                self.repository
                .mark_revoked(
                    invitation,
                    revoked_at=utc_now(),
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return (
            WorkspaceInvitationActionResponse(
                message=(
                    "Workspace invitation "
                    "revoked."
                ),
                success=True,
                workspace_id=workspace_id,
            )
        )

    # =====================================================
    # INTERNAL TOKEN RESOLUTION
    # =====================================================

    async def _require_token(
        self,
        token: str,
    ) -> WorkspaceInvitation:
        try:
            token_hash = (
                hash_invitation_token(
                    token
                )
            )

        except ValueError as exc:
            raise self._not_found(
                "Workspace invitation "
                "was not found."
            ) from exc

        invitation = await (
            self.repository
            .get_by_token_hash(
                token_hash
            )
        )

        if invitation is None:
            raise self._not_found(
                "Workspace invitation "
                "was not found."
            )

        return invitation

    # =====================================================
    # EMAIL BINDING
    # =====================================================

    def _require_email_match(
        self,
        *,
        invitation: WorkspaceInvitation,
        user: User,
    ) -> None:
        authenticated_email = (
            normalize_invitation_email(
                str(
                    user.email
                )
            )
        )

        invitation_email = (
            normalize_invitation_email(
                invitation.email
            )
        )

        if invitation.invited_user_id is not None and invitation.invited_user_id != user.id:
            raise self._forbidden("Invitation belongs to another account.")

        if (
            authenticated_email
            != invitation_email
        ):
            raise self._forbidden(
                "Invitation email does not "
                "match the authenticated "
                "account."
            )

    # =====================================================
    # PUBLIC SERIALIZATION
    # =====================================================

    @staticmethod
    def _public(
        invitation: WorkspaceInvitation,
    ) -> WorkspaceInvitationPublic:
        return (
            WorkspaceInvitationPublic
            .model_validate(
                invitation
            )
        )


__all__ = [
    "WorkspaceInvitationService",
    "DEFAULT_INVITATION_TTL",
]
