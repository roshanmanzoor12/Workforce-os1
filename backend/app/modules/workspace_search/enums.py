from __future__ import annotations

from enum import StrEnum


class SearchEntityType(
    StrEnum
):
    EMPLOYEE = "employee"
    GOAL = "goal"
    NOTE = "note"
    KNOWLEDGE = "knowledge"
    MEETING = "meeting"


SEARCH_ENTITY_TYPES = frozenset(
    item.value
    for item
    in SearchEntityType
)


__all__ = [
    "SearchEntityType",
    "SEARCH_ENTITY_TYPES",
]