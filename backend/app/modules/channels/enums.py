from enum import StrEnum


class WorkspaceChannelType(StrEnum):
    TEXT = "text"
    ANNOUNCEMENT = "announcement"
    VOICE = "voice"


class WorkspaceChannelRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class WorkspaceChannelMessageType(StrEnum):
    TEXT = "text"
    SYSTEM = "system"


__all__ = [
    "WorkspaceChannelMessageType",
    "WorkspaceChannelRole",
    "WorkspaceChannelType",
]