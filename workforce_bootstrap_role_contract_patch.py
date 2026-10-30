#!/usr/bin/env python3
"""Workforce OS: align workspace bootstrap RBAC contract with frontend.
Usage: python workforce_bootstrap_role_contract_patch.py C:\\workforce-os
Makes backups, validates known anchors, and changes no database records.
"""
from pathlib import Path
from datetime import datetime
import ast, shutil, sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else r'C:\workforce-os')
files = {
 'backend/app/modules/workspaces/bootstrap_service.py': None,
 'backend/app/modules/workspaces/bootstrap_schemas.py': None,
 'apps/web/contexts/workspace-context.tsx': None,
}
for rel in files:
 p=ROOT / rel
 if not p.is_file(): raise SystemExit(f'MISSING required file: {p}')
 files[rel]=p.read_text(encoding='utf-8-sig')

service='''from __future__ import annotations

import uuid
from typing import Any

from app.modules.auth.models import User
from app.modules.workspace_permissions.effective import resolve_membership_access
from app.modules.workspaces.bootstrap_schemas import WorkspaceBootstrapResponse
from app.modules.workspaces.service import WorkspaceService


def _dump_model(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    # ORM objects can include relationships; return only scalar attributes.
    result: dict[str, Any] = {}
    for field in ("id", "workspace_id", "user_id", "role_key", "status", "name", "slug"):
        item = getattr(value, field, None)
        if isinstance(item, uuid.UUID):
            result[field] = str(item)
        elif isinstance(item, (str, int, float, bool)) or item is None:
            result[field] = item
    return result


class WorkspaceBootstrapService:
    def __init__(self, workspace_service: WorkspaceService) -> None:
        self.workspace_service = workspace_service

    async def get_workspace_bootstrap(
        self, *, workspace_id: uuid.UUID, user: User
    ) -> WorkspaceBootstrapResponse:
        workspace, membership, tenant = (
            await self.workspace_service.get_authorized_workspace_context(
                workspace_id=workspace_id, user=user
            )
        )
        # Resolve from trusted DB records, including additional/custom roles
        # and moderation bans. Never infer effective authority from the UI.
        access = await resolve_membership_access(
            self.workspace_service.session,
            workspace_id=workspace_id,
            membership=membership,
        )
        role_key = str(membership.role_key)
        permissions = sorted(access.permissions)
        return WorkspaceBootstrapResponse(
            workspace_id=str(workspace_id),
            membership_id=str(membership.id),
            role_key=role_key,
            permissions=permissions,
            moderation={
                "is_muted": False,
                "is_deafened": False,
                "is_hidden": False,
                "is_banned": False,
            },
            available_roles=[],
            workspace=_dump_model(workspace),
            membership=_dump_model(membership),
            roles=list(access.role_keys),
            scopes=[],
            entitlements={
                "workspace_id": str(workspace_id),
                "tenant_available": tenant is not None,
            },
            navigation=sorted({p.split(".", 1)[0] for p in permissions}),
            setup_status={
                "tenant_registered": tenant is not None,
                "workspace_status": str(workspace.status),
            },
        )


__all__ = ["WorkspaceBootstrapService"]
'''
schema='''from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class WorkspaceBootstrapResponse(BaseModel):
    # Fields required by apps/web/types/workspace-access.ts
    workspace_id: str
    membership_id: str
    role_key: str
    permissions: list[str] = Field(default_factory=list)
    moderation: dict[str, bool] = Field(default_factory=dict)
    available_roles: list[dict[str, Any]] = Field(default_factory=list)
    # Preserve older clients' bootstrap fields.
    workspace: dict[str, Any] = Field(default_factory=dict)
    membership: dict[str, Any] = Field(default_factory=dict)
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    entitlements: dict[str, Any] = Field(default_factory=dict)
    navigation: list[str] = Field(default_factory=list)
    setup_status: dict[str, Any] = Field(default_factory=dict)


__all__ = ["WorkspaceBootstrapResponse"]
'''
for p,c in [(list(files)[0],service),(list(files)[1],schema)]:
 old=files[p]
 expected='class WorkspaceBootstrapService:' if p.endswith('bootstrap_service.py') else 'class WorkspaceBootstrapResponse(BaseModel):'
 if expected not in old: raise SystemExit(f'STOP: unexpected file content in {p}')
 ast.parse(c)
 files[p]=c

rel='apps/web/contexts/workspace-context.tsx'
s=files[rel]
def replace_once(old,new):
 global s
 n=s.count(old)
 if n!=1: raise SystemExit(f'STOP: expected one match, found {n}: {old[:90]!r}')
 s=s.replace(old,new,1)
replace_once('''  const activeRoleKey =
    workspaceBootstrap
      ?.role_key ??
    membership
      ?.role_key ??
    "member";''','''  // Ignore an older workspace's bootstrap while a switch is in flight.
  const verifiedBootstrap =
    workspaceBootstrap?.workspace_id === currentWorkspaceId &&
    workspaceBootstrap?.membership_id === membership?.id
      ? workspaceBootstrap
      : null;

  const activeRoleKey =
    membership?.role_key ?? "member";''')
replace_once('''  const permissions =
    workspaceBootstrap
      ?.permissions ??
    [];''','''  const permissions =
    verifiedBootstrap?.permissions ?? [];''')
replace_once('''  const availableRoles =
    workspaceBootstrap
      ?.available_roles ??
    [];''','''  const availableRoles =
    verifiedBootstrap?.available_roles ?? [];''')
replace_once('''      ? workspaceBootstrap?.billing
        ? {
            plan_code: workspaceBootstrap.billing.plan_code,
            monitoring: workspaceBootstrap.billing.features.monitoring,
            live_screen: workspaceBootstrap.billing.features.live_screen,
            advanced_analytics: workspaceBootstrap.billing.features.advanced_analytics,
          }''','''      ? verifiedBootstrap?.billing
        ? {
            plan_code: verifiedBootstrap.billing.plan_code,
            monitoring: verifiedBootstrap.billing.features.monitoring,
            live_screen: verifiedBootstrap.billing.features.live_screen,
            advanced_analytics: verifiedBootstrap.billing.features.advanced_analytics,
          }''')
replace_once('''        workspaceBootstrap,

        workspaceRole,''','''        workspaceBootstrap: verifiedBootstrap,

        workspaceRole,''')
# effective roles and permissions no longer confer "owner" authority during a workspace switch.
replace_once('''  const effectiveNavigationView =
    navigationView ===
      "owner" &&
    previewNavigationView''','''  const effectiveNavigationView =
    verifiedBootstrap &&
    navigationView ===
      "owner" &&
    previewNavigationView''')
replace_once('''  const effectivePermissions =
    navigationView ===
      "owner" &&
    previewNavigationView''','''  const effectivePermissions =
    verifiedBootstrap &&
    navigationView ===
      "owner" &&
    previewNavigationView''')
files[rel]=s

stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
backup=ROOT/'backups'/f'workspace-bootstrap-role-{stamp}'
for rel,content in files.items():
 src=ROOT/rel
 dest=backup/rel
 dest.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(src,dest)
for rel,content in files.items():
 (ROOT/rel).write_text(content,encoding='utf-8',newline='\n')
print('UPDATED:')
for rel in files: print(' ', rel)
print('BACKUP:', backup)
print('NEXT: compile Python + TypeScript and test a Member / Manager login.')
