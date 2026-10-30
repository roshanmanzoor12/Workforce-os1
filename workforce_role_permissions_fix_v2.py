"""Workforce OS workspace-scoped built-in role overrides. Run from repository root.
Backs up files; fails closed on unexpected source; no DB migration automatically executed.
"""
from pathlib import Path
from datetime import datetime
import re, shutil, sys, ast

root = Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os').resolve()
files = {}
def edit(rel, fn):
    path=root/rel
    if not path.is_file(): raise RuntimeError(f'Missing source: {rel}')
    old=path.read_text(encoding='utf-8-sig'); new=fn(old)
    if new==old: raise RuntimeError(f'No matching source for {rel} (not patched)')
    files[rel]=new

def replace_once(s, old, new, context):
    if s.count(old)!=1: raise RuntimeError(f'Unexpected {context}: found {s.count(old)} matches')
    return s.replace(old,new,1)

MODEL='backend/app/modules/workspace_rbac/models.py'
def model_patch(s):
    s=replace_once(s,'from sqlalchemy import (\n    Boolean,\n','from sqlalchemy import (\n    Boolean,\n    JSON,\n', 'model imports')
    marker='# =========================================================\n# MEMBER MODERATION STATE'
    new='''class WorkspaceBuiltinRoleOverride(StandardModelMixin, Base):
    """Workspace-local replacement policy for a non-owner built-in role."""
    __tablename__ = "workspace_builtin_role_overrides"
    __table_args__ = (
        UniqueConstraint("workspace_id", "role_key", name="uq_builtin_role_override_workspace_key"),
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    role_key: Mapped[str] = mapped_column(String(64), nullable=False)
    permissions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


'''
    return replace_once(s,marker,new+marker,'model anchor')
edit(MODEL,model_patch)

EFFECTIVE='backend/app/modules/workspace_permissions/effective.py'
def effective_patch(s):
    s=replace_once(s,'from app.modules.workspace_rbac.repository import (','from app.modules.workspace_rbac.models import WorkspaceBuiltinRoleOverride\nfrom sqlalchemy import select\nfrom app.modules.workspace_rbac.repository import (','effective imports')
    s=replace_once(s,'    repository: WorkspaceRBACRepository,\n    *,\n    workspace_id:', '    repository: WorkspaceRBACRepository,\n    *,\n    workspace_id:', 'resolve role anchor') if False else s
    original='''        return _known_permissions(
            WorkspacePermissionPolicy.permissions_for_role(role_key)
        )'''
    replacement='''        if role_key != OWNER_ROLE:
            override = await repository.session.scalar(
                select(WorkspaceBuiltinRoleOverride).where(
                    WorkspaceBuiltinRoleOverride.workspace_id == workspace_id,
                    WorkspaceBuiltinRoleOverride.role_key == role_key,
                )
            )
            if override is not None:
                return _known_permissions(override.permissions or [])
        return _known_permissions(
            WorkspacePermissionPolicy.permissions_for_role(role_key)
        )'''
    return replace_once(s, original, replacement,'effective permissions resolver')
edit(EFFECTIVE,effective_patch)

