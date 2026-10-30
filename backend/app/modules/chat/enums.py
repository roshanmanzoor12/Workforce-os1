from enum import StrEnum


class ConversationType(StrEnum):
    DIRECT = "direct"
    GROUP = "group"


class ConversationMemberRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class MessageType(StrEnum):
    TEXT = "text"
    SYSTEM = "system"


class PresenceStatus(StrEnum):
    ONLINE = "online"
    IDLE = "idle"
    DND = "dnd"
    OFFLINE = "offline"


__all__ = [
    "ConversationMemberRole",
    "ConversationType",
    "MessageType",
    "PresenceStatus",
]