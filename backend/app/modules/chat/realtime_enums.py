from enum import StrEnum


class ChatRealtimeEventType(StrEnum):
    MESSAGE_CREATED = "message.created"
    MESSAGE_UPDATED = "message.updated"
    MESSAGE_DELETED = "message.deleted"
    MESSAGE_DELIVERED = "message.delivered"
    MESSAGE_REACTION = "message_reaction"
    MESSAGE_READ = "message.read"
    MESSAGE_PIN = "message_pin"
    MESSAGE_UNPIN = "message_unpin"

    TYPING_STARTED = "typing.started"
    TYPING_STOPPED = "typing.stopped"

    PRESENCE_UPDATED = "presence.updated"

    MEMBER_JOINED = "member.joined"
    MEMBER_LEFT = "member.left"

    CONVERSATION_PREFERENCES_UPDATED = "conversation.preferences.updated"

    CALL_CREATED = "call.created"
    CALL_PARTICIPANT_JOINED = "call.participant.joined"
    CALL_PARTICIPANT_LEFT = "call.participant.left"
    CALL_PARTICIPANT_DECLINED = "call.participant.declined"
    CALL_ENDED = "call.ended"
    CALL_CANCELLED = "call.cancelled"
    CALL_MEDIA_STATE_UPDATED = "call.media_state.updated"
    CALL_SCREEN_SHARE_STARTED = "call.screen_share.started"
    CALL_SCREEN_SHARE_STOPPED = "call.screen_share.stopped"
    CALL_SIGNAL = "call.signal"


__all__ = [
    "ChatRealtimeEventType",
]