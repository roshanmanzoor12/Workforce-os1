from __future__ import annotations

from fastapi import APIRouter

from app.modules.devices.heartbeat_presence_router import (
    router as heartbeat_presence_router,
)
from app.modules.devices.heartbeat_router import (
    router as heartbeat_router,
)


__all__ = [
    "router",
]


router = APIRouter()


router.include_router(
    heartbeat_router
)

router.include_router(
    heartbeat_presence_router
)