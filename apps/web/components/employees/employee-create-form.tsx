
"use client";

import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Link2,
  Loader2,
  Mail,
  UserPlus,
  Users,
} from "lucide-react";

import { useWorkspace } from "@/contexts/workspace-context";
import {
  employeesService,
  type Employee,
} from "@/services/employees.service";
import {
  workspaceMembersService,
} from "@/services/workspace-members.service";
import {
  workspaceInvitationsService,
} from "@/services/workspace-invitations.service";
import {
  departmentsService,
  type Department,
} from "@/services/departments.service";
import {
  teamsService,
  type Team,
} from "@/services/teams.service";
import {
  workspaceRolesService,
} from "@/services/workspace-roles.service";
import type {
  WorkspaceMemberPublic,
} from "@/types/workspace-members";
import type {
  WorkspaceRolePublic,
} from "@/types/workspace-roles";

interface Props {
  employees: Employee[];
  onCancel: () => void;
  onCreated: () => Promise<void>;
}

type Mode = "existing" | "new";

type FormData = {
  memberUserId: string;
  employeeCode: string;
  firstName: string;
  lastName: string;
  workEmail: string;
  phoneNumber: string;
  jobTitle: string;
  departmentId: string;
  teamId: string;
  managerId: string;
  roleKey: string;
  invite: boolean;
};

const EMPTY: FormData = {
  memberUserId: "",
  employeeCode: "",
  firstName: "",
  lastName: "",
  workEmail: "",
  phoneNumber: "",
  jobTitle: "",
  departmentId: "",
  teamId: "",
  managerId: "",
  roleKey: "member",
  invite: true,
};

function nameOf(employee: Employee): string {
  return (
    employee.full_name?.trim() ||
    `${employee.first_name} ${employee.last_name}`.trim() ||
    employee.employee_code
  );
}

