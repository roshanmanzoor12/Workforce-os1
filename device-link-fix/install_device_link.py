from pathlib import Path
import shutil, datetime, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
p=root/'apps/web/app/(workspace)/devices/page.tsx'
if not p.exists(): raise SystemExit(f'ERROR page missing: {p}')
s=p.read_text(encoding='utf-8-sig')
if 'WFOS_DEVICE_ACCOUNT_LINK_V1' in s: raise SystemExit('Already installed; no changes.')
checks=['async function saveAssignment()', 'const [assignmentId, setAssignmentId]', 'const [employees, setEmployees]', 'const selectedEmployee =', 'Save assignment', 'onChange={(event) => {\n                            setAssignmentId(event.target.value);']
missing=[x for x in checks if x not in s]
if missing: raise SystemExit('ERROR current page differs; no changes. Missing: '+', '.join(missing))
orig=s
# Fix malformed import from an attempted partial manual edit, if present.
s=s.replace('import { reassignDeviceAndLinkAccount } from "@/lib/devices/reassign-device-and-link-account"\n','')
s=s.replace('import { reassignDeviceAndLinkAccount } from "@/lib/devices/reassign-device-and-link-account";\n','')
anchor='import { api } from "@/lib/api/client";'
s=s.replace(anchor, 'import { workspaceMembersService } from "@/services/workspace-members.service";\nimport type { WorkspaceMemberPublic } from "@/types/workspace-members";\n'+anchor,1)
s=s.replace('  const [employees, setEmployees] = useState<Employee[]>([]);', '  const [employees, setEmployees] = useState<Employee[]>([]);\n  // WFOS_DEVICE_ACCOUNT_LINK_V1\n  const [members, setMembers] = useState<WorkspaceMemberPublic[]>([]);',1)
s=s.replace('  const [assignmentId, setAssignmentId] = useState("");','  const [assignmentId, setAssignmentId] = useState("");\n  const [memberUserId, setMemberUserId] = useState("");',1)
s=s.replace('const [deviceResult, employeeResult] =\n            await Promise.all([','const [deviceResult, employeeResult, memberResult] =\n            await Promise.all([',1)
s=s.replace('              employeesService.list(workspaceId, {\n                includeInactive: true,\n              }),\n            ]);','              employeesService.list(workspaceId, {\n                includeInactive: true,\n              }),\n              workspaceMembersService.list(workspaceId),\n            ]);',1)
s=s.replace('          setEmployees(employeeResult.employees ?? []);','          setEmployees(employeeResult.employees ?? []);\n          setMembers(memberResult.members ?? []);',1)
s=s.replace('          setEmployees([]);','          setEmployees([]);\n          setMembers([]);',1)
anchor='  const selectedReadiness = selected\n'
insert='''  const targetEmployee = employees.find((e) => e.id === assignmentId);
  const linkedMember = targetEmployee?.user_id || "";
  const accountChanged = Boolean(
    targetEmployee && memberUserId && memberUserId !== linkedMember
  );
  const assignmentChanged = Boolean(
    selected && assignmentId !== (selected.employee_id || "")
  );
  const activeMembers = members.filter(
    (m) => m.status.toLowerCase() === "active" && !m.moderation?.is_banned
  );

'''
s=s.replace(anchor,insert+anchor,1)
start=s.index('  async function saveAssignment() {')
end=s.index('  function selectDevice(device: Device) {',start)
s=s[:start]+'''  async function saveAssignment() {
    if (!workspaceId || !selected || !canAssign) return;
    const newId = assignmentId || null;
    const employee = newId ? employees.find((e) => e.id === newId) : undefined;
    const member = memberUserId
      ? activeMembers.find((m) => m.user_id === memberUserId)
      : undefined;

    if (newId && (!employee || !employee.is_active || employee.employment_status !== "active")) {
      setFeedback({ message: "Select an active employee in this workspace.", error: true });
      return;
    }
    if (newId && !member && !employee?.user_id) {
      setFeedback({ message: "Select the employee's active workspace login account first.", error: true });
      return;
    }
    if (employee && member) {
      if (employee.user_id && employee.user_id !== member.user_id) {
        setFeedback({ message: "Employee already linked to another login. Resolve separately.", error: true });
        return;
      }
      if (employees.some((e) => e.id !== employee.id && e.user_id === member.user_id)) {
        setFeedback({ message: "This login is linked to another employee.", error: true });
        return;
      }
      if (employee.work_email?.trim().toLowerCase() !== member.email?.trim().toLowerCase()) {
        setFeedback({ message: "Employee and account email differ. Verify identity before linking.", error: true });
        return;
      }
    }
    if (selected.status === "revoked" || selected.status === "disabled" || !selected.is_active) {
      setFeedback({ message: "Revoked or disabled devices cannot be assigned.", error: true });
      return;
    }
    if (!assignmentChanged && !accountChanged) return;

    setBusy(true);
    setFeedback(null);
    let linkedNow = false;
    try {
      // Account link first. Failed verification never changes the device assignment.
      if (employee && member && !employee.user_id) {
        await employeesService.update(workspaceId, employee.id, { user_id: member.user_id });
        linkedNow = true;
      }
      if (assignmentChanged) {
        await devicesService.assign(workspaceId, selected.id, newId);
      }
      setFeedback({
        message: linkedNow
          ? assignmentChanged
            ? "Account linked and device assignment saved."
            : "Login account linked; existing device assignment preserved."
          : assignmentChanged
            ? newId ? "Device assignment saved." : "Device unassigned."
            : "Already linked.",
        error: false,
      });
      setConfirmUnassign(false);
      await load(true);
    } catch (cause) {
      setFeedback({
        message: `${linkedNow ? "Account link saved, but device assignment failed. " : ""}${cause instanceof Error ? cause.message : "Unable to save changes."}`,
        error: true,
      });
      await load(true);
    } finally {
      setBusy(false);
    }
  }

'''+s[end:]
s=s.replace('    setAssignmentId(device.employee_id || "");','    setAssignmentId(device.employee_id || "");\n    setMemberUserId(employees.find((e) => e.id === device.employee_id)?.user_id || "");',1)
s=s.replace('                            setAssignmentId(event.target.value);\n                            setConfirmUnassign(false);','                            setAssignmentId(event.target.value);\n                            setMemberUserId(employees.find((e) => e.id === event.target.value)?.user_id || "");\n                            setConfirmUnassign(false);',1)
anchor='''                      {assignmentId === "" &&
                        Boolean(selected.employee_id) &&'''
