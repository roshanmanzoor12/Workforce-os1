
"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Laptop2,
  Link2,
  Monitor,
  RefreshCw,
  Search,
  ShieldCheck,
  Unplug,
  UserRound,
  Users,
  Wifi,
  WifiOff,
  X,
} from "lucide-react";
import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";
import {
  devicesService,
  type Device,
} from "@/services/devices.service";
import {
  employeesService,
  type Employee,
} from "@/services/employees.service";
import { workspaceMembersService } from "@/services/workspace-members.service";
import type { WorkspaceMemberPublic } from "@/types/workspace-members";
import { api } from "@/lib/api/client";

type ReadinessDevice = {
  device_id: string;
  employee_id: string | null;
  device_name: string;
  platform: string;
  status: string;
  is_online: boolean;
  monitoring_ready: boolean;
  live_ready: boolean;
  last_seen_at: string | null;
};

type ReadinessResponse = {
  devices?: ReadinessDevice[];
};

type Filter = "all" | "assigned" | "unassigned" | "offline";
type View = "devices" | "employees";
type Feedback = { message: string; error: boolean } | null;

const PAGE_SIZE = 9;

function employeeName(employee: Employee): string {
  return (
    employee.full_name?.trim() ||
    `${employee.first_name} ${employee.last_name}`.trim() ||
    employee.employee_code ||
    "Unnamed employee"
  );
}

function initials(value: string): string {
  return (
    value
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() || "")
      .join("") || "?"
  );
}

function lastSeen(value: string | null): string {
  if (!value) return "Never";

  const time = new Date(value).getTime();
  if (!Number.isFinite(time)) return "Unknown";

  const minutes = Math.max(
    0,
    Math.floor((Date.now() - time) / 60000)
  );

  if (minutes === 0) return "Just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (minutes < 1440) {
    return `${Math.floor(minutes / 60)}h ago`;
  }

  return new Date(time).toLocaleDateString();
}

function readableStatus(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (c) =>
    c.toUpperCase()
  );
}

function statusClass(status: string): string {
  if (status === "active" || status === "online") {
    return "ed-good";
  }
  if (status === "pending") return "ed-pending";
  if (status === "revoked" || status === "disabled") {
    return "ed-bad";
  }
  return "ed-offline";
}