SERVICE='backend/app/modules/workspace_rbac/service.py'
def service_patch(s):
    s=replace_once(s,'from app.modules.workspace_rbac.repository import WorkspaceRBACRepository','from app.modules.workspace_rbac.models import WorkspaceBuiltinRoleOverride\nfrom app.modules.workspace_rbac.repository import WorkspaceRBACRepository','service model import')
    anchor='''    async def permissions_for(
'''
    helper='''    async def _built_in_permissions(self, workspace_id: uuid.UUID, role_key: str) -> frozenset[str]:
        if role_key == WORKSPACE_ROLE_OWNER:
            return frozenset(ALL_WORKSPACE_PERMISSIONS)
        override = await self.session.scalar(
            select(WorkspaceBuiltinRoleOverride).where(
                WorkspaceBuiltinRoleOverride.workspace_id == workspace_id,
                WorkspaceBuiltinRoleOverride.role_key == role_key,
            )
        )
        if override is not None:
            return frozenset(key for key in (override.permissions or []) if key in ALL_WORKSPACE_PERMISSIONS)
        return frozenset(WorkspacePermissionPolicy.permissions_for_role(role_key))

    async def update_builtin_role(
        self, *, workspace_id: uuid.UUID, role_key: str,
        permissions: list[str], user: User,
    ) -> WorkspaceRolePublic:
        """Replace one workspace's non-owner role policy atomically."""
        normalized = role_key.strip().lower()
        if normalized not in BUILT_IN_ROLE_KEYS or normalized == WORKSPACE_ROLE_OWNER:
            raise ValidationError("Owner or unknown built-in role cannot be edited.")
        requested = set(permissions)
        unknown = requested - ALL_WORKSPACE_PERMISSIONS
        if unknown:
            raise ValidationError("Unknown permissions: " + ", ".join(sorted(unknown)))
        try:
            actor = await self._require(
                workspace_id=workspace_id, user=user,
                permission=WorkspacePermission.ROLES_MANAGE.value,
            )
            # Only a primary owner may alter system role policies.
            if actor.role_key != WORKSPACE_ROLE_OWNER:
                raise HTTPException(status_code=403, detail="Workspace owner required to edit built-in roles.")
            await self._assert_grantable(actor, requested)
            override = await self.session.scalar(
                select(WorkspaceBuiltinRoleOverride).where(
                    WorkspaceBuiltinRoleOverride.workspace_id == workspace_id,
                    WorkspaceBuiltinRoleOverride.role_key == normalized,
                ).with_for_update()
            )
            if override is None:
                override = WorkspaceBuiltinRoleOverride(
                    workspace_id=workspace_id, role_key=normalized,
                    permissions=sorted(requested),
                )
                self.session.add(override)
            else:
                override.permissions = sorted(requested)
            await self.session.commit()
            return WorkspaceRolePublic(
                id=None, role_key=normalized,
                display_name=ROLE_DISPLAY_NAMES[normalized], description=None,
                permissions=sorted(requested), is_builtin=True,
                is_immutable=False, is_active=True,
            )
        except Exception:
            await self.session.rollback()
            raise

'''
    s=replace_once(s,anchor,helper+anchor,'service helper insertion')
    old='''            return frozenset(
                WorkspacePermissionPolicy.permissions_for_role(normalized)
            )'''
    s=replace_once(s,old,'            return await self._built_in_permissions(workspace_id, normalized)','service permissions_for')
    old='''            return frozenset(
                WorkspacePermissionPolicy.permissions_for_role(role_key)
            )'''
    s=replace_once(s,old,'            return await self._built_in_permissions(workspace_id, role_key)','service assignment permissions')
    old='''            permissions = WorkspacePermissionPolicy.permissions_for_role(
                role_key
            )'''
    s=replace_once(s,old,'            permissions = await self._built_in_permissions(workspace_id, role_key)','service list roles')
    return s
edit(SERVICE,service_patch)

ROUTER='backend/app/modules/workspace_rbac/router.py'
def router_patch(s):
    anchor='''@router.post(
    "/roles",
'''
    endpoint='''@router.put("/roles/builtin/{role_key}", response_model=WorkspaceRolePublic)
async def update_builtin_workspace_role(
    workspace_id: uuid.UUID,
    role_key: str,
    payload: WorkspaceRoleUpdateRequest,
    service: ServiceDependency,
    user: VerifiedUser,
) -> WorkspaceRolePublic:
    if payload.permissions is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="permissions list is required")
    return await service.update_builtin_role(
        workspace_id=workspace_id, role_key=role_key,
        permissions=payload.permissions, user=user,
    )


'''
    return replace_once(s,anchor,endpoint+anchor,'RBAC router anchor')
edit(ROUTER,router_patch)

# Frontend supports both custom roles (UUID PATCH) and built-in roles (role-key PUT).
EDITOR='apps/web/components/workspace/role-editor.tsx'
def editor_patch(s):
    # Existing submit path always creates a role when editing an id-less built-in.
    pattern=r'if\s*\(\s*editing\s*&&\s*role\?\.id\s*\)'
    hits=list(re.finditer(pattern,s))
    if len(hits)!=1: raise RuntimeError('Unexpected role-editor submit guard')
    s=s[:hits[0].start()]+'''if (editing && role && (role.id || role.is_builtin))'''+s[hits[0].end():]
    pat=r'workspaceRolesService\.update\(\s*workspaceId,\s*role\.id,\s*\{'
    hits=list(re.finditer(pat,s))
    if len(hits)!=1: raise RuntimeError('Unexpected role-editor update call')
    s=s[:hits[0].start()]+'''(role.is_builtin
            ? workspaceRolesService.updateBuiltin(workspaceId, role.role_key, {
                permissions: Array.from(selectedPermissions),
              })
            : workspaceRolesService.update(workspaceId, role.id!, {'''+s[hits[0].end():]
    # Existing code ended await update call with `);`; close ternary expression too
    pos=s.find('        onSaved?.',hits[0].start())
    if pos<0: raise RuntimeError('Cannot find role-editor onSaved')
    segment=s[hits[0].start():pos]
    # change the LAST `);` in this segment to `));` to close ternary grouping
    ix=segment.rfind(');')
    if ix<0: raise RuntimeError('Cannot find role-editor call end')
    segment=segment[:ix]+'));'+segment[ix+2:]
    s=s[:hits[0].start()]+segment+s[pos:]
    # Built-ins cannot rename/disable; submitted update only changes permissions.
    return s
edit(EDITOR,editor_patch)