export function EmployeeCreateForm({
  employees,
  onCancel,
  onCreated,
}: Props) {
  const { workspaceId } = useWorkspace();

  const [mode, setMode] = useState<Mode>("existing");
  const [form, setForm] = useState<FormData>(EMPTY);

  const [members, setMembers] = useState<
    WorkspaceMemberPublic[]
  >([]);
  const [departments, setDepartments] = useState<
    Department[]
  >([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [roles, setRoles] = useState<
    WorkspaceRolePublic[]
  >([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [success, setSuccess] = useState("");
  const [membersError, setMembersError] = useState("");
  const [createdEmployee, setCreatedEmployee] =
    useState<Employee | null>(null);

  function update<K extends keyof FormData>(
    key: K,
    value: FormData[K]
  ) {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  }

  useEffect(() => {
    if (!workspaceId) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    const id = workspaceId;

    async function load() {
      setLoading(true);

      const results = await Promise.allSettled([
        workspaceMembersService.list(id),
        departmentsService.list(id),
        teamsService.list(id),
        workspaceRolesService.list(id),
      ]);

      if (cancelled) return;

      const [memberResult, departmentResult, teamResult, roleResult] =
        results;

      if (memberResult.status === "fulfilled") {
        setMembers(memberResult.value.members || []);
        setMembersError("");
      } else {
        setMembers([]);
        setMembersError(
          "The workspace member directory could not be loaded. You can still create an employee without linking an existing account."
        );
        setMode("new");
      }

      if (departmentResult.status === "fulfilled") {
        setDepartments(
          departmentResult.value.departments || []
        );
      }

      if (teamResult.status === "fulfilled") {
        setTeams(teamResult.value.teams || []);
      }

      if (roleResult.status === "fulfilled") {
        setRoles(
          (roleResult.value.roles || []).filter(
            (role) =>
              role.is_active &&
              role.role_key !== "owner"
          )
        );
      } else {
        setWarning(
          "Workspace roles could not be loaded. Invitation options may be limited."
        );
      }

      setLoading(false);
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [workspaceId]);

  const linkedUserIds = useMemo(
    () =>
      new Set(
        employees
          .map((employee) => employee.user_id)
          .filter((id): id is string => Boolean(id))
      ),
    [employees]
  );

  const availableMembers = useMemo(
    () =>
      members
        .filter(
          (member) =>
            member.status === "active" &&
            !member.moderation?.is_banned &&
            !linkedUserIds.has(member.user_id)
        )
        .sort((a, b) =>
          (a.username || a.email).localeCompare(
            b.username || b.email
          )
        ),
    [members, linkedUserIds]
  );

  const selectedMember = members.find(
    (member) => member.user_id === form.memberUserId
  );

  const filteredTeams = teams.filter(
    (team) =>
      !form.departmentId ||
      !team.department_id ||
      team.department_id === form.departmentId
  );

  const managers = employees.filter(
    (employee) => employee.is_active
  );

  function chooseMember(userId: string) {
    const member = availableMembers.find(
      (item) => item.user_id === userId
    );

    if (!member) {
      update("memberUserId", "");
      return;
    }

    const parts = (member.username || "")
      .trim()
      .split(/\s+/)
      .filter(Boolean);

    const firstName = parts[0] || "";
    const lastName = parts.slice(1).join(" ");

    setForm((current) => ({
      ...current,
      memberUserId: member.user_id,
      firstName: current.firstName || firstName,
      lastName: current.lastName || lastName,
      workEmail: member.email || current.workEmail,
      roleKey: member.role_key || "member",
      invite: false,
    }));

    setError("");
  }

  function switchMode(next: Mode) {
    setMode(next);
    setForm(EMPTY);
    setError("");
    setWarning("");
    setSuccess("");
  }

  async function sendInvitation(employee: Employee) {
    if (!workspaceId) {
      throw new Error("Workspace unavailable.");
    }

    const email = employee.work_email?.trim();

    if (!email) {
      throw new Error(
        "A work email is required to send an invitation."
      );
    }

    await workspaceInvitationsService.create(
      workspaceId,
      {
        email,
        employee_id: employee.id,
        role_key: form.roleKey || "member",
        department_id: employee.department_id,
        team_id: employee.team_id,
        manager_membership_id: null,
        expires_at: null,
      }
    );
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!workspaceId || saving || createdEmployee) {
      return;
    }

    setError("");
    setWarning("");
    setSuccess("");

    const employeeCode = form.employeeCode.trim();
    const firstName = form.firstName.trim();
    const lastName = form.lastName.trim();
    const email = form.workEmail.trim();

    if (!employeeCode || !firstName || !lastName) {
      setError(
        "Employee code, first name, and last name are required."
      );
      return;
    }

    if (
      employees.some(
        (employee) =>
          employee.employee_code.toLowerCase() ===
          employeeCode.toLowerCase()
      )
    ) {
      setError(
        "An employee with this employee code already exists."
      );
      return;
    }

    if (mode === "existing") {
      if (
        !selectedMember ||
        !availableMembers.some(
          (member) =>
            member.user_id === selectedMember.user_id
        )
      ) {
        setError(
          "Select an unlinked active workspace member."
        );
        return;
      }
    } else if (form.invite && !email) {
      setError(
        "Enter a work email to send an invitation."
      );
      return;
    }

    setSaving(true);

    try {
      const result = await employeesService.create(
        workspaceId,
        {
          user_id:
            mode === "existing"
              ? selectedMember!.user_id
              : null,
          employee_code: employeeCode,
          first_name: firstName,
          last_name: lastName,
          work_email: email || null,
          phone_number:
            form.phoneNumber.trim() || null,
          job_title: form.jobTitle.trim() || null,
          employment_status: "active",
          department_id: form.departmentId || null,
          team_id: form.teamId || null,
          manager_id: form.managerId || null,
        }
      );

      const employee = result.employee;
      setCreatedEmployee(employee);

      try {
        await onCreated();
      } catch {
        setWarning(
          "Employee was created, but the directory did not refresh. Refresh the Employees page."
        );
      }

      if (mode === "existing") {
        setSuccess(
          "Employee created and linked to the existing workspace member."
        );
      } else if (form.invite) {
        try {
          await sendInvitation(employee);
          setSuccess(
            "Employee created and workspace invitation requested."
          );
        } catch (cause) {
          setWarning(
            `Employee created, but invitation failed: ${
              cause instanceof Error
                ? cause.message
                : "Unknown error"
            }`
          );
          setSuccess(
            "The employee record was saved successfully."
          );
        }
      } else {
        setSuccess("Employee created successfully.");
      }
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not create employee."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      className="ec-form"
      onSubmit={(event) => void submit(event)}
    >
      <div className="ec-content">
        {error && (
          <div className="ec-alert ec-error" role="alert">
            <AlertTriangle size={17} />
            {error}
          </div>
        )}

        {membersError && (
          <div className="ec-alert ec-warning">
            <AlertTriangle size={17} />
            {membersError}
          </div>
        )}

        {warning && (
          <div className="ec-alert ec-warning">
            <AlertTriangle size={17} />
            {warning}
          </div>
        )}

        {success && (
          <div className="ec-alert ec-success" role="status">
            <CheckCircle2 size={17} />
            {success}
          </div>
        )}

        <div className="ec-section-head">
          <div>
            <h3>Workspace employee</h3>
            <p>
              Link an existing member or create a new
              employee record.
            </p>
          </div>
        </div>

        <div className="ec-mode-tabs">
          <button
            type="button"
            className={
              mode === "existing" ? "ec-selected" : ""
            }
            disabled={saving || Boolean(createdEmployee)}
            onClick={() => switchMode("existing")}
          >
            <Link2 size={16} />
            Existing member
          </button>

          <button
            type="button"
            className={
              mode === "new" ? "ec-selected" : ""
            }
            disabled={saving || Boolean(createdEmployee)}
            onClick={() => switchMode("new")}
          >
            <UserPlus size={16} />
            New employee
          </button>
        </div>

        {mode === "existing" && (
          <div className="ec-member-box">
            <label className="ec-field">
              <span>Active workspace member</span>
              <select
                value={form.memberUserId}
                disabled={
                  loading ||
                  saving ||
                  Boolean(createdEmployee)
                }
                onChange={(event) =>
                  chooseMember(event.target.value)
                }
                required
              >
                <option value="">
                  Select a member to link
                </option>
                {availableMembers.map((member) => (
                  <option
                    key={member.membership_id}
                    value={member.user_id}
                  >
                    {member.username || member.email}
                    {" — "}
                    {member.email}
                    {" ("}
                    {member.role_key}
                    {")"}
                  </option>
                ))}
              </select>
            </label>

            <p>
              <Users size={15} />
              {availableMembers.length} unlinked active
              workspace member(s). Already-linked members
              are excluded.
            </p>

            {selectedMember && (
              <div className="ec-linked-preview">
                <CheckCircle2 size={17} />
                <span>
                  This employee will be linked to{" "}
                  <strong>
                    {selectedMember.email ||
                      selectedMember.username}
                  </strong>
                  . Their existing workspace role{" "}
                  <strong>
                    {selectedMember.role_key}
                  </strong>{" "}
                  will not change.
                </span>
              </div>
            )}
          </div>
        )}

        <div className="ec-section-head">
          <div>
            <h3>Employee details</h3>
            <p>
              These details will be saved in the employee
              directory.
            </p>
          </div>
        </div>

        <div className="ec-grid">
          <Field
            label="Employee code"
            value={form.employeeCode}
            onChange={(value) =>
              update("employeeCode", value)
            }
            disabled={Boolean(createdEmployee) || saving}
            required
            placeholder="EMP-001"
          />

          <Field
            label="Job title"
            value={form.jobTitle}
            onChange={(value) =>
              update("jobTitle", value)
            }
            disabled={Boolean(createdEmployee) || saving}
            placeholder="Software Engineer"
          />

          <Field
            label="First name"
            value={form.firstName}
            onChange={(value) =>
              update("firstName", value)
            }
            disabled={Boolean(createdEmployee) || saving}
            required
          />

          <Field
            label="Last name"
            value={form.lastName}
            onChange={(value) =>
              update("lastName", value)
            }
            disabled={Boolean(createdEmployee) || saving}
            required
          />

          <Field
            label="Work email"
            type="email"
            value={form.workEmail}
            onChange={(value) =>
              update("workEmail", value)
            }
            disabled={Boolean(createdEmployee) || saving}
            required={mode === "new" && form.invite}
            placeholder="employee@company.com"
          />

          <Field
            label="Phone number"
            type="tel"
            value={form.phoneNumber}
            onChange={(value) =>
              update("phoneNumber", value)
            }
            disabled={Boolean(createdEmployee) || saving}
          />
        </div>

        <div className="ec-section-head">
          <div>
            <h3>Organization assignment</h3>
            <p>
              Assign department, team, and reporting manager.
            </p>
          </div>
        </div>

        <div className="ec-grid">
          <label className="ec-field">
            <span>Department</span>
            <select
              value={form.departmentId}
              disabled={Boolean(createdEmployee) || saving}
              onChange={(event) => {
                update("departmentId", event.target.value);
                update("teamId", "");
              }}
            >
              <option value="">No department</option>
              {departments.map((department) => (
                <option
                  key={department.id}
                  value={department.id}
                >
                  {department.name}
                </option>
              ))}
            </select>
          </label>

          <label className="ec-field">
            <span>Team</span>
            <select
              value={form.teamId}
              disabled={Boolean(createdEmployee) || saving}
              onChange={(event) =>
                update("teamId", event.target.value)
              }
            >
              <option value="">No team</option>
              {filteredTeams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </label>

          <label className="ec-field">
            <span>Manager</span>
            <select
              value={form.managerId}
              disabled={Boolean(createdEmployee) || saving}
              onChange={(event) =>
                update("managerId", event.target.value)
              }
            >
              <option value="">No manager</option>
              {managers.map((manager) => (
                <option key={manager.id} value={manager.id}>
                  {nameOf(manager)}
                </option>
              ))}
            </select>
          </label>

          {mode === "new" ? (
            <label className="ec-field">
              <span>Invitation workspace role</span>
              <select
                value={form.roleKey}
                disabled={Boolean(createdEmployee) || saving}
                onChange={(event) =>
                  update("roleKey", event.target.value)
                }
              >
                {roles.length === 0 && (
                  <option value="member">Member</option>
                )}
                {roles.map((role) => (
                  <option
                    key={role.role_key}
                    value={role.role_key}
                  >
                    {role.display_name}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <div className="ec-field">
              <span>Existing member role</span>
              <div className="ec-readonly">
                {selectedMember?.role_key || "Select a member"}
              </div>
            </div>
          )}
        </div>

        {mode === "new" && (
          <label className="ec-invite">
            <input
              type="checkbox"
              checked={form.invite}
              disabled={Boolean(createdEmployee) || saving}
              onChange={(event) =>
                update("invite", event.target.checked)
              }
            />
            <span>
              <strong>
                <Mail size={15} />
                Invite to workspace
              </strong>
              <small>
                Create the employee first, then request a
                workspace invitation with the selected role.
              </small>
            </span>
          </label>
        )}

        <div className="ec-setup-note">
          <Link2 size={18} />
          <div>
            <strong>Device assignment comes next</strong>
            <p>
              After creating this employee, open
              Organization → Device Assignments to connect
              an enrolled computer. Linking a user account
              does not automatically start the desktop
              monitoring agent or screen sharing.
            </p>
          </div>
        </div>
      </div>

      <footer className="ec-footer">
        <span className="ec-footer-status">
          {loading
            ? "Loading workspace options..."
            : createdEmployee
              ? "Employee saved"
              : "Employee creation"}
        </span>

        <div>
          <button
            type="button"
            className="ec-button ec-secondary"
            onClick={onCancel}
          >
            {createdEmployee ? "Close" : "Cancel"}
          </button>

          {!createdEmployee && (
            <button
              type="submit"
              className="ec-button ec-primary"
              disabled={
                loading ||
                saving ||
                !workspaceId ||
                (mode === "existing" &&
                  !form.memberUserId)
              }
            >
              {saving ? (
                <Loader2
                  size={16}
                  className="ec-spin"
                />
              ) : (
                <UserPlus size={16} />
              )}
              {saving
                ? "Creating..."
                : mode === "existing"
                  ? "Create & link member"
                  : form.invite
                    ? "Create & invite"
                    : "Create employee"}
            </button>
          )}
        </div>
      </footer>

      <style jsx global>{`
        .ec-form {
          display: flex;
          flex-direction: column;
          min-height: 100%;
          background: #fbf9f5;
          color: #17213a;
          font-size: 13px;
          box-sizing: border-box;
        }

        .ec-form * {
          box-sizing: border-box;
        }

        .ec-content {
          flex: 1;
          padding: 22px 25px 32px;
        }

        .ec-section-head {
          margin: 17px 0 13px;
        }

        .ec-section-head:first-child {
          margin-top: 0;
        }

        .ec-section-head h3 {
          margin: 0;
          font-size: 15px;
          font-weight: 750;
        }

        .ec-section-head p {
          color: #7c8798;
          font-size: 12px;
          margin: 5px 0 0;
          line-height: 1.5;
        }

        .ec-mode-tabs {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 9px;
          margin: 12px 0 18px;
        }

        .ec-mode-tabs button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 12px;
          border-radius: 8px;
          border: 1px solid #e4e0d9;
          background: white;
          color: #60708b;
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
        }

        .ec-mode-tabs button.ec-selected {
          border-color: #e8c881;
          background: #fff5de;
          color: #192538;
        }

        .ec-member-box {
          background: #fffdf7;
          border: 1px solid #eee4d2;
          border-radius: 10px;
          padding: 15px;
        }

        .ec-member-box > p {
          margin: 11px 0 0;
          display: flex;
          align-items: center;
          gap: 8px;
          color: #748298;
          font-size: 11px;
        }

        .ec-linked-preview {
          margin-top: 13px;
          display: flex;
          align-items: flex-start;
          gap: 9px;
          background: #eaf8ef;
          color: #246b44;
          border-radius: 7px;
          padding: 11px;
          font-size: 12px;
          line-height: 1.6;
        }

        .ec-linked-preview svg {
          flex-shrink: 0;
          margin-top: 1px;
        }

        .ec-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 15px;
        }

        .ec-field {
          display: flex;
          min-width: 0;
          flex-direction: column;
          gap: 7px;
          font-size: 12px;
          font-weight: 650;
          color: #414d61;
        }

        .ec-field input,
        .ec-field select,
        .ec-readonly {
          display: block;
          width: 100%;
          min-width: 0;
          height: 42px;
          padding: 0 12px;
          border: 1px solid #e2dfd8;
          border-radius: 8px;
          background: white;
          color: #19253c;
          outline: none;
          font: inherit;
          font-weight: 450;
        }

        .ec-field input:focus,
        .ec-field select:focus {
          border-color: #deb14f;
          box-shadow: 0 0 0 3px #f5e5bc80;
        }

        .ec-readonly {
          display: flex;
          align-items: center;
          background: #f3f1ed;
          color: #647087;
        }

        .ec-invite {
          margin-top: 21px;
          display: flex;
          align-items: flex-start;
          gap: 11px;
          padding: 14px;
          border: 1px solid #e6e1d8;
          border-radius: 9px;
          background: #fffefa;
          cursor: pointer;
        }

        .ec-invite > input {
          accent-color: #232c37;
          margin-top: 3px;
        }

        .ec-invite > span {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .ec-invite strong {
          display: flex;
          align-items: center;
          gap: 7px;
        }

        .ec-invite small {
          color: #77849a;
          line-height: 1.5;
        }

        .ec-setup-note {
          margin-top: 19px;
          display: flex;
          align-items: flex-start;
          gap: 11px;
          padding: 15px;
          border-radius: 9px;
          border: 1px solid #dce6f5;
          background: #f0f5fd;
          color: #315074;
        }

        .ec-setup-note svg {
          flex-shrink: 0;
        }

        .ec-setup-note p {
          font-size: 12px;
          line-height: 1.6;
          margin: 5px 0 0;
        }

        .ec-alert {
          display: flex;
          align-items: flex-start;
          gap: 9px;
          padding: 12px;
          margin-bottom: 13px;
          border-radius: 8px;
          line-height: 1.55;
        }

        .ec-alert svg {
          flex-shrink: 0;
        }

        .ec-error {
          color: #b32a31;
          background: #fff0f0;
          border: 1px solid #edc6c7;
        }

        .ec-warning {
          color: #956600;
          background: #fff7e7;
          border: 1px solid #f0dcad;
        }

        .ec-success {
          color: #217b4c;
          background: #eef9f0;
          border: 1px solid #cce8d5;
        }

        .ec-footer {
          position: sticky;
          bottom: 0;
          z-index: 2;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 16px 24px;
          border-top: 1px solid #e5e0d9;
          background: #fffefa;
        }

        .ec-footer-status {
          color: #8893a3;
          font-size: 11px;
        }

        .ec-footer > div {
          display: flex;
          align-items: center;
          gap: 9px;
          margin-left: auto;
        }

        .ec-button {
          height: 39px;
          display: inline-flex;
          justify-content: center;
          align-items: center;
          gap: 8px;
          border-radius: 7px;
          padding: 0 13px;
          white-space: nowrap;
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
        }

        .ec-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .ec-secondary {
          color: #263349;
          background: #fff;
          border: 1px solid #e0ddd7;
        }

        .ec-primary {
          color: #fff;
          background: #242a32;
          border: 1px solid #242a32;
        }

        .ec-spin {
          animation: ec-spin 1s linear infinite;
        }

        @keyframes ec-spin {
          to {
            transform: rotate(360deg);
          }
        }

        @media (max-width: 620px) {
          .ec-content {
            padding: 18px 15px 25px;
          }

          .ec-grid {
            grid-template-columns: 1fr;
          }

          .ec-footer {
            flex-wrap: wrap;
            padding: 13px 15px;
          }

          .ec-footer-status {
            display: none;
          }

          .ec-footer > div {
            width: 100%;
          }

          .ec-button {
            flex: 1;
          }
        }
      `}</style>
    </form>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  disabled,
  required,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
}) {
  return (
    <label className="ec-field">
      <span>
        {label}
        {required ? " *" : ""}
      </span>

      <input
        type={type}
        value={value}
        required={required}
        placeholder={placeholder}
        disabled={disabled}
        onChange={(event) =>
          onChange(event.target.value)
        }
      />
    </label>
  );
}
