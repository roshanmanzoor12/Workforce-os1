from __future__ import annotations

from enum import StrEnum


class AIProductivityAction(StrEnum):
    SUMMARIZE_NOTES = (
        "summarize_notes"
    )

    REVIEW_GOALS = (
        "review_goals"
    )

    KNOWLEDGE_ASSIST = (
        "knowledge_assist"
    )

    DAILY_FOCUS = (
        "daily_focus"
    )


class AIProductivitySource(StrEnum):
    GOALS = "goals"
    NOTES = "notes"
    KNOWLEDGE = "knowledge"


class AIProviderStatus(StrEnum):
    READY = "ready"
    DISABLED = "disabled"


__all__ = [
    "AIProductivityAction",
    "AIProductivitySource",
    "AIProviderStatus",
]