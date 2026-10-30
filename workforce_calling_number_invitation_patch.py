"""Patch Calling Number invitations against the Workforce OS source layout.
Run: python workforce_calling_number_invitation_patch.py C:\\workforce-os
"""
from pathlib import Path
from datetime import datetime
import sys, shutil, ast

root=Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
repo=root/'backend/app/modules/workspace_invitations/repository.py'
service=root/'backend/app/modules/workspace_invitations/service.py'
frontend=root/'apps/web/components/workspace/invite-members-button.tsx'
paths=(repo,service,frontend)
for p in paths:
    if not p.is_file(): raise SystemExit(f'Missing: {p}')
original={p:p.read_text(encoding='utf-8-sig') for p in paths}

def once(text, old, new, description):
    count=text.count(old)
    if count!=1: raise RuntimeError(f'{description}: expected exactly one match, found {count}. Nothing changed.')
    return text.replace(old,new)

r=original[repo]
r=once(r, 'from sqlalchemy import (\n    func,\n    select,\n)',
'''from sqlalchemy import (
    Column,
    MetaData,
    String,
    Table,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID''','repository imports')
marker='''class WorkspaceInvitationRepository:
'''
r=once(r,marker,'''# Match the existing personal Calling Number table; do not allocate numbers
# or require the user to share their email with the inviter.
_calling_numbers = Table(
    "personal_call_numbers_v1",
    MetaData(),
    Column("user_id", PG_UUID(as_uuid=True), primary_key=True),
    Column("calling_number", String(10), nullable=False),
)


class WorkspaceInvitationRepository:
''','calling-number table')
old='''        condition = (User.id == target_id) if target_id else (func.lower(User.username) == value)
        result = await self.session.execute(select(User).where(condition, User.is_active.is_(True), User.is_locked.is_(False), User.is_email_verified.is_(True)))
        return result.scalar_one_or_none()'''
new='''        if target_id is None and len(value) == 10 and value.isascii() and value.isdecimal():
            statement = (
                select(User)
                .join(_calling_numbers, _calling_numbers.c.user_id == User.id)
                .where(_calling_numbers.c.calling_number == value)
            )
        else:
            condition = (User.id == target_id) if target_id else (func.lower(User.username) == value)
            statement = select(User).where(condition)

        result = await self.session.execute(
            statement.where(
                User.is_active.is_(True),
                User.is_locked.is_(False),
                User.is_email_verified.is_(True),
            )
        )
        return result.scalar_one_or_none()'''
r=once(r,old,new,'repository account lookup')
ast.parse(r)

s=original[service]
s=once(s,'No verified user found for this username or account ID.',
       'No verified user found for this Calling Number, username, or account ID.','service lookup error')
s=once(s,'Email or username/account ID is required.',
       'Email, Calling Number, username, or account ID is required.','service missing-identifier error')
ast.parse(s)

f=original[frontend]
f=once(f,'type Method = "email" | "username" | "account";',
       'type Method = "calling" | "email" | "username" | "account";','frontend identifier type')
f=once(f,'useState<Method>("email")','useState<Method>("calling")','frontend method default')
f=once(f,'function open() { setMethod("email");',
       'function open() { setMethod("calling");','frontend dialog default')
f=once(f,'<option value="email">Email</option><option value="username">Username</option>',
       '<option value="calling">Calling Number</option><option value="email">Email</option><option value="username">Username</option>','frontend select')
f=once(f,'method === "username" ? "Username" : "Account User ID"',
       'method === "calling" ? "Calling Number" : method === "username" ? "Username" : "Account User ID"','frontend input label')
f=once(f,'type={method === "email" ? "email" : "text"} required maxLength={320}',
       'type={method === "email" ? "email" : "text"} required maxLength={method === "calling" ? 10 : 320} minLength={method === "calling" ? 10 : 3} inputMode={method === "calling" ? "numeric" : undefined} pattern={method === "calling" ? "[0-9]{10}" : undefined}',
       'frontend input validation')
f=once(f,'method === "username" ? "@username" : "User ID"',
       'method === "calling" ? "10-digit Calling Number" : method === "username" ? "@username" : "User ID"','frontend placeholder')
updated={repo:r,service:s,frontend:f}
backup=root/'backups'/f'calling-number-invite-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
for p in paths:
    dest=backup/p.relative_to(root)
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,dest)
try:
    for p in paths: p.write_text(updated[p],encoding='utf-8',newline='')
except BaseException:
    for p in paths: shutil.copy2(backup/p.relative_to(root),p)
    raise
print('PATCH APPLIED:')
for p in paths: print(' ',p)
print('Backup:',backup)
print('NEXT: run backend py_compile, TypeScript, and test Calling Number invitation with two accounts.')
