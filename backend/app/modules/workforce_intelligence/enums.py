from __future__ import annotations

from enum import StrEnum


class IntelligenceScope(
    StrEnum
):
    SELF = "self"
    TEAM = "team"
    WORKSPACE = "workspace"


class IntelligenceSignalSeverity(
    StrEnum
):
    INFO = "info"
    WARNING = "warning"


class IntelligenceSignalCode(
    StrEnum
):
    NO_ATTENDANCE = "no_attendance"
    ABSENCE_RECORDED = "absence_recorded"
    OPEN_GOALS = "open_goals"
    LOW_GOAL_PROGRESS = "low_goal_progress"


__all__ = [
    "IntelligenceScope",
    "IntelligenceSignalSeverity",
    "IntelligenceSignalCode",
]