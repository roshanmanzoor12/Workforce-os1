from __future__ import annotations

from enum import StrEnum


class WorkspaceInvitationStatus(
    StrEnum
):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    REVOKED = "revoked"


__all__ = [
    "WorkspaceInvitationStatus",
]