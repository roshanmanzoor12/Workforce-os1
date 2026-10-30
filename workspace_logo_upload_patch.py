#!/usr/bin/env python3
"""Add authenticated workspace logo upload to Workforce OS. Transactional source backup."""
from __future__ import annotations
import ast,datetime,pathlib,shutil,sys
ROOT=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
ROUTER=pathlib.Path('backend/app/modules/workspaces/logo_router.py')
MAIN=pathlib.Path('backend/app/modules/workspaces/router.py')
PAGE=pathlib.Path('apps/web/app/(workspace)/settings/workspace/page.tsx')
COMP=pathlib.Path('apps/web/components/workspace/workspace-logo-upload.tsx')

def replace_once(s,a,b,label):
    n=s.count(a)
    if n!=1:raise RuntimeError(f'{label}: expected one exact anchor; found {n}. No files changed.')
    return s.replace(a,b)

router_code='''"""Authorized workspace logo file uploads; stored in control-plane object storage."""
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
'''
component_code='''"use client";

import { useRef, useState } from "react";
import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";

export function WorkspaceLogoUpload() {
  const { workspaceId, membership, refreshWorkspaces } = useWorkspace();
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const canEdit = membership?.role_key === "owner" || membership?.role_key === "admin";

  async function upload(file: File) {
    if (!workspaceId || !canEdit || busy) return;
    setError("");
    setMessage("");
    if (file.size > 5 * 1024 * 1024) {
      setError("Choose a JPG, PNG, or WebP smaller than 5 MB.");
      return;
    }
    const data = new FormData();
    data.append("file", file);
    setBusy(true);
    try {
      await api.postForm<{logo_url: string}>(`/workspaces/${workspaceId}/logo/upload`, data);
      await refreshWorkspaces();
      setMessage("Company logo uploaded successfully.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Logo upload failed.");
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <section className="space-y-2 rounded-xl border p-5" aria-label="Upload company logo">
      <h2 className="font-semibold">Upload company logo</h2>
      <p className="text-sm text-muted-foreground">JPG, PNG or WebP, up to 5 MB. This logo belongs only to the selected workspace.</p>
      <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp"
        disabled={!canEdit || busy} aria-label="Company logo file"
        onChange={(event) => { const file = event.target.files?.[0]; if (file) void upload(file); }} />
      {busy ? <p role="status">Uploading company logo…</p> : null}
      {message ? <p role="status" className="text-sm text-green-700">{message}</p> : null}
      {error ? <p role="alert" className="text-sm text-red-600">{error}</p> : null}
    </section>
  );
}
'''

def main():
    if not ROOT.is_dir():raise RuntimeError('Project root does not exist')
    for path in [ROUTER,COMP]:
        if ROOT.joinpath(path).exists():raise RuntimeError(f'{path} already exists, stopping to avoid overwrite.')
    for path in [MAIN,PAGE]:
        if not ROOT.joinpath(path).is_file():raise RuntimeError(f'Missing {path}')
    main_src=(ROOT/MAIN).read_text(encoding='utf-8')
    page_src=(ROOT/PAGE).read_text(encoding='utf-8')
    main_new=main_src.rstrip()+'''\n\n# Company logo upload and image delivery routes.\nfrom .logo_router import router as workspace_logo_router\nrouter.include_router(workspace_logo_router)\n'''
    page_new=replace_once(page_src,'import { workspacesService } from "@/services/workspaces.service";','import { workspacesService } from "@/services/workspaces.service";\nimport { WorkspaceLogoUpload } from "@/components/workspace/workspace-logo-upload";','appearance import')
    page_new=replace_once(page_new,'      <section className="rounded-xl border p-5 space-y-4">','      <WorkspaceLogoUpload />\n\n      <section className="rounded-xl border p-5 space-y-4">','appearance upload insertion')
    ast.parse(router_code)
    ast.parse(main_new)
    changes={MAIN:main_new,PAGE:page_new,ROUTER:router_code,COMP:component_code}
    backup=ROOT/'backups'/('workspace-logo-upload-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    for p in [MAIN,PAGE]:
        out=backup/p;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,out)
    written=[]
    try:
        for p,body in changes.items():
            full=ROOT/p;full.parent.mkdir(parents=True,exist_ok=True);full.write_text(body,encoding='utf-8');written.append(full)
    except Exception:
        for full in written:
            rel=full.relative_to(ROOT)
            if rel in [MAIN,PAGE]:shutil.copy2(backup/rel,full)
            else:full.unlink(missing_ok=True)
        raise
    print('WORKSPACE LOGO UPLOAD PATCH APPLIED. Backup:',backup)
    for p in changes:print(' ',p)
if __name__=='__main__':main()