ROLE_SERVICE='apps/web/services/workspace-roles.service.ts'
def roles_service_patch(s):
    anchor='async function remove('
    f='''async function updateBuiltin(
  workspaceId: string,
  roleKey: string,
  payload: { permissions: string[] },
): Promise<WorkspaceRolePublic> {
  const response = await api.put<WorkspaceRolePublic>(
    `/workspaces/${workspaceId}/roles/builtin/${encodeURIComponent(roleKey)}`,
    payload,
  );
  return normalizeRole(response);
}


'''
    s=replace_once(s,anchor,f+anchor,'roles service helper')
    match=re.search(r'export const workspaceRolesService\s*=\s*\{',s)
    if not match: raise RuntimeError('Missing roles service export')
    s=s[:match.end()]+ '\n  updateBuiltin,\n'+s[match.end():]
    return s
edit(ROLE_SERVICE,roles_service_patch)

# Fix built-in selection where all built-ins have id=null (always choose role_key).
ACCESS='apps/web/components/workspace/roles-access-client.tsx'
def access_patch(s):
    # replace identity comparisons and selection with stable synthetic key, preserving custom role UUID.
    s=re.sub(r'role\.id\s*===\s*previous', '(role.id ?? role.role_key) === previous',s)
    s=re.sub(r'role\.id\s*===\s*selectedRoleId', '(role.id ?? role.role_key) === selectedRoleId',s)
    s=re.sub(r'item\.id\s*===\s*role\.id', '(item.id ?? item.role_key) === (role.id ?? role.role_key)',s)
    s=re.sub(r'item\.id\s*===\s*selectedRoleId', '(item.id ?? item.role_key) === selectedRoleId',s)
    s=re.sub(r'role\.id\s*!==\s*selectedRoleId', '(role.id ?? role.role_key) !== selectedRoleId',s)
    # role.id in identifier setters / fallbacks only
    s=re.sub(r'roleResponse\.roles\[0\]\s*\?\.id\s*\?\?', '(roleResponse.roles[0]?.id ?? roleResponse.roles[0]?.role_key) ??',s)
    s=re.sub(r'setSelectedRoleId\(\s*role\.id\s*,?\s*\)', 'setSelectedRoleId(role.id ?? role.role_key)',s)
    s=re.sub(r'remaining\[0\]\s*\?\.id\s*\?\?', '(remaining[0]?.id ?? remaining[0]?.role_key) ??',s)
    return s
# The role-selection hotfix already uses role_key on newer checkouts.
# Do not insist on editing a file whose role identity is already correct.
access_source = (root / ACCESS).read_text(encoding="utf-8-sig")
if "role.role_key ===" in access_source and "setSelectedRoleId(\n      role.role_key," in access_source:
    print("SKIPPED already-fixed role selector:", ACCESS)
else:
    edit(ACCESS, access_patch)

# Built-in role selector itself may still compare null IDs; fix if its source is present.
ROLE_LIST='apps/web/components/workspace/role-list.tsx'
def role_list_patch(s):
    s2=re.sub(r'role\.id\s*===\s*selectedRoleId','(role.id ?? role.role_key) === selectedRoleId',s)
    s2=re.sub(r'selectedRoleId\s*===\s*role\.id','selectedRoleId === (role.id ?? role.role_key)',s2)
    return s2
if (root/ROLE_LIST).is_file():
    try: edit(ROLE_LIST,role_list_patch)
    except RuntimeError as e:
        if 'not patched' not in str(e): raise

MIGRATION='backend/migrations/control/versions/ws_builtin_roles_20261021_01.py'
if (root/MIGRATION).exists(): raise RuntimeError('Migration name already exists; stop to avoid collision')
files[MIGRATION]='''"""Per-workspace permission overrides for non-owner built-in roles.

Revision ID: ws_builtin_roles_20261021_01
Revises: ws_theme_20261021_01
"""
from alembic import op
import sqlalchemy as sa

revision = "ws_builtin_roles_20261021_01"
down_revision = "ws_theme_20261021_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "workspace_builtin_role_overrides",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("workspace_id", sa.Uuid(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_key", sa.String(64), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.UniqueConstraint("workspace_id", "role_key", name="uq_builtin_role_override_workspace_key"),
        sa.CheckConstraint("role_key IN ('admin', 'manager', 'member', 'client')", name="ck_builtin_role_override_role_key"),
    )


def downgrade():
    op.drop_table("workspace_builtin_role_overrides")
'''

# Validate all patches before ANY files are overwritten.
for rel, content in files.items():
    if rel.endswith('.py'):
        ast.parse(content, filename=rel)
backup=root/'backups'/('builtin-role-fix-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
try:
    for rel in files:
        src=root/rel
        if src.exists():
            dst=backup/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    for rel,content in files.items():
        dst=root/rel; dst.parent.mkdir(parents=True,exist_ok=True); dst.write_text(content,encoding='utf-8')
except Exception:
    for rel in files:
        saved=backup/rel
        if saved.exists(): shutil.copy2(saved,root/rel)
        elif (root/rel).exists(): (root/rel).unlink()
    raise
print('PATCH INSTALLED:',len(files),'files')
print('BACKUP:',backup)
print('NEXT: Run alembic upgrade head against CONTROL database, then pnpm --dir apps/web exec tsc --noEmit')
