from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select

from app.db.tenant_dependency import TenantScope
from app.modules.auth.models import User
from app.modules.workspace_permissions.service import WorkspacePermissionService
from .models import WorkspaceMembership

router = APIRouter()


class DirectoryMember(BaseModel):
    id: str
    name: str
    email: str
    role: str
    status: str
    account_active: bool
    joined_at: datetime | None


class DirectoryResponse(BaseModel):
    items: list[DirectoryMember]
    total: int
    page: int
    page_size: int


@router.get('/{workspace_id}/directory', response_model=DirectoryResponse)
async def directory(
    scope: TenantScope,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str, Query(max_length=80)] = '',
    clients_only: bool = False,
):
    # Existing tenant authorization and billing run before directory access.
    WorkspacePermissionService(scope).require('members.read')
    db = scope.control_session
    if db is None:
        raise HTTPException(503, 'The workspace directory is temporarily unavailable.')
    member = WorkspaceMembership.__table__.c
    user = User.__table__.c
    predicates = [member.workspace_id == scope.workspace_id, member.status != 'removed']
    if clients_only:
        predicates.append(func.lower(member.role_key) == 'client')
    term = search.strip()
    if term:
        escaped = term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        pattern = '%' + escaped + '%'
        predicates.append(or_(user.username.ilike(pattern, escape='\\'),
                              user.email.ilike(pattern, escape='\\')))
    joined = WorkspaceMembership.__table__.join(User.__table__, member.user_id == user.id)
    total = int(await db.scalar(select(func.count()).select_from(joined).where(*predicates)) or 0)
    rows = (await db.execute(select(
        member.id, member.role_key, member.status, member.joined_at,
        user.username, user.email, user.is_active,
    ).select_from(joined).where(*predicates).order_by(user.username, member.id)
      .offset((page - 1) * page_size).limit(page_size))).mappings().all()
    return DirectoryResponse(items=[DirectoryMember(
        id=str(row['id']), name=row['username'],
        email=row['email'], role=row['role_key'], status=row['status'],
        account_active=row['is_active'], joined_at=row['joined_at'],
    ) for row in rows], total=total, page=page, page_size=page_size)
