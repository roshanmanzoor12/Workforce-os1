from __future__ import annotations

from enum import Enum


class CallScope(str, Enum):
    CONVERSATION = "CONVERSATION"
    CHANNEL = "CHANNEL"


class CallKind(str, Enum):
    VOICE = "VOICE"
    VIDEO = "VIDEO"


class CallStatus(str, Enum):
    RINGING = "RINGING"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    CANCELLED = "CANCELLED"


class CallParticipantState(str, Enum):
    INVITED = "INVITED"
    JOINED = "JOINED"
    LEFT = "LEFT"
    DECLINED = "DECLINED"


class CallSignalType(str, Enum):
    OFFER = "OFFER"
    ANSWER = "ANSWER"
    ICE_CANDIDATE = "ICE_CANDIDATE"


class ScreenShareState(str, Enum):
    STOPPED = "STOPPED"
    ACTIVE = "ACTIVE"