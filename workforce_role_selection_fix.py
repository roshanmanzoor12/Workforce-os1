from pathlib import Path
from datetime import datetime
import shutil,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
paths=[root/'apps/web/components/workspace/roles-access-client.tsx',root/'apps/web/components/workspace/role-list.tsx']
for path in paths:
 if not path.is_file(): raise SystemExit(f'MISSING: {path}')
source=[p.read_text(encoding='utf-8') for p in paths]
def once(s,old,new):
 c=s.count(old)
 if c!=1: raise ValueError(f'Expected one match, found {c}: {old[:120]}')
 return s.replace(old,new,1)
a,b=source
# Null role IDs are ambiguous for all built-in roles. Use unique keys instead.
# Every built-in role has id=None; use role_key for UI selection only.
a=a.replace('role.id', 'role.role_key').replace('item.id', 'item.role_key')
a=a.replace('?.id ??', '?.role_key ??')
# Built-ins are read-only server templates; their 126/57/32 etc permissions must be shown, not re-created.
a=once(a,'<RoleEditor\n            workspaceId=', '''{!creating && selectedRole?.is_builtin ? (
            <section className="panel" style={{ padding: 20 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>
                {selectedRole.display_name} — built-in permissions
              </h2>
              <p style={{ marginBottom: 15, color: "#697586", fontSize: 13 }}>
                This system role has {selectedRole.permissions.length} fixed permissions.
                To customize what a user can access, create a custom role and assign it to that member.
              </p>
              <div style={{ display: "grid", gap: 9, gridTemplateColumns: "repeat(auto-fit,minmax(210px,1fr))" }}>
                {catalog.filter((p) => selectedRole.permissions.includes(p.key)).map((p) => (
                  <div key={p.key} style={{ background: "#fffefa", border: "1px solid #e8e0d3", padding: 10, borderRadius: 8 }}>
                    <strong style={{ fontSize: 12 }}>{p.label}</strong>
                    <div style={{ fontSize: 11, color: "#6b7280" }}>{p.key}</div>
                  </div>
                ))}
              </div>
            </section>
          ) : (
          <RoleEditor
             workspaceId=''')
a=once(a, '          />\n        </PermissionGate>', '          />\n          )}\n        </PermissionGate>')
# Role list highlights based on key.
b=once(b,'selectedRoleId ===\n                role.id','selectedRoleId ===\n                role.role_key')
if a==source[0] or b==source[1]: raise SystemExit('No changes')
backup=root/'backups'/('role-selection-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
for p in paths:
 t=backup/p.relative_to(root);t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,t)
for p,s in zip(paths,[a,b]):p.write_text(s,encoding='utf-8')
print('PATCH APPLIED:',*[str(p) for p in paths],sep='\n  ')
print('BACKUP:',backup)
