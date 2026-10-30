"""Development browser-to-browser screen share, explicit employee consent.
Not a Windows service capture transport; in-memory state, single worker only.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.modules.employees.models import Employee
from app.modules.live_monitoring.access import resolve_live_monitoring_access, can_access_employee
from app.modules.tenant_api.dependencies import get_authorized_tenant_context

router = APIRouter(prefix="/workspaces/{workspace_id}/browser-screen-share", tags=["browser-screen-share"])
Context = Annotated[Any, Depends(get_authorized_tenant_context)]
_lock = asyncio.Lock()
_rooms: dict[str, dict[str, Any]] = {}
TTL = timedelta(minutes=15)


def now() -> datetime:
    return datetime.now(timezone.utc)


def clean() -> None:
    deadline = now() - TTL
    for key, room in list(_rooms.items()):
        if room["created"] < deadline:
            _rooms.pop(key, None)


def view(room: dict[str, Any]) -> dict[str, Any]:
    return {"id": room["id"], "employee_id": room["employee_id"], "status": room["status"],
            "offer": room["offer"], "answer": room["answer"]}


def room_for(workspace_id: uuid.UUID, room_id: uuid.UUID, actor: uuid.UUID) -> dict[str, Any]:
    room = _rooms.get(str(room_id))
    if not room or room["workspace_id"] != str(workspace_id):
        raise HTTPException(404, "Share request not found or expired")
    if str(actor) not in (room["owner_id"], room["employee_user_id"]):
        raise HTTPException(403, "Not a participant in this share")
    return room


class NewRequest(BaseModel):
    employee_id: uuid.UUID


class Signal(BaseModel):
    sdp: str = Field(min_length=10, max_length=150000)
    type: Literal["offer", "answer"]


@router.post("/requests")
async def create_request(workspace_id: uuid.UUID, payload: NewRequest, context: Context):
    access = await resolve_live_monitoring_access(workspace_id=workspace_id, context=context)
    if not access.can_request_live_screen or not can_access_employee(access=access, employee_id=payload.employee_id):
        raise HTTPException(403, "Live-screen permission required")
    employee = await context.tenant_session.scalar(select(Employee).where(
        Employee.id == payload.employee_id, Employee.is_active.is_(True)))
    if not employee or not employee.user_id:
        raise HTTPException(409, "Employee must be linked to an active workspace account")
    if employee.user_id == context.actor_user_id:
        raise HTTPException(400, "Cannot request sharing from yourself")
    room_id = str(uuid.uuid4())
    async with _lock:
        clean()
        _rooms[room_id] = {"id": room_id, "workspace_id": str(workspace_id),
                           "employee_id": str(payload.employee_id), "employee_user_id": str(employee.user_id),
                           "owner_id": str(context.actor_user_id), "created": now(), "status": "pending",
                           "offer": None, "answer": None}
        return view(_rooms[room_id])


@router.get("/inbox")
async def inbox(workspace_id: uuid.UUID, context: Context):
    async with _lock:
        clean()
        return {"requests": [view(r) for r in _rooms.values()
                if r["workspace_id"] == str(workspace_id)
                and r["employee_user_id"] == str(context.actor_user_id)
                and r["status"] in ("pending", "offered", "connected")]}


@router.get("/requests/{room_id}")
async def get_request(workspace_id: uuid.UUID, room_id: uuid.UUID, context: Context):
    async with _lock:
        clean()
        return view(room_for(workspace_id, room_id, context.actor_user_id))


@router.post("/requests/{room_id}/signal")
async def signal(workspace_id: uuid.UUID, room_id: uuid.UUID, payload: Signal, context: Context):
    async with _lock:
        clean()
        room = room_for(workspace_id, room_id, context.actor_user_id)
        if payload.type == "offer":
            if str(context.actor_user_id) != room["employee_user_id"] or room["status"] != "pending":
                raise HTTPException(409, "Only invited employee can initiate a pending share")
            room["offer"] = payload.model_dump()
            room["status"] = "offered"
        else:
            if str(context.actor_user_id) != room["owner_id"] or room["status"] != "offered":
                raise HTTPException(409, "Only requester can answer a share offer")
            room["answer"] = payload.model_dump()
            room["status"] = "connected"
        return view(room)


@router.post("/requests/{room_id}/stop")
async def stop(workspace_id: uuid.UUID, room_id: uuid.UUID, context: Context):
    async with _lock:
        room = room_for(workspace_id, room_id, context.actor_user_id)
        room["status"] = "ended"
        room["offer"] = None
        room["answer"] = None
        return {"status": "ended"}
