from __future__ import annotations

from fastapi import APIRouter

from app.modules.activity.agent_router import (
    router as activity_agent_router,
)


__all__ = [
    "router",
]


router = APIRouter()

router.include_router(
    activity_agent_router
)