from pathlib import Path
from datetime import datetime
import shutil, sys

root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(r'C:\workforce-os')
changes={}
def edit(rel, fn):
 p=root/rel
 if not p.is_file(): raise RuntimeError(f'Missing {p}')
 old=p.read_text(encoding='utf-8-sig');new=fn(old)
 if new==old: raise RuntimeError(f'No change to {rel}; possibly already installed')
 changes[p]=(old,new)
def replace_once(s,old,new):
 if s.count(old)!=1: raise RuntimeError(f'Expected one anchor, found {s.count(old)} for {old[:95]!r}')
 return s.replace(old,new,1)

def schema(s):
 return replace_once(s,'class WorkspaceInvitationPublic(\n    InvitationSchema\n):\n    id: uuid.UUID', 'class WorkspaceInvitationPublic(\n    InvitationSchema\n):\n    workspace_name: str | None = None\n\n    id: uuid.UUID')
edit('backend/app/modules/workspace_invitations/schemas.py',schema)

def svc(s):
 s=replace_once(s,'DEFAULT_INVITATION_TTL = timedelta(\n    days=7\n)','DEFAULT_INVITATION_TTL = timedelta(\n    days=3\n)')
 s=replace_once(s,'        if expires_at <= now:\n            raise self._invalid(', '        if expires_at > now + DEFAULT_INVITATION_TTL:\n            raise self._invalid("Invitation cannot expire more than 3 days from now.")\n\n        if expires_at <= now:\n            raise self._invalid(')
 old='''        items = await self.repository.list_incoming(user)
        return IncomingWorkspaceInvitationListResponse(items=[self._public(row) for row in items], total=len(items))'''
 new='''        items = await self.repository.list_incoming(user)
        serialized = []
        workspace_names = {}
        for row in items:
            if row.workspace_id not in workspace_names:
                workspace = await self.repository.get_workspace(row.workspace_id)
                workspace_names[row.workspace_id] = workspace.name if workspace is not None else None
            serialized.append(self._public(row).model_copy(update={
                "workspace_name": workspace_names[row.workspace_id]
            }))
        return IncomingWorkspaceInvitationListResponse(items=serialized, total=len(items))'''
 return replace_once(s,old,new)
edit('backend/app/modules/workspace_invitations/service.py',svc)

def typ(s):
 return replace_once(s,'export interface WorkspaceInvitationPublic {\n  id:', 'export interface WorkspaceInvitationPublic {\n  workspace_name?: string | null;\n\n  id:')
edit('apps/web/types/workspace-invitations.ts',typ)

def friends(s):
 old='<strong>Workspace invitation</strong><span>Workspace: {invitation.workspace_id}</span><small>Role: {invitation.role_key} · Expires {new Date(invitation.expires_at).toLocaleDateString()}</small>'
 new='<strong>Invitation to {invitation.workspace_name || "a workspace"}</strong><span>Workspace invitation</span><small>Role: {invitation.role_key} · Expires {new Date(invitation.expires_at).toLocaleDateString()} (new invitations expire after 3 days)</small>'
 return replace_once(s,old,new)
edit('apps/web/app/(workspace)/friends/page.tsx',friends)

def editor(s):
 anchor='''    if (
      !workspaceId
    ) {
      return;
    }'''
 new='''    if (
      !workspaceId
    ) {
      return;
    }

    if (role?.is_builtin) {
      setError("Built-in roles are managed by the system. Create a custom role to choose permissions.");
      return;
    }'''
 s=replace_once(s,anchor,new)
 anchor='''            disabled={
              saving ||
              deleting
            }'''
 new='''            disabled={
              saving ||
              deleting ||
              Boolean(role?.is_builtin)
            }'''
 s=replace_once(s,anchor,new)
 return s
edit('apps/web/components/workspace/role-editor.tsx',editor)

stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
backup=root/'backups'/f'invite-role-followup-{stamp}'
for p,(old,new) in changes.items():
 b=backup/p.relative_to(root);b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
for p,(old,new) in changes.items():
 p.write_text(new,encoding='utf-8')
 print('UPDATED',p.relative_to(root))
print('BACKUP:',backup)
print('NEXT: py_compile, pnpm --dir apps/web exec tsc --noEmit, restart backend')