export default function DevicesPage() {
  const {
    workspaceId,
    workspace,
    user,
    membership,
    navigationView,
    effectiveNavigationView,
    effectivePermissions,
    workspaceEntitlements,
    loading: contextLoading,
  } = useWorkspace();

  // Real role controls mutations. Preview never grants writes.
  const realRole = membership?.role_key?.toLowerCase() || "";
  const canAssign =
    realRole === "owner" || realRole === "admin";

  const isClient = navigationView === "client";
  const isMember = navigationView === "member";
  const isManager = navigationView === "manager";

  const canSeeOwnReadiness = hasAnyPermission(
    effectivePermissions,
    [
      "devices.self.read",
      "devices.team.read",
      "devices.all.read",
      "monitoring.self.read",
      "monitoring.team.read",
      "monitoring.all.read",
    ],
    effectiveNavigationView
  );

  const hasMonitoringPlan =
    workspaceEntitlements?.monitoring === true;

  const [devices, setDevices] = useState<Device[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  // WFOS_DEVICE_ACCOUNT_LINK_V1
  const [members, setMembers] = useState<WorkspaceMemberPublic[]>([]);
  const [readiness, setReadiness] =
    useState<ReadinessDevice[]>([]);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState<Feedback>(null);

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [view, setView] = useState<View>("devices");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(
    null
  );
  const [assignmentId, setAssignmentId] = useState("");
  const [memberUserId, setMemberUserId] = useState("");
  const [confirmUnassign, setConfirmUnassign] = useState(false);

  const canLoadManagement = Boolean(
    workspaceId && canAssign
  );
  const canLoadReadiness = Boolean(
    workspaceId &&
      !isClient &&
      hasMonitoringPlan &&
      canSeeOwnReadiness
  );

  const load = useCallback(
    async (quiet = false) => {
      if (!workspaceId || contextLoading) {
        setLoading(false);
        return;
      }

      if (quiet) setRefreshing(true);
      else setLoading(true);

      try {
        setError("");

        if (canLoadManagement) {
          const [deviceResult, employeeResult, memberResult] =
            await Promise.all([
              devicesService.list(workspaceId, {
                includeInactive: true,
              }),
              employeesService.list(workspaceId, {
                includeInactive: true,
              }),
              workspaceMembersService.list(workspaceId),
            ]);

          setDevices(deviceResult.devices ?? []);
          setEmployees(employeeResult.employees ?? []);
          setMembers(memberResult.members ?? []);
        } else {
          setDevices([]);
          setEmployees([]);
          setMembers([]);
        }

        if (canLoadReadiness) {
          try {
            const result = await api.get<ReadinessResponse>(
              `/workspaces/${workspaceId}/devices/readiness`
            );

            setReadiness(result.devices ?? []);
          } catch (cause) {
            setReadiness([]);
            if (!canLoadManagement) {
              throw cause;
            }
          }
        } else {
          setReadiness([]);
        }
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load device information."
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [
      workspaceId,
      contextLoading,
      canLoadManagement,
      canLoadReadiness,
    ]
  );

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!workspaceId) return;

    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void load(true);
      }
    }, 30000);

    return () => window.clearInterval(interval);
  }, [workspaceId, load]);

  const employeesById = useMemo(
    () => new Map(employees.map((item) => [item.id, item])),
    [employees]
  );

  const readinessById = useMemo(
    () =>
      new Map(
        readiness.map((item) => [item.device_id, item])
      ),
    [readiness]
  );

  const assignedCount = devices.filter(
    (item) => Boolean(item.employee_id) &&
      item.status !== "revoked"
  ).length;

  const unassignedCount = devices.filter(
    (item) => !item.employee_id &&
      item.status !== "revoked"
  ).length;

  const onlineCount = readiness.filter(
    (item) => item.is_online
  ).length;

  const filteredDevices = useMemo(() => {
    const needle = search.toLowerCase().trim();

    return devices.filter((device) => {
      const employee = device.employee_id
        ? employeesById.get(device.employee_id)
        : undefined;

      const text = [
        device.hostname,
        device.device_uuid,
        device.os_name,
        device.status,
        employee ? employeeName(employee) : "",
      ]
        .join(" ")
        .toLowerCase();

      const matchesText = !needle || text.includes(needle);
      const matchesFilter =
        filter === "all" ||
        (filter === "assigned" && Boolean(device.employee_id)) ||
        (filter === "unassigned" && !device.employee_id) ||
        (filter === "offline" &&
          (device.status === "offline" ||
            readinessById.get(device.id)?.is_online === false));

      return matchesText && matchesFilter;
    });
  }, [devices, employeesById, search, filter, readinessById]);

  const filteredEmployees = useMemo(() => {
    const needle = search.toLowerCase().trim();

    return employees.filter((employee) =>
      [
        employeeName(employee),
        employee.employee_code,
        employee.job_title,
        employee.work_email,
      ]
        .join(" ")
        .toLowerCase()
        .includes(needle)
    );
  }, [employees, search]);

  const totalItems =
    view === "devices"
      ? filteredDevices.length
      : filteredEmployees.length;

  const totalPages = Math.max(
    1,
    Math.ceil(totalItems / PAGE_SIZE)
  );
  const currentPage = Math.min(page, totalPages);

  const visibleDevices = filteredDevices.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const visibleEmployees = filteredEmployees.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const selected = devices.find(
    (item) => item.id === selectedId
  ) || null;

  const selectedEmployee = selected?.employee_id
    ? employeesById.get(selected.employee_id)
    : undefined;

  const targetEmployee = employees.find((e) => e.id === assignmentId);
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

  const selectedReadiness = selected
    ? readinessById.get(selected.id)
    : undefined;

  async function saveAssignment() {
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

  function selectDevice(device: Device) {
    setSelectedId(device.id);
    setAssignmentId(device.employee_id || "");
    setMemberUserId(employees.find((e) => e.id === device.employee_id)?.user_id || "");
    setFeedback(null);
    setConfirmUnassign(false);
  }

  const roleDescription = isClient
    ? "Client workspace access"
    : isMember
      ? "Employee self-service"
      : isManager
        ? "Manager monitoring"
        : canAssign
          ? "Workspace device administration"
          : "Permission-scoped device access";

  const workspaceLabel =
    workspace?.workspace_type === "agency"
      ? "Agency"
      : "Company";

  return (
    <WorkspaceRequired>
      <main className="ed-page">
        <header className="ed-header">
          <div>
            <div className="ed-breadcrumb">
              Workspace <ChevronRight size={13} />
              {workspaceLabel} <ChevronRight size={13} />
              Devices
            </div>
            <h1>
              {canAssign
                ? "Employee & Device Assignment"
                : isMember
                  ? "My Monitoring Devices"
                  : "Device Monitoring"}
            </h1>
            <p>
              {canAssign
                ? "Connect registered computers to employees and manage monitoring readiness."
                : "View monitoring information permitted for your workspace role."}
            </p>
          </div>

          <div className="ed-header-actions">
            <span className="ed-role">
              <ShieldCheck size={15} />
              {roleDescription}
            </span>
            <button
              className="ed-button"
              type="button"
              disabled={refreshing || contextLoading}
              onClick={() => void load(true)}
            >
              <RefreshCw
                size={16}
                className={refreshing ? "ed-spin" : ""}
              />
              Refresh
            </button>
          </div>
        </header>

        {error && (
          <div className="ed-notice ed-error">
            <AlertTriangle size={17} />
            <span>{error}</span>
            <button type="button" onClick={() => void load()}>
              Retry
            </button>
          </div>
        )}

        {canAssign ? (
          <>
            <section className="ed-metrics">
              <Metric icon={<Laptop2 size={23} />}
                label="Registered devices"
                value={String(devices.length)}
                description="Workspace inventory" />
              <Metric icon={<Link2 size={23} />}
                label="Assigned devices"
                value={String(assignedCount)}
                description="Linked to employees" />
              <Metric icon={<Unplug size={23} />}
                label="Unassigned"
                value={String(unassignedCount)}
                description="Need employee assignment" />
              <Metric icon={<Wifi size={23} />}
                label="Online"
                value={canLoadReadiness ? String(onlineCount) : "—"}
                description="Based on authorized readiness" />
            </section>

            <section className="ed-workspace-grid">
              <div className="ed-card">
                <div className="ed-toolbar">
                  <div className="ed-tabs">
                    <button
                      className={view === "devices" ? "ed-active" : ""}
                      type="button"
                      onClick={() => {
                        setView("devices");
                        setPage(1);
                      }}
                    >
                      <Laptop2 size={16} />
                      Devices
                    </button>
                    <button
                      className={view === "employees" ? "ed-active" : ""}
                      type="button"
                      onClick={() => {
                        setView("employees");
                        setPage(1);
                      }}
                    >
                      <Users size={16} />
                      Employees
                    </button>
                  </div>
                  <span className="ed-muted">
                    {totalItems} records
                  </span>
                </div>

                <div className="ed-searchbar">
                  <label className="ed-search">
                    <Search size={16} />
                    <input
                      type="search"
                      value={search}
                      onChange={(event) => {
                        setSearch(event.target.value);
                        setPage(1);
                      }}
                      placeholder={
                        view === "devices"
                          ? "Search devices or employees..."
                          : "Search employee directory..."
                      }
                    />
                  </label>

                  {view === "devices" && (
                    <select
                      value={filter}
                      aria-label="Device assignment filter"
                      onChange={(event) => {
                        setFilter(event.target.value as Filter);
                        setPage(1);
                      }}
                    >
                      <option value="all">All devices</option>
                      <option value="assigned">Assigned</option>
                      <option value="unassigned">Unassigned</option>
                      <option value="offline">Offline</option>
                    </select>
                  )}

                  <button
                    type="button"
                    className="ed-reset"
                    onClick={() => {
                      setSearch("");
                      setFilter("all");
                      setPage(1);
                    }}
                  >
                    Clear filters
                  </button>
                </div>

                <div className="ed-table-scroll">
                  {view === "devices" ? (
                    <table>
                      <thead>
                        <tr>
                          <th>Device</th>
                          <th>Assigned employee</th>
                          <th>Status</th>
                          <th>Last seen</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {visibleDevices.map((device) => {
                          const employee = device.employee_id
                            ? employeesById.get(device.employee_id)
                            : undefined;

                          const deviceReady = readinessById.get(
                            device.id
                          );

                          return (
                            <tr
                              key={device.id}
                              className={
                                selectedId === device.id
                                  ? "ed-selected-row"
                                  : ""
                              }
                            >
                              <td>
                                <div className="ed-device-cell">
                                  <span className="ed-device-icon">
                                    <Monitor size={18} />
                                  </span>
                                  <div>
                                    <strong>{device.hostname}</strong>
                                    <small>
                                      {device.os_name}
                                      {device.os_version
                                        ? ` ${device.os_version}`
                                        : ""}
                                    </small>
                                  </div>
                                </div>
                              </td>
                              <td>
                                {employee ? (
                                  <span className="ed-employee">
                                    <span className="ed-avatar">
                                      {initials(employeeName(employee))}
                                    </span>
                                    {employeeName(employee)}
                                  </span>
                                ) : device.employee_id ? (
                                  <span className="ed-muted">
                                    Assigned employee unavailable
                                  </span>
                                ) : (
                                  <span className="ed-unassigned">
                                    Not assigned
                                  </span>
                                )}
                              </td>
                              <td>
                                <span className={`ed-status ${statusClass(
                                  deviceReady
                                    ? deviceReady.is_online
                                      ? "online"
                                      : device.status
                                    : device.status
                                )}`}>
                                  <i />
                                  {deviceReady
                                    ? deviceReady.is_online
                                      ? "Online"
                                      : readableStatus(device.status)
                                    : readableStatus(device.status)}
                                </span>
                              </td>
                              <td className="ed-muted">
                                {lastSeen(device.last_seen_at)}
                              </td>
                              <td>
                                <button
                                  type="button"
                                  className="ed-action"
                                  onClick={() => selectDevice(device)}
                                >
                                  Assign
                                  <ArrowRight size={14} />
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  ) : (
                    <table>
                      <thead>
                        <tr>
                          <th>Employee</th>
                          <th>Role / position</th>
                          <th>Assigned devices</th>
                          <th>Account</th>
                        </tr>
                      </thead>
                      <tbody>
                        {visibleEmployees.map((employee) => {
                          const linked = devices.filter(
                            (item) =>
                              item.employee_id === employee.id &&
                              item.status !== "revoked"
                          );

                          return (
                            <tr key={employee.id}>
                              <td>
                                <div className="ed-employee-cell">
                                  <span className="ed-avatar">
                                    {initials(employeeName(employee))}
                                  </span>
                                  <div>
                                    <strong>
                                      {employeeName(employee)}
                                    </strong>
                                    <small>
                                      {employee.employee_code}
                                    </small>
                                  </div>
                                </div>
                              </td>
                              <td>
                                {employee.job_title || "—"}
                              </td>
                              <td>
                                <strong>{linked.length}</strong>
                                <small className="ed-device-list">
                                  {linked.length
                                    ? linked.map((device) => device.hostname)
                                        .join(", ")
                                    : "No device assigned"}
                                </small>
                              </td>
                              <td>
                                <span className="ed-status ed-neutral">
                                  <i />
                                  {employee.user_id
                                    ? "Linked user"
                                    : "No linked user"}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  )}

                  {!loading && totalItems === 0 && (
                    <div className="ed-empty">
                      <Laptop2 size={32} />
                      <strong>
                        {view === "devices"
                          ? "No matching registered devices"
                          : "No matching employee records"}
                      </strong>
                      <p>
                        {view === "devices"
                          ? "Enroll the desktop agent in this workspace before assigning its device."
                          : "Employees must exist in this workspace before a device can be assigned."}
                      </p>
                    </div>
                  )}

                  {loading && (
                    <div className="ed-empty">
                      <RefreshCw size={25} className="ed-spin" />
                      Loading workspace records...
                    </div>
                  )}
                </div>

                <footer className="ed-pagination">
                  <span>
                    Showing {totalItems
                      ? (currentPage - 1) * PAGE_SIZE + 1
                      : 0}
                    –{Math.min(currentPage * PAGE_SIZE, totalItems)}
                    {" "}of {totalItems}
                  </span>
                  <div>
                    <button
                      type="button"
                      disabled={currentPage <= 1}
                      onClick={() =>
                        setPage((p) => Math.max(1, p - 1))
                      }
                    >
                      <ChevronLeft size={17} />
                    </button>
                    <span>
                      {currentPage} / {totalPages}
                    </span>
                    <button
                      type="button"
                      disabled={currentPage >= totalPages}
                      onClick={() =>
                        setPage((p) => Math.min(totalPages, p + 1))
                      }
                    >
                      <ChevronRight size={17} />
                    </button>
                  </div>
                </footer>
              </div>

              <aside className="ed-side">
                <div className="ed-card ed-assignment-card">
                  <div className="ed-side-heading">
                    <h2>
                      <Link2 size={19} />
                      Device assignment
                    </h2>
                    {selected && (
                      <button
                        type="button"
                        aria-label="Close selection"
                        onClick={() => {
                          setSelectedId(null);
                          setFeedback(null);
                        }}
                      >
                        <X size={17} />
                      </button>
                    )}
                  </div>

                  {selected ? (
                    <div className="ed-side-content">
                      <div className="ed-selected-device">
                        <span>
                          <Laptop2 size={27} />
                        </span>
                        <div>
                          <strong>{selected.hostname}</strong>
                          <small>
                            {selected.os_name} ·{" "}
                            {selected.agent_version
                              ? `Agent ${selected.agent_version}`
                              : "Agent version unavailable"}
                          </small>
                        </div>
                      </div>

                      <dl className="ed-details">
                        <div>
                          <dt>Device status</dt>
                          <dd>
                            {readableStatus(selected.status)}
                          </dd>
                        </div>
                        <div>
                          <dt>Last heartbeat</dt>
                          <dd>
                            {lastSeen(selected.last_seen_at)}
                          </dd>
                        </div>
                        <div>
                          <dt>Live ready</dt>
                          <dd>
                            {selectedReadiness
                              ? selectedReadiness.live_ready
                                ? "Yes"
                                : "No"
                              : "Not verified"}
                          </dd>
                        </div>
                        <div>
                          <dt>Employee assignment</dt>
                          <dd>
                            {selectedEmployee
                              ? employeeName(selectedEmployee)
                              : selected.employee_id
                                ? "Employee unavailable"
                                : "Unassigned"}
                          </dd>
                        </div>
                      </dl>

                      <label className="ed-field">
                        Assign to employee
                        <select
                          value={assignmentId}
                          onChange={(event) => {
                            setAssignmentId(event.target.value);
                            setMemberUserId(employees.find((e) => e.id === event.target.value)?.user_id || "");
                            setConfirmUnassign(false);
                          }}
                        >
                          <option value="">
                            No employee / Unassign
                          </option>
                          {employees
                            .filter((employee) => employee.is_active)
                            .map((employee) => (
                              <option
                                key={employee.id}
                                value={employee.id}
                              >
                                {employeeName(employee)}
                                {" "}· {employee.employee_code}
                              </option>
                            ))}
                        </select>
                      </label>

                      {targetEmployee && (
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

                      {assignmentId === "" &&
                        Boolean(selected.employee_id) &&
                        !confirmUnassign && (
                          <button
                            type="button"
                            className="ed-button ed-warning"
                            onClick={() => setConfirmUnassign(true)}
                          >
                            <Unplug size={16} />
                            Confirm unassignment
                          </button>
                        )}

                      {confirmUnassign && (
                        <div className="ed-confirm">
                          <AlertTriangle size={17} />
                          This will remove the employee
                          association without revoking the device.
                        </div>
                      )}

                      <button
                        type="button"
                        className="ed-button ed-primary ed-full"
                        disabled={
                          busy ||
                          (!assignmentChanged && !accountChanged) ||
                          (Boolean(assignmentId) && !memberUserId && !targetEmployee?.user_id) ||
                          (assignmentId === "" &&
                            Boolean(selected.employee_id) &&
                            !confirmUnassign)
                        }
                        onClick={() => void saveAssignment()}
                      >
                        {busy ? (
                          <RefreshCw
                            size={16}
                            className="ed-spin"
                          />
                        ) : (
                          <Check size={16} />
                        )}
                        {accountChanged ? "Save assignment & link account" : "Save assignment"}
                      </button>

                      {feedback && (
                        <div className={`ed-feedback ${
                          feedback.error ? "ed-error" : "ed-success"
                        }`}>
                          {feedback.message}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="ed-empty ed-side-empty">
                      <Link2 size={29} />
                      <strong>Select a device</strong>
                      <p>
                        Choose a device from the inventory
                        to assign or unassign an employee.
                      </p>
                    </div>
                  )}
                </div>

                <div className="ed-card ed-help-card">
                  <div className="ed-side-heading">
                    <h2>
                      <ShieldCheck size={19} />
                      Monitoring setup
                    </h2>
                  </div>
                  <div className="ed-help-content">
                    <div>
                      <span>1</span>
                      <p>
                        <strong>Create or link an employee</strong>
                        <small>
                          The employee record can link to a
                          workspace user account.
                        </small>
                      </p>
                    </div>
                    <div>
                      <span>2</span>
                      <p>
                        <strong>Register the computer</strong>
                        <small>
                          Use the installed authenticated
                          WorkforceOS desktop agent.
                        </small>
                      </p>
                    </div>
                    <div>
                      <span>3</span>
                      <p>
                        <strong>Assign the device</strong>
                        <small>
                          Each employee may have multiple
                          registered devices.
                        </small>
                      </p>
                    </div>
                    <div>
                      <span>4</span>
                      <p>
                        <strong>Verify readiness and consent</strong>
                        <small>
                          Live-screen requests require the
                          separate authorization flow.
                        </small>
                      </p>
                    </div>
                    <Link href="/monitoring/live-screen">
                      Open Live Screen
                      <ArrowRight size={15} />
                    </Link>
                  </div>
                </div>
              </aside>
            </section>
          </>
        ) : (
          <section className="ed-restricted">
            <div className="ed-card">
              <div className="ed-side-heading">
                <h2>
                  {isClient
                    ? <ShieldCheck size={19} />
                    : <Laptop2 size={19} />}
                  {isClient
                    ? "Client workspace"
                    : "Authorized monitoring devices"}
                </h2>
              </div>

              <div className="ed-restricted-content">
                {isClient ? (
                  <>
                    <ShieldCheck size={35} />
                    <h3>Employee monitoring is private</h3>
                    <p>
                      Client accounts cannot access internal
                      employee device inventories, monitoring,
                      screen-sharing, or employee assignments.
                    </p>
                  </>
                ) : !canLoadReadiness ? (
                  <>
                    <ShieldCheck size={35} />
                    <h3>Device visibility is not available</h3>
                    <p>
                      Your current permissions or workspace
                      monitoring entitlement do not allow a
                      scoped device-readiness view.
                    </p>
                  </>
                ) : (
                  <>
                    <div className="ed-restricted-top">
                      <div>
                        <h3>
                          {isMember
                            ? "My registered monitoring status"
                            : isManager
                              ? "Scoped team device readiness"
                              : "Authorized device readiness"}
                        </h3>
                        <p>
                          Showing only devices returned by
                          the backend's authorized readiness API.
                        </p>
                      </div>
                      <span className="ed-readiness-count">
                        {readiness.length} devices
                      </span>
                    </div>

                    {readiness.length === 0 ? (
                      <div className="ed-empty">
                        <Laptop2 size={30} />
                        <strong>No authorized devices returned</strong>
                        <p>
                          A device must be registered, linked,
                          and visible within your assigned scope.
                        </p>
                      </div>
                    ) : (
                      <div className="ed-readiness-grid">
                        {readiness.map((device) => (
                          <div
                            className="ed-readiness-item"
                            key={device.device_id}
                          >
                            <span className="ed-device-icon">
                              <Laptop2 size={21} />
                            </span>
                            <div>
                              <strong>{device.device_name}</strong>
                              <small>
                                {device.platform} ·{" "}
                                {lastSeen(device.last_seen_at)}
                              </small>
                            </div>
                            <span className={`ed-status ${
                              device.is_online
                                ? "ed-good"
                                : "ed-offline"
                            }`}>
                              {device.is_online
                                ? <Wifi size={14} />
                                : <WifiOff size={14} />}
                              {device.is_online
                                ? "Online"
                                : "Offline"}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {!isClient && (
              <div className="ed-card ed-self-note">
                <CheckCircle2 size={20} />
                <div>
                  <strong>No assignment permissions</strong>
                  <p>
                    Device assignment is limited to authorized
                    workspace owners and admins by the current
                    backend. Employee access is self-service;
                    manager access depends on backend scope.
                    A role preview cannot grant real API access.
                  </p>
                </div>
              </div>
            )}
          </section>
        )}

        <style jsx global>{`
          .ed-page {
            --ed-bg: #faf9f6;
            --ed-ink: #121b30;
            --ed-muted: #748098;
            --ed-line: #ebe7de;
            background: var(--ed-bg);
            color: var(--ed-ink);
            min-height: 100%;
            padding: 24px;
            font-size: 13px;
          }
          .ed-page * { box-sizing: border-box; }
          .ed-page button,
          .ed-page input,
          .ed-page select { font: inherit; }
          .ed-page button { cursor: pointer; }
          .ed-page button:disabled {
            opacity: .5;
            cursor: not-allowed;
          }
          .ed-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 23px;
          }
          .ed-breadcrumb {
            display: flex;
            align-items: center;
            gap: 7px;
            color: #7a8599;
            font-size: 12px;
            margin-bottom: 15px;
          }
          .ed-header h1 {
            margin: 0;
            font-size: clamp(25px, 2.6vw, 34px);
            line-height: 1.16;
            letter-spacing: -1px;
            font-weight: 760;
          }
          .ed-header p {
            margin: 10px 0 0;
            color: var(--ed-muted);
            font-size: 14px;
            line-height: 1.55;
          }
          .ed-header-actions {
            display: flex;
            align-items: center;
            gap: 9px;
            flex-wrap: wrap;
          }
          .ed-role {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            border-radius: 7px;
            background: #f1efe9;
            padding: 9px 11px;
            color: #5e6774;
            white-space: nowrap;
            font-size: 11px;
          }
          .ed-button {
            border: 1px solid #e1ddd4;
            border-radius: 8px;
            background: #fff;
            color: var(--ed-ink);
            min-height: 38px;
            padding: 0 14px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-weight: 650 !important;
          }
          .ed-button.ed-primary {
            color: white;
            background: #262522;
            border-color: #262522;
          }
          .ed-button.ed-warning {
            background: #fff7e5;
            color: #a26a00;
            border-color: #ecd5a8;
            width: 100%;
            margin-bottom: 12px;
          }
          .ed-full { width: 100%; }
          .ed-metrics {
            display: grid;
            grid-template-columns: repeat(4,minmax(0,1fr));
            gap: 13px;
            margin-bottom: 17px;
          }
          .ed-metric {
            min-height: 112px;
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 20px;
            border-radius: 13px;
            border: 1px solid #e7e0d3;
            background: #fffdf7;
          }
          .ed-metric-icon {
            flex-shrink: 0;
            width: 52px;
            height: 52px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            color: #a66d00;
            background: #ffefbf;
          }
          .ed-metric-copy {
            display: flex;
            flex-direction: column;
            gap: 5px;
            min-width: 0;
          }
          .ed-metric-copy span {
            font-weight: 650;
            font-size: 12px;
          }
          .ed-metric-copy strong {
            font-size: 28px;
            line-height: 1;
            letter-spacing: -.8px;
          }
          .ed-metric-copy small {
            color: var(--ed-muted);
            line-height: 1.3;
            font-size: 11px;
          }
          .ed-workspace-grid {
            display: grid;
            grid-template-columns: minmax(0,1.85fr) minmax(290px,.8fr);
            gap: 16px;
            align-items: start;
          }
          .ed-card {
            min-width: 0;
            border: 1px solid var(--ed-line);
            border-radius: 13px;
            background: #fffefa;
            overflow: hidden;
          }
          .ed-toolbar {
            padding: 17px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            border-bottom: 1px solid #ece8e0;
          }
          .ed-tabs {
            display: flex;
            gap: 6px;
            align-items: center;
          }
          .ed-tabs button {
            border: 0;
            background: transparent;
            border-radius: 8px;
            color: #7a8597;
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 9px 13px;
            font-weight: 650;
          }
          .ed-tabs button.ed-active {
            background: #282622;
            color: #fff;
          }
          .ed-muted { color: var(--ed-muted); }
          .ed-searchbar {
            padding: 15px 17px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
          }
          .ed-search {
            flex: 1;
            min-width: 180px;
            display: flex;
            align-items: center;
            gap: 9px;
            border: 1px solid #e8e4dd;
            border-radius: 8px;
            background: #fff;
            height: 39px;
            padding: 0 12px;
            color: #8a94a6;
          }
          .ed-search input {
            border: 0;
            outline: 0;
            width: 100%;
            min-width: 0;
            background: transparent;
            color: var(--ed-ink);
          }
          .ed-searchbar select,
          .ed-field select {
            background: white;
            color: var(--ed-ink);
            border: 1px solid #e8e4dd;
            border-radius: 8px;
            height: 39px;
            padding: 0 10px;
          }
          .ed-reset {
            background: transparent;
            border: 0;
            color: #627087;
            text-decoration: underline;
            white-space: nowrap;
          }
          .ed-table-scroll {
            overflow-x: auto;
            min-height: 310px;
          }
          .ed-table-scroll table {
            min-width: 650px;
            border-collapse: collapse;
            width: 100%;
            text-align: left;
          }
          .ed-table-scroll th {
            background: #f7f5f0;
            color: #6a7485;
            padding: 13px 14px;
            font-size: 11px;
            font-weight: 700;
            white-space: nowrap;
          }
          .ed-table-scroll td {
            padding: 13px 14px;
            border-top: 1px solid #eeeae3;
            font-size: 12px;
          }
          .ed-selected-row {
            background: #fff6dc;
          }
          .ed-device-cell,
          .ed-employee-cell,
          .ed-employee {
            display: flex;
            align-items: center;
            gap: 10px;
          }
          .ed-device-cell > div,
          .ed-employee-cell > div {
            display: flex;
            flex-direction: column;
            gap: 5px;
          }
          .ed-device-cell small,
          .ed-employee-cell small,
          .ed-device-list {
            display: block;
            color: var(--ed-muted);
            font-size: 11px;
            line-height: 1.4;
          }
          .ed-device-list {
            max-width: 210px;
            white-space: normal;
            margin-top: 5px;
          }
          .ed-device-icon {
            width: 36px;
            height: 36px;
            flex-shrink: 0;
            display: grid;
            place-items: center;
            background: #eff0f2;
            border-radius: 8px;
            color: #414e62;
          }
          .ed-avatar {
            width: 31px;
            height: 31px;
            display: inline-grid;
            place-items: center;
            flex-shrink: 0;
            border-radius: 50%;
            background: #ffe9af;
            color: #956000;
            font-size: 11px;
            font-weight: 750;
          }
          .ed-status {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            border-radius: 99px;
            padding: 5px 9px;
            font-size: 11px;
            background: #f1f1f1;
            color: #777;
            white-space: nowrap;
          }
          .ed-status i {
            width: 7px;
            height: 7px;
            background: currentColor;
            border-radius: 50%;
          }
          .ed-status.ed-good {
            background: #e1f6e9;
            color: #208b53;
          }
          .ed-status.ed-pending {
            background: #fff1cd;
            color: #9d720d;
          }
          .ed-status.ed-offline,
          .ed-status.ed-neutral {
            background: #f0f0f2;
            color: #778094;
          }
          .ed-status.ed-bad {
            background: #ffe6e6;
            color: #b43a3a;
          }
          .ed-unassigned {
            color: #b27800;
            background: #fff0c9;
            padding: 5px 9px;
            border-radius: 6px;
          }
          .ed-action {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 7px 9px;
            background: white;
            border: 1px solid #e6e2db;
            border-radius: 7px;
            color: #23344a;
            font-weight: 650 !important;
          }
          .ed-pagination {
            padding: 13px 17px;
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            color: #758195;
          }
          .ed-pagination > div {
            display: flex;
            align-items: center;
            gap: 9px;
          }
          .ed-pagination button {
            width: 31px;
            height: 31px;
            display: grid;
            place-items: center;
            border: 1px solid #e8e4df;
            background: white;
            border-radius: 7px;
          }
          .ed-side {
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 15px;
          }
          .ed-side-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 18px;
            border-bottom: 1px solid #eee9e2;
            gap: 10px;
          }
          .ed-side-heading h2 {
            display: inline-flex;
            align-items: center;
            gap: 9px;
            margin: 0;
            font-size: 16px;
            font-weight: 750;
          }
          .ed-side-heading > button {
            border: 0;
            background: transparent;
          }
          .ed-side-content { padding: 18px; }
          .ed-selected-device {
            display: flex;
            gap: 11px;
            align-items: center;
            border: 1px solid #eee8db;
            border-radius: 10px;
            background: #fff9eb;
            padding: 13px;
            margin-bottom: 18px;
          }
          .ed-selected-device > span {
            color: #9a6700;
          }
          .ed-selected-device > div {
            display: flex;
            flex-direction: column;
            gap: 5px;
            min-width: 0;
          }
          .ed-selected-device small {
            color: #788399;
            line-height: 1.4;
          }
          .ed-details {
            margin: 0 0 18px;
          }
          .ed-details > div {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            border-bottom: 1px solid #f0ece5;
            padding: 10px 0;
          }
          .ed-details dt { color: #7b8698; }
          .ed-details dd {
            margin: 0;
            font-weight: 650;
            text-align: right;
            overflow-wrap: anywhere;
          }
          .ed-field {
            display: flex;
            flex-direction: column;
            gap: 9px;
            font-weight: 700;
            margin-bottom: 15px;
          }
          .ed-field select { width: 100%; }
          .ed-confirm {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            padding: 10px;
            border-radius: 7px;
            background: #fff3d5;
            color: #9d720a;
            line-height: 1.5;
            margin-bottom: 12px;
          }
          .ed-feedback,
          .ed-notice {
            border-radius: 8px;
            padding: 12px;
            margin: 12px 0;
            line-height: 1.5;
          }
          .ed-notice {
            display: flex;
            align-items: center;
            gap: 10px;
          }
          .ed-notice span { flex: 1; }
          .ed-notice button {
            background: transparent;
            border: 0;
            text-decoration: underline;
          }
          .ed-error {
            background: #fff0f0;
            border: 1px solid #ecc3c3;
            color: #ad3535;
          }
          .ed-success {
            background: #edf8ed;
            border: 1px solid #c9e9c9;
            color: #257047;
          }
          .ed-empty {
            min-height: 230px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 11px;
            padding: 25px;
            text-align: center;
            color: #8590a3;
          }
          .ed-empty strong { color: var(--ed-ink); }
          .ed-empty p {
            max-width: 300px;
            margin: 0;
            line-height: 1.6;
          }
          .ed-side-empty { min-height: 285px; }
          .ed-help-content { padding: 18px; }
          .ed-help-content > div {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 17px;
          }
          .ed-help-content > div > span {
            display: grid;
            place-items: center;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            background: #ffedbd;
            color: #916000;
            font-weight: 750;
            flex-shrink: 0;
          }
          .ed-help-content p {
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 5px;
          }
          .ed-help-content small {
            font-size: 11px;
            color: #79869b;
            line-height: 1.5;
          }
          .ed-help-content a {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 9px;
            border-radius: 7px;
            background: #282622;
            color: white;
            min-height: 38px;
            text-decoration: none;
            font-weight: 650;
          }
          .ed-restricted {
            max-width: 1100px;
            display: grid;
            gap: 15px;
          }
          .ed-restricted-content { padding: 22px; }
          .ed-restricted-content > svg {
            color: #ae8a31;
          }
          .ed-restricted-content h3 {
            font-size: 19px;
            margin: 10px 0 5px;
          }
          .ed-restricted-content p {
            color: #78859a;
            line-height: 1.6;
          }
          .ed-restricted-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
          }
          .ed-readiness-count {
            padding: 7px 10px;
            border-radius: 20px;
            background: #fff2cb;
            color: #8b6306;
            white-space: nowrap;
          }
          .ed-readiness-grid {
            display: grid;
            gap: 10px;
            margin-top: 15px;
          }
          .ed-readiness-item {
            border: 1px solid #ebe7df;
            border-radius: 9px;
            background: white;
            display: flex;
            align-items: center;
            gap: 13px;
            padding: 14px;
          }
          .ed-readiness-item > div {
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 6px;
          }
          .ed-readiness-item small {
            color: #8490a0;
          }
          .ed-self-note {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 18px;
            color: #57704d;
          }
          .ed-self-note p {
            color: #7a8596;
            line-height: 1.6;
            margin: 6px 0 0;
          }
          .ed-spin {
            animation: ed-spin 1s linear infinite;
          }
          @keyframes ed-spin {
            to { transform: rotate(360deg); }
          }
          @media (max-width: 1250px) {
            .ed-workspace-grid {
              grid-template-columns: 1fr;
            }
            .ed-metrics {
              grid-template-columns: repeat(2,1fr);
            }
          }
          @media (max-width: 760px) {
            .ed-header {
              flex-direction: column;
            }
            .ed-metrics {
              grid-template-columns: 1fr;
            }
            .ed-page {
              padding: 15px;
            }
            .ed-readiness-item {
              flex-wrap: wrap;
            }
          }
        `}</style>
      </main>
    </WorkspaceRequired>
  );
}

function Metric({
  icon,
  label,
  value,
  description,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  description: string;
}) {
  return (
    <div className="ed-metric">
      <span className="ed-metric-icon">{icon}</span>
      <div className="ed-metric-copy">
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{description}</small>
      </div>
    </div>
  );
}
