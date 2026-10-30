"""Authorized workspace logo file uploads; stored in control-plane object storage."""
from __future__ import annotations

from functools import partial
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.database import get_control_db
from app.core.exceptions import StorageError
from app.core.storage import download_bytes, upload_bytes
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user
from app.modules.personal_account.avatar_images import MAX_UPLOAD_BYTES, crop_profile_photo
from app.modules.workspaces.service import WorkspaceService

router = APIRouter(tags=["Workspace appearance"])


@router.post("/{workspace_id}/logo/upload")
async def upload_workspace_logo(
    workspace_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    service = WorkspaceService(db)
    workspace, membership, _ = await service.get_authorized_workspace_context(
        workspace_id=workspace_id, user=user,
    )
    if membership.role_key not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only workspace Owners/Admins can change company logos.")
    if not workspace.is_active or workspace.status == "archived":
        raise HTTPException(status_code=409, detail="This workspace cannot be modified.")
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()
    try:
        encoded = await run_in_threadpool(crop_profile_photo, content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    version = uuid.uuid4()
    key = f"workspace-logos/{workspace_id}/{version}.webp"
    try:
        await run_in_threadpool(partial(upload_bytes, object_key=key, data=encoded, content_type="image/webp"))
    except StorageError as exc:
        raise HTTPException(status_code=503, detail="Logo storage is unavailable. The existing logo remains unchanged.") from exc

    workspace.logo_url = f"/api/v1/workspaces/logos/{workspace_id}/{version}.webp"
    try:
        await db.commit()
        await db.refresh(workspace)
    except Exception:
        await db.rollback()
        raise
    return {"logo_url": workspace.logo_url, "workspace_id": str(workspace.id)}


@router.get("/logos/{workspace_id}/{version}.webp")
async def get_workspace_logo(workspace_id: uuid.UUID, version: uuid.UUID):
    # UUID-only path values; users cannot select arbitrary object-store keys.
    key = f"workspace-logos/{workspace_id}/{version}.webp"
    try:
        data = await run_in_threadpool(partial(download_bytes, object_key=key))
    except StorageError as exc:
        raise HTTPException(status_code=404, detail="Workspace logo is unavailable.") from exc
    return Response(data, media_type="image/webp", headers={
        "Cache-Control": "public, max-age=31536000, immutable",
        "X-Content-Type-Options": "nosniff",
    })
