from __future__ import annotations

from app.modules.work_sessions.integration import (
    process_activity_event_into_work_session,
)
from app.modules.work_sessions.models import (
    WORK_SESSION_STATE_ACTIVE,
    WORK_SESSION_STATE_IDLE,
    WORK_SESSION_STATUS_CLOSED,
    WORK_SESSION_STATUS_OPEN,
    WorkSession,
)
from app.modules.work_sessions.repository import (
    WorkSessionRepository,
)
from app.modules.work_sessions.schemas import (
    WorkSessionCloseRequest,
    WorkSessionListResponse,
    WorkSessionProcessingResult,
    WorkSessionResponse,
    WorkSessionSummaryResponse,
)
from app.modules.work_sessions.service import (
    DEFAULT_MAX_EVENT_GAP_SECONDS,
    WorkSessionService,
)


__all__ = [
    "DEFAULT_MAX_EVENT_GAP_SECONDS",
    "WORK_SESSION_STATE_ACTIVE",
    "WORK_SESSION_STATE_IDLE",
    "WORK_SESSION_STATUS_CLOSED",
    "WORK_SESSION_STATUS_OPEN",
    "WorkSession",
    "WorkSessionCloseRequest",
    "WorkSessionListResponse",
    "WorkSessionProcessingResult",
    "WorkSessionRepository",
    "WorkSessionResponse",
    "WorkSessionService",
    "WorkSessionSummaryResponse",
    "process_activity_event_into_work_session",
]