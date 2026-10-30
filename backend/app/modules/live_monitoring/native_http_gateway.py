"""In-process HTTP frame gateway after database authorization.

Each endpoint MUST independently validate the actor against the active, unexpired
LiveScreenSession.  Server-generated tokens never leave this module.
Single worker only; restart/redeploy interrupts streams. No recording.
"""
from __future__ import annotations

import asyncio
import time
from .native_frame_relay import NativeFrameRelay, RelayError

relay = NativeFrameRelay()
_lock = asyncio.Lock()
_tickets: dict[str, tuple[str, str, str, float]] = {}

async def _ensure(workspace_id: str, session_id: str, employee_id: str, device_id: str, expiry_seconds: int) -> tuple[str, str]:
    async with _lock:
        existing = _tickets.get(session_id)
        if existing and existing[0] == workspace_id and existing[3] > time.monotonic():
            return existing[1], existing[2]
        if existing:
            await relay.revoke(session_id=session_id, workspace_id=existing[0])
        duration = min(max(expiry_seconds, 1), 900)
        publisher, viewer = await relay.issue(workspace_id=workspace_id, session_id=session_id,
            employee_id=employee_id, device_id=device_id, expires_in=duration)
        _tickets[session_id] = (workspace_id, publisher, viewer, time.monotonic() + duration)
        return publisher, viewer

async def publish(workspace_id: str, session_id: str, employee_id: str, device_id: str,
                  expiry_seconds: int, jpeg: bytes) -> int:
    publisher, _ = await _ensure(workspace_id, session_id, employee_id, device_id, expiry_seconds)
    await relay.approve(session_id=session_id, workspace_id=workspace_id, publisher_token=publisher)
    return await relay.publish(session_id=session_id, workspace_id=workspace_id,
                              publisher_token=publisher, jpeg=jpeg)

async def snapshot(workspace_id: str, session_id: str, employee_id: str, device_id: str,
                   expiry_seconds: int, after: int = 0) -> tuple[int, bytes | None]:
    _, viewer = await _ensure(workspace_id, session_id, employee_id, device_id, expiry_seconds)
    return await relay.snapshot(session_id=session_id, workspace_id=workspace_id,
                                viewer_token=viewer, after=after)

async def revoke(workspace_id: str, session_id: str) -> None:
    async with _lock:
        current = _tickets.pop(session_id, None)
        if current and current[0] == workspace_id:
            await relay.revoke(session_id=session_id, workspace_id=workspace_id)
