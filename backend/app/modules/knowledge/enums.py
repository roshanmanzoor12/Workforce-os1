from __future__ import annotations

from enum import StrEnum


class KnowledgeStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class KnowledgeVisibility(StrEnum):
    PRIVATE = "private"
    WORKSPACE = "workspace"


class KnowledgeCategory(StrEnum):
    GENERAL = "general"
    PROCESS = "process"
    REFERENCE = "reference"
    LEARNING = "learning"


__all__ = [
    "KnowledgeStatus",
    "KnowledgeVisibility",
    "KnowledgeCategory",
]