insert='''                      {targetEmployee && (
                        <label className="ed-field">
                          Linked workspace login account
                          <select
                            value={memberUserId}
                            onChange={(event) => setMemberUserId(event.target.value)}
                            disabled={Boolean(targetEmployee.user_id)}
                          >
                            <option value="">Select an active workspace member</option>
                            {activeMembers.map((member) => (
                              <option key={member.user_id} value={member.user_id}>
                                {member.username} · {member.email}
                              </option>
                            ))}
                          </select>
                          <small style={{ color: "#778094", fontWeight: 400 }}>
                            {targetEmployee.user_id
                              ? "This employee already has a linked account."
                              : "Account email must match employee work email. No screen-sharing consent is granted."}
                          </small>
                        </label>
                      )}

'''
if anchor not in s: raise SystemExit('Insertion point missing')
s=s.replace(anchor,insert+anchor,1)
s=s.replace('''                          assignmentId ===
                            (selected.employee_id || "") ||''','''                          (!assignmentChanged && !accountChanged) ||
                          (Boolean(assignmentId) && !memberUserId && !targetEmployee?.user_id) ||''',1)
s=s.replace('''                        Save assignment
''','''                        {accountChanged ? "Save assignment & link account" : "Save assignment"}
''',1)
if s==orig: raise SystemExit('ERROR no modifications made')
backup=p.with_name('page.tsx.backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
shutil.copy2(p,backup)
p.write_text(s,encoding='utf-8')
print('INSTALLED:',p,'\nBACKUP:',backup)
print('Refresh UI, open Device Assignments, select device, employee and member account.')
