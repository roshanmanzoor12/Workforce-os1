from __future__ import annotations

from enum import StrEnum


class TemplateAnalysisStatus(StrEnum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class TemplateFramework(StrEnum):
    STATIC_HTML = "static_html"
    PHP = "php"
    REACT = "react"
    NEXT = "next"
    TAILWIND = "tailwind"


__all__ = [
    "TemplateAnalysisStatus",
    "TemplateFramework",
]