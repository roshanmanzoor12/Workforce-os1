"""Apply minimal role invitation fixes to an existing Workforce OS checkout.
Run: python workforce_role_invitation_patch.py C:\\workforce-os
Requires current source patterns from 2026-10-21 exports. Backs up and rolls back on errors.
"""
from pathlib import Path
from datetime import datetime
import sys, shutil, re, ast

root=Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
service=root/'backend/app/modules/workspace_invitations/service.py'
front=root/'apps/web/components/workspace/invite-members-button.tsx'
paths=[service,front]
for p in paths:
    if not p.is_file(): raise SystemExit(f'Missing file: {p}')
orig={p:p.read_text(encoding='utf-8-sig') for p in paths}

def once(s, old, new, name):
    count=s.count(old)
    if count!=1: raise RuntimeError(f'{name}: expected one occurrence, found {count}. NO files modified.')
    return s.replace(old,new)

s=orig[service]
s=once(s, 'from app.modules.workspace_permissions.policy import (\n    WorkspacePermissionPolicy,\n)\n',
'''from app.modules.workspace_permissions.effective import resolve_membership_access
from app.modules.workspace_rbac.repository import WorkspaceRBACRepository
from app.modules.workspace_permissions.roles import BUILT_IN_ROLE_KEYS
''', 'backend imports')
start='''        allowed = (
            WorkspacePermissionPolicy
            .allows(
                role_key=(
                    membership.role_key
                ),
                permission=(
                    WorkspacePermission
                    .MEMBERS_INVITE
                    .value
                ),
            )
        )'''
replacement='''        access = await resolve_membership_access(
            self.session,
            workspace_id=workspace_id,
            membership=membership,
        )
        allowed = WorkspacePermission.MEMBERS_INVITE.value in access.permissions'''
s=once(s,start,replacement,'backend invite authorization')
old='''        # The invitation must reference a role the backend recognizes.
        # Custom-role membership authorization remains enforced separately.
        from app.modules.workspace_permissions.roles import BUILT_IN_ROLE_KEYS
        if request.role_key not in BUILT_IN_ROLE_KEYS:
            raise self._invalid("This role is not supported by the invitation membership backend yet.")'''
new='''        # Never allow invitations to grant ownership. Custom roles must
        # exist, be active, and belong to this workspace.
        if request.role_key == "owner":
            raise self._invalid("Ownership cannot be granted by invitation.")
        if request.role_key not in BUILT_IN_ROLE_KEYS:
            custom_role = await WorkspaceRBACRepository(
                self.session
            ).get_custom_role_by_key(
                workspace_id=workspace_id,
                role_key=request.role_key,
            )
            if custom_role is None or not custom_role.is_active:
                raise self._invalid("Workspace role does not exist or is inactive.")'''
s=once(s,old,new,'backend role validation')
ast.parse(s)
f=orig[front]
f=once(f,'const builtinKeys = new Set(["admin", "manager", "member", "client"]);\n\n','', 'frontend built-in filter')
f=once(f,'data.roles.filter(role => role.is_active && builtinKeys.has(role.role_key))',
          'data.roles.filter(role => role.is_active && role.role_key !== "owner")', 'frontend role choices')
f=once(f,'Role permissions are enforced by the workspace backend. Custom roles need server-side membership support before they can be assigned.',
       'The selected role controls workspace access. Workspace Owners cannot be invited.', 'frontend help copy')
updated={service:s,front:f}
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
backup=root/'backups'/f'custom-role-invite-{stamp}'
for p in paths:
    target=backup/p.relative_to(root)
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,target)
try:
    for p in paths: p.write_text(updated[p],encoding='utf-8',newline='')
except Exception:
    for p in paths: shutil.copy2(backup/p.relative_to(root),p)
    raise
print('PATCH APPLIED to:')
for p in paths: print(' ',p)
print('Backup:',backup)
print('NEXT: run py_compile, TypeScript, then a custom-role invitation test.')
