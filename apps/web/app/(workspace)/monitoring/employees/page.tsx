
"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Download,
  Laptop2,
  Monitor,
  RefreshCw,
  Search,
  ShieldCheck,
  UserRound,
  UsersRound,
  WifiOff,
  X,
} from "lucide-react";

import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";
import {
  monitoringService,
  type MonitoringSnapshot,
} from "@/services/monitoring.service";

type Status = "online" | "idle" | "offline" | "unavailable";
type DetailTab = "overview" | "activity" | "devices";

type EmployeeRow = {
  id: string;
  employee_id: string;
  employee: string;
  employee_code: string;
  department: string;
  job_title: string;
  device: string;
  device_id: string | null;
  status: Status;
  last_signal: string | null;
  last_activity: string | null;
  last_activity_state: string | null;
  employment_status: string;
  agent_ready: boolean;
  device_count: number;
};

type DeviceRow = {
  id: string;
  employee_id: string;
  name: string;
  platform: string;
  agent_version: string;
  status: string;
  last_seen_at: string | null;
  agent_ready: boolean;
};

const PAGE_SIZE = 15;

const asText = (value: unknown, fallback = ""): string => {
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  return fallback;
};

const asBoolean = (value: unknown): boolean =>
  value === true || value === "true";

const asNumber = (value: unknown): number =>
  typeof value === "number" && Number.isFinite(value)
    ? value
    : Number(value) || 0;

function normalizeStatus(value: unknown): Status {
  switch (asText(value).toLowerCase()) {
    case "online":
    case "active":
      return "online";
    case "idle":
      return "idle";
    case "offline":
      return "offline";
    default:
      return "unavailable";
  }
}

function parseEmployee(
  value: Record<string, unknown>
): EmployeeRow {
  return {
    id: asText(value.id || value.employee_id),
    employee_id: asText(value.employee_id || value.id),
    employee: asText(
      value.employee || value.name,
      "Unknown employee"
    ),
    employee_code: asText(value.employee_code),
    department: asText(value.department, "Unassigned"),
    job_title: asText(value.job_title),
    device: asText(value.device, "No registered agent"),
    device_id: value.device_id
      ? asText(value.device_id)
      : null,
    status: normalizeStatus(value.status),
    last_signal: value.last_signal
      ? asText(value.last_signal)
      : null,
    last_activity: value.last_activity
      ? asText(value.last_activity)
      : null,
    last_activity_state: value.last_activity_state
      ? asText(value.last_activity_state)
      : null,
    employment_status: asText(value.employment_status),
    agent_ready: asBoolean(value.agent_ready),
    device_count: asNumber(value.device_count),
  };
}

function parseDevice(
  value: Record<string, unknown>
): DeviceRow {
  return {
    id: asText(value.id || value.device_id),
    employee_id: asText(value.employee_id),
    name: asText(value.name || value.device, "Device"),
    platform: asText(value.platform, "Unknown platform"),
    agent_version: asText(value.agent_version, "—"),
    status: asText(value.status, "offline"),
    last_seen_at: value.last_seen_at
      ? asText(value.last_seen_at)
      : null,
    agent_ready: asBoolean(value.agent_ready),
  };
}

function formatTime(value: string | null): string {
  if (!value) return "No signal";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  const seconds = Math.floor(
    (Date.now() - date.getTime()) / 1000
  );

  if (seconds < 0) return date.toLocaleString();
  if (seconds < 60) return "Just now";
  if (seconds < 3600) {
    return `${Math.floor(seconds / 60)} min ago`;
  }
  if (seconds < 86400) {
    return `${Math.floor(seconds / 3600)} hours ago`;
  }

  return date.toLocaleDateString();
}

function exportCsv(rows: EmployeeRow[]) {
  const headings = [
    "Employee",
    "Employee code",
    "Department",
    "Job title",
    "Assigned device",
    "Monitoring status",
    "Last signal",
    "Agent ready",
  ];

  const cells = rows.map((row) => [
    row.employee,
    row.employee_code,
    row.department,
    row.job_title,
    row.device,
    row.status,
    row.last_signal || "",
    row.agent_ready ? "Yes" : "No",
  ]);

  const escapeCell = (value: string): string => {
    // Avoid interpreting spreadsheet formula prefixes
    // when an administrator opens the exported CSV.
    const safe = /^[=+\-@\t\r]/.test(value)
      ? `'${value}`
      : value;

    return `"${safe.replaceAll('"', '""')}"`;
  };

  const csv = [headings, ...cells]
    .map((row) => row.map(escapeCell).join(","))
    .join("\r\n");

  const blob = new Blob(
    ["\uFEFF", csv],
    { type: "text/csv;charset=utf-8" }
  );

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "workforce-monitoring-employees.csv";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function StatusIndicator({
  status,
  badge = false,
}: {
  status: Status;
  badge?: boolean;
}) {
  const label =
    status === "unavailable"
      ? "No signal"
      : status.charAt(0).toUpperCase() + status.slice(1);

  return (
    <span
      className={`em-status em-status-${status} ${
        badge ? "em-status-badge" : ""
      }`}
    >
      <span className="em-dot" />
      {label}
    </span>
  );
}

function EmptyState({
  message,
}: {
  message: string;
}) {
  return (
    <div className="em-empty">
      <UsersRound size={28} strokeWidth={1.6} />
      <strong>{message}</strong>
      <span>
        Monitoring information appears when authorized
        employee and device records are available.
      </span>
    </div>
  );
}

export default function MonitoringEmployeesPage() {
  const {
    workspaceId,
    permissions,
    navigationView,
  } = useWorkspace();

  const allowed = hasAnyPermission(
    permissions,
    [
      "monitoring.all.read",
      "monitoring.team.read",
      "monitoring.self.read",
    ],
    navigationView
  );

  const canLiveScreen = hasAnyPermission(
    permissions,
    ["monitoring.live_screen"],
    navigationView
  );

  const [employeeData, setEmployeeData] =
    useState<MonitoringSnapshot | null>(null);

  const [deviceData, setDeviceData] =
    useState<MonitoringSnapshot | null>(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("all");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);

  const [selectedId, setSelectedId] = useState<string | null>(
    null
  );
  const [detailTab, setDetailTab] =
    useState<DetailTab>("overview");

  const loadData = useCallback(
    async (quiet = false) => {
      if (!workspaceId || !allowed) {
        setLoading(false);
        return;
      }

      if (quiet) setRefreshing(true);
      else setLoading(true);

      try {
        const [employeesResponse, devicesResponse] =
          await Promise.all([
            monitoringService.employees(workspaceId),
            monitoringService.devices(workspaceId),
          ]);

        setEmployeeData(employeesResponse);
        setDeviceData(devicesResponse);
        setError("");
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load monitoring employees."
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [workspaceId, allowed]
  );

  useEffect(() => {
    void loadData();
  }, [loadData]);

  useEffect(() => {
    if (!workspaceId || !allowed) return;

    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void loadData(true);
      }
    }, 30000);

    return () => window.clearInterval(timer);
  }, [workspaceId, allowed, loadData]);

  const employees = useMemo(() => {
    return (employeeData?.items || [])
      .map(parseEmployee)
      .filter((employee) => employee.employee_id);
  }, [employeeData]);

  const devices = useMemo(() => {
    return (deviceData?.items || [])
      .map(parseDevice)
      .filter((device) => device.id);
  }, [deviceData]);

  const summary = useMemo(() => {
    const raw = employeeData?.summary || {};

    const count = (key: string, fallback: number) =>
      raw[key] !== undefined
        ? asNumber(raw[key])
        : fallback;

    return {
      employees: count("employees", employees.length),
      online: count(
        "online",
        employees.filter((row) => row.status === "online")
          .length
      ),
      idle: count(
        "idle",
        employees.filter((row) => row.status === "idle")
          .length
      ),
      offline: count(
        "offline",
        employees.filter(
          (row) =>
            row.status === "offline" ||
            row.status === "unavailable"
        ).length
      ),
    };
  }, [employeeData, employees]);

  const departments = useMemo(() => {
    return Array.from(
      new Set(employees.map((row) => row.department))
    ).sort();
  }, [employees]);

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();

    return employees.filter((row) => {
      const matchesText =
        !needle ||
        [
          row.employee,
          row.employee_code,
          row.department,
          row.device,
          row.job_title,
        ]
          .join(" ")
          .toLowerCase()
          .includes(needle);

      const matchesDepartment =
        department === "all" ||
        row.department === department;

      const matchesStatus =
        status === "all" || row.status === status;

      return (
        matchesText &&
        matchesDepartment &&
        matchesStatus
      );
    });
  }, [employees, search, department, status]);

  const pageCount = Math.max(
    1,
    Math.ceil(filtered.length / PAGE_SIZE)
  );

  const currentPage = Math.min(page, pageCount);

  const visibleRows = filtered.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const selectedEmployee = employees.find(
    (row) => row.employee_id === selectedId
  );

  const selectedDevices = devices.filter(
    (device) =>
      device.employee_id === selectedEmployee?.employee_id
  );

  const percentage = (value: number) =>
    summary.employees > 0
      ? `${((value / summary.employees) * 100).toFixed(1)}%`
      : "0%";

  const changeFilter = (
    update: () => void
  ) => {
    update();
    setPage(1);
  };

  return (
    <WorkspaceRequired>
      <main className="em-page">
        <header className="em-page-header">
          <div>
            <h1>Employee Monitoring</h1>
            <p>
              View and monitor employee device status,
              activity and monitoring readiness.
            </p>
          </div>

          <div className="em-header-actions">
            <button
              type="button"
              className="em-btn"
              onClick={() => void loadData(true)}
              disabled={refreshing || !allowed}
            >
              <RefreshCw
                size={15}
                className={refreshing ? "em-spinning" : ""}
              />
              Refresh
            </button>

            <button
              type="button"
              className="em-btn em-btn-dark"
              onClick={() => exportCsv(filtered)}
              disabled={!allowed || filtered.length === 0}
            >
              <Download size={16} />
              Export
            </button>
          </div>
        </header>

        {!allowed ? (
          <section className="em-notice">
            <AlertTriangle size={18} />
            You do not have permission to view employee
            monitoring records.
          </section>
        ) : (
          <>
            {error && (
              <section className="em-notice em-error">
                <AlertTriangle size={18} />
                <span>{error}</span>
                <button
                  type="button"
                  onClick={() => void loadData()}
                >
                  Retry
                </button>
              </section>
            )}

            <section className="em-summary">
              <div className="em-summary-item">
                <span className="em-summary-icon">
                  <UsersRound size={31} />
                </span>
                <div>
                  <strong>{summary.employees}</strong>
                  <b>Employees</b>
                  <small>Total employees</small>
                </div>
              </div>

              <div className="em-summary-item">
                <span className="em-summary-icon">
                  <UserRound size={29} />
                </span>
                <div>
                  <strong>
                    <i className="em-dot em-green" />
                    {summary.online}
                  </strong>
                  <b>Online</b>
                  <small>
                    {percentage(summary.online)} of employees
                  </small>
                </div>
              </div>

              <div className="em-summary-item">
                <span className="em-summary-icon">
                  <UserRound size={29} />
                </span>
                <div>
                  <strong>
                    <i className="em-dot em-yellow" />
                    {summary.idle}
                  </strong>
                  <b>Idle</b>
                  <small>
                    {percentage(summary.idle)} of employees
                  </small>
                </div>
              </div>

              <div className="em-summary-item">
                <span className="em-summary-icon">
                  <UserRound size={29} />
                </span>
                <div>
                  <strong>
                    <i className="em-dot em-red" />
                    {summary.offline}
                  </strong>
                  <b>Offline</b>
                  <small>
                    {percentage(summary.offline)} of employees
                  </small>
                </div>
              </div>
            </section>

            <div
              className={`em-content ${
                selectedEmployee ? "em-with-details" : ""
              }`}
            >
              <section className="em-panel em-table-panel">
                <div className="em-panel-header">
                  <h2>
                    <UserRound size={22} />
                    Employees ({filtered.length})
                  </h2>

                  <div className="em-table-filters">
                    <label className="em-search">
                      <Search size={17} />
                      <input
                        value={search}
                        onChange={(event) =>
                          changeFilter(() =>
                            setSearch(event.target.value)
                          )
                        }
                        placeholder="Search employees..."
                      />
                    </label>

                    <select
                      aria-label="Filter by department"
                      value={department}
                      onChange={(event) =>
                        changeFilter(() =>
                          setDepartment(event.target.value)
                        )
                      }
                    >
                      <option value="all">
                        All departments
                      </option>
                      {departments.map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>

                    <select
                      aria-label="Filter by status"
                      value={status}
                      onChange={(event) =>
                        changeFilter(() =>
                          setStatus(event.target.value)
                        )
                      }
                    >
                      <option value="all">All status</option>
                      <option value="online">Online</option>
                      <option value="idle">Idle</option>
                      <option value="offline">Offline</option>
                      <option value="unavailable">
                        No signal
                      </option>
                    </select>
                  </div>
                </div>

                <div className="em-table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Assigned device</th>
                        <th>Status</th>
                        <th>Last signal</th>
                        <th>Monitoring readiness</th>
                        <th>Actions</th>
                      </tr>
                    </thead>

                    <tbody>
                      {visibleRows.map((employee) => (
                        <tr
                          key={employee.employee_id}
                          className={
                            selectedId === employee.employee_id
                              ? "em-selected-row"
                              : ""
                          }
                        >
                          <td>
                            <strong>{employee.employee}</strong>
                          </td>

                          <td>{employee.department}</td>

                          <td className="em-muted">
                            {employee.device}
                          </td>

                          <td>
                            <StatusIndicator
                              status={employee.status}
                            />
                          </td>

                          <td className="em-muted">
                            {formatTime(employee.last_signal)}
                          </td>

                          <td>
                            <span
                              className={
                                employee.agent_ready
                                  ? "em-ready"
                                  : "em-unavailable"
                              }
                            >
                              <i className="em-dot" />
                              {employee.agent_ready
                                ? "Ready"
                                : "Unavailable"}
                            </span>
                          </td>

                          <td>
                            <button
                              type="button"
                              className="em-detail-btn"
                              onClick={() => {
                                setSelectedId(
                                  employee.employee_id
                                );
                                setDetailTab("overview");
                              }}
                            >
                              View details
                              <ChevronRight size={15} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {!loading && visibleRows.length === 0 && (
                    <EmptyState
                      message={
                        employees.length === 0
                          ? "No employees available"
                          : "No matching employees"
                      }
                    />
                  )}

                  {loading && (
                    <div className="em-loading">
                      <RefreshCw
                        size={18}
                        className="em-spinning"
                      />
                      Loading employee monitoring...
                    </div>
                  )}
                </div>

                <footer className="em-pagination">
                  <span>
                    Showing{" "}
                    {filtered.length
                      ? (currentPage - 1) * PAGE_SIZE + 1
                      : 0}
                    –
                    {Math.min(
                      currentPage * PAGE_SIZE,
                      filtered.length
                    )}{" "}
                    of {filtered.length} employees
                  </span>

                  <div className="em-page-buttons">
                    <button
                      type="button"
                      aria-label="Previous page"
                      disabled={currentPage === 1}
                      onClick={() =>
                        setPage((value) =>
                          Math.max(1, value - 1)
                        )
                      }
                    >
                      <ChevronLeft size={16} />
                    </button>

                    {Array.from(
                      { length: Math.min(pageCount, 5) },
                      (_, index) => {
                        const start = Math.max(
                          1,
                          Math.min(
                            currentPage - 2,
                            pageCount - 4
                          )
                        );
                        const number = start + index;

                        if (number > pageCount) return null;

                        return (
                          <button
                            key={number}
                            type="button"
                            className={
                              currentPage === number
                                ? "em-page-active"
                                : ""
                            }
                            onClick={() => setPage(number)}
                          >
                            {number}
                          </button>
                        );
                      }
                    )}

                    <button
                      type="button"
                      aria-label="Next page"
                      disabled={currentPage >= pageCount}
                      onClick={() =>
                        setPage((value) =>
                          Math.min(pageCount, value + 1)
                        )
                      }
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </footer>
              </section>

              {selectedEmployee && (
                <aside className="em-panel em-details">
                  <div className="em-profile">
                    <span className="em-avatar">
                      {selectedEmployee.employee
                        .split(" ")
                        .slice(0, 2)
                        .map((part) => part.charAt(0))
                        .join("")
                        .toUpperCase()}
                    </span>

                    <div className="em-profile-text">
                      <div className="em-profile-name">
                        <h2>{selectedEmployee.employee}</h2>
                        <StatusIndicator
                          status={selectedEmployee.status}
                          badge
                        />
                      </div>
                      <p>{selectedEmployee.department}</p>
                      <small>
                        <Monitor size={14} />
                        {selectedEmployee.device}
                      </small>
                    </div>

                    <button
                      type="button"
                      className="em-close"
                      aria-label="Close employee details"
                      onClick={() => setSelectedId(null)}
                    >
                      <X size={18} />
                    </button>
                  </div>

                  <div className="em-tabs">
                    {(
                      ["overview", "activity", "devices"] as const
                    ).map((tab) => (
                      <button
                        key={tab}
                        type="button"
                        className={
                          detailTab === tab ? "em-tab-active" : ""
                        }
                        onClick={() => setDetailTab(tab)}
                      >
                        {tab.charAt(0).toUpperCase() +
                          tab.slice(1)}
                      </button>
                    ))}
                  </div>

                  {detailTab === "overview" && (
                    <div className="em-details-body">
                      <h3>
                        <UsersRound size={18} />
                        Employee information
                      </h3>

                      <dl>
                        <div>
                          <dt>Name</dt>
                          <dd>{selectedEmployee.employee}</dd>
                        </div>
                        <div>
                          <dt>Employee code</dt>
                          <dd>
                            {selectedEmployee.employee_code ||
                              "—"}
                          </dd>
                        </div>
                        <div>
                          <dt>Department</dt>
                          <dd>{selectedEmployee.department}</dd>
                        </div>
                        <div>
                          <dt>Assigned device</dt>
                          <dd>{selectedEmployee.device}</dd>
                        </div>
                        <div>
                          <dt>Job title</dt>
                          <dd>
                            {selectedEmployee.job_title || "—"}
                          </dd>
                        </div>
                        <div>
                          <dt>Employment status</dt>
                          <dd>
                            {selectedEmployee.employment_status ||
                              "—"}
                          </dd>
                        </div>
                        <div>
                          <dt>Monitoring status</dt>
                          <dd>
                            <StatusIndicator
                              status={selectedEmployee.status}
                            />
                          </dd>
                        </div>
                        <div>
                          <dt>Last signal</dt>
                          <dd>
                            {formatTime(
                              selectedEmployee.last_signal
                            )}
                          </dd>
                        </div>
                        <div>
                          <dt>Monitoring readiness</dt>
                          <dd>
                            {selectedEmployee.agent_ready
                              ? "Ready"
                              : "Unavailable"}
                          </dd>
                        </div>
                      </dl>
                    </div>
                  )}

                  {detailTab === "activity" && (
                    <div className="em-details-body">
                      <h3>
                        <Activity size={18} />
                        Latest activity
                      </h3>

                      <dl>
                        <div>
                          <dt>Last observed</dt>
                          <dd>
                            {formatTime(
                              selectedEmployee.last_activity
                            )}
                          </dd>
                        </div>
                        <div>
                          <dt>Reported state</dt>
                          <dd>
                            {selectedEmployee.last_activity_state ||
                              "No activity recorded"}
                          </dd>
                        </div>
                      </dl>

                      <p className="em-hint">
                        Activity history is separate from live
                        monitoring status. An old activity event
                        does not mean an employee is online.
                      </p>

                      <Link
                        href="/monitoring/activity"
                        className="em-action-link"
                      >
                        <Activity size={17} />
                        View activity timeline
                        <ArrowRight size={16} />
                      </Link>
                    </div>
                  )}

                  {detailTab === "devices" && (
                    <div className="em-details-body">
                      <h3>
                        <Laptop2 size={18} />
                        Registered devices
                      </h3>

                      {selectedDevices.length ? (
                        selectedDevices.map((device) => (
                          <div
                            className="em-device-card"
                            key={device.id}
                          >
                            <strong>
                              <Laptop2 size={17} />
                              {device.name}
                            </strong>
                            <span>{device.platform}</span>
                            <span>
                              Agent version:{" "}
                              {device.agent_version}
                            </span>
                            <span>
                              Last heartbeat:{" "}
                              {formatTime(
                                device.last_seen_at
                              )}
                            </span>
                            <span>
                              {device.agent_ready ? (
                                <Check size={14} />
                              ) : (
                                <WifiOff size={14} />
                              )}
                              {device.status}
                            </span>
                          </div>
                        ))
                      ) : (
                        <p className="em-hint">
                          No registered desktop agent devices
                          are assigned to this employee.
                        </p>
                      )}

                      <Link
                        href="/monitoring/devices"
                        className="em-action-link"
                      >
                        <Laptop2 size={17} />
                        Open device inventory
                        <ArrowRight size={16} />
                      </Link>
                    </div>
                  )}

                  <div className="em-detail-actions">
                    <Link
                      href="/monitoring/activity"
                      className="em-action-link em-primary-link"
                    >
                      <Activity size={17} />
                      View activity
                      <ArrowRight size={16} />
                    </Link>

                    {canLiveScreen && (
                      selectedEmployee.agent_ready &&
                      selectedEmployee.device_id ? (
                        <Link
                          href="/monitoring/live-screen"
                          className="em-action-link"
                        >
                          <Monitor size={17} />
                          Open live-screen requests
                          <ChevronRight size={16} />
                        </Link>
                      ) : (
                        <div className="em-disabled-action">
                          <Monitor size={17} />
                          Live screen unavailable:
                          no connected agent
                        </div>
                      )
                    )}
                  </div>
                </aside>
              )}
            </div>

            <section className="em-footnote">
              <ShieldCheck size={15} />
              Monitoring status is based on authorized agent
              signals. Missing or outdated heartbeats are not
              treated as live activity.
              <Clock3 size={14} />
              Updated:{" "}
              {employeeData?.generated_at
                ? formatTime(employeeData.generated_at)
                : "Not available"}
            </section>
          </>
        )}

        <style jsx global>{`
          .em-page {
            --em-navy: #071638;
            --em-muted: #637390;
            --em-border: #e5e7eb;
            --em-surface: #fffefa;
            --em-amber: #ffb51e;
            padding: 20px 22px 32px;
            min-height: 100%;
            background: #fbfaf7;
            color: var(--em-navy);
            font-size: 13px;
          }

          .em-page * {
            box-sizing: border-box;
          }

          .em-page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            margin-bottom: 18px;
          }

          .em-page-header h1 {
            font-size: 29px;
            line-height: 1.2;
            letter-spacing: -0.9px;
            margin: 0;
            font-weight: 750;
          }

          .em-page-header p {
            color: var(--em-muted);
            margin: 5px 0 0;
            font-size: 14px;
          }

          .em-header-actions {
            display: flex;
            align-items: center;
            gap: 8px;
          }

          .em-btn,
          .em-detail-btn,
          .em-close,
          .em-page-buttons button {
            cursor: pointer;
            font: inherit;
          }

          .em-btn {
            height: 36px;
            padding: 0 15px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: #fff;
            color: var(--em-navy);
            border: 1px solid #dce1e8;
            border-radius: 7px;
            font-weight: 600;
          }

          .em-btn-dark {
            background: #17232f;
            border-color: #17232f;
            color: white;
          }

          .em-btn:disabled,
          .em-detail-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }

          .em-notice {
            display: flex;
            align-items: center;
            gap: 10px;
            border: 1px solid #f3daa0;
            background: #fff8e8;
            border-radius: 9px;
            padding: 13px 16px;
            margin-bottom: 16px;
          }

          .em-error {
            border-color: #f4b5b5;
            background: #fff1f1;
            color: #b72a2a;
          }

          .em-error button {
            margin-left: auto;
            background: #fff;
            border: 1px solid #efcccc;
            border-radius: 6px;
            padding: 6px 12px;
          }

          .em-summary {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin-bottom: 16px;
            border: 1px solid #eee8dc;
            border-radius: 13px;
            background: linear-gradient(
              100deg,
              #fffaf0 0%,
              #fffdfa 54%,
              #fffaf2 100%
            );
            padding: 14px 8px;
            min-height: 94px;
          }

          .em-summary-item {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            border-right: 1px solid #e9e4dc;
            min-width: 0;
          }

          .em-summary-item:last-child {
            border-right: 0;
          }

          .em-summary-icon {
            color: #101d3c;
            display: flex;
            align-items: center;
          }

          .em-summary-item strong {
            display: flex;
            align-items: center;
            gap: 9px;
            font-size: 26px;
            line-height: 1.05;
            letter-spacing: -0.7px;
            font-weight: 750;
          }

          .em-summary-item b {
            display: block;
            font-size: 13px;
            margin-top: 4px;
          }

          .em-summary-item small {
            display: block;
            font-size: 12px;
            color: var(--em-muted);
            margin-top: 4px;
          }

          .em-dot {
            width: 10px;
            height: 10px;
            display: inline-block;
            border-radius: 50%;
            background: #94a3b8;
            flex-shrink: 0;
          }

          .em-green,
          .em-status-online .em-dot,
          .em-ready .em-dot {
            background: #24bf79;
          }

          .em-yellow,
          .em-status-idle .em-dot {
            background: #ffb71b;
          }

          .em-red,
          .em-status-offline .em-dot {
            background: #ff4848;
          }

          .em-status-unavailable .em-dot,
          .em-unavailable .em-dot {
            background: #8d98ab;
          }

          .em-status,
          .em-ready,
          .em-unavailable {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            white-space: nowrap;
            font-size: 12px;
          }

          .em-status-badge {
            border-radius: 999px;
            background: #e1f8e9;
            padding: 5px 10px;
          }

          .em-status-idle.em-status-badge {
            background: #fff2d1;
          }

          .em-status-offline.em-status-badge {
            background: #ffe4e4;
          }

          .em-status-unavailable.em-status-badge {
            background: #eef0f4;
          }

          .em-content {
            display: grid;
            grid-template-columns: minmax(0, 1fr);
            gap: 14px;
            align-items: stretch;
          }

          .em-with-details {
            grid-template-columns: minmax(0, 1.8fr) minmax(
                340px,
                0.95fr
              );
          }

          .em-panel {
            background: var(--em-surface);
            border: 1px solid var(--em-border);
            border-radius: 12px;
            overflow: hidden;
          }

          .em-table-panel {
            min-width: 0;
          }

          .em-panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 12px 13px;
            min-height: 56px;
          }

          .em-panel-header h2 {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 17px;
            margin: 0;
            letter-spacing: -0.3px;
            white-space: nowrap;
          }

          .em-table-filters {
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 0;
          }

          .em-search {
            display: flex;
            align-items: center;
            gap: 7px;
            height: 34px;
            padding: 0 10px;
            color: #7c8ba0;
            background: #fff;
            border: 1px solid #dce1e8;
            border-radius: 7px;
          }

          .em-search input {
            width: 135px;
            border: 0;
            outline: 0;
            background: transparent;
            color: var(--em-navy);
            font: inherit;
          }

          .em-search input::placeholder {
            color: #8491a6;
          }

          .em-table-filters select {
            height: 34px;
            max-width: 155px;
            border: 1px solid #dce1e8;
            background: white;
            color: var(--em-navy);
            border-radius: 7px;
            padding: 0 9px;
            font: inherit;
            cursor: pointer;
          }

          .em-table-scroll {
            width: 100%;
            overflow-x: auto;
          }

          .em-table-scroll table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            min-width: 850px;
          }

          .em-table-scroll th {
            background: #f7f7f7;
            font-size: 11px;
            font-weight: 650;
            padding: 12px 10px;
            white-space: nowrap;
          }

          .em-table-scroll td {
            padding: 10px;
            border-top: 1px solid #e8e9ec;
            font-size: 12px;
            white-space: nowrap;
          }

          .em-table-scroll td strong {
            font-weight: 650;
          }

          .em-muted {
            color: var(--em-muted);
          }

          .em-selected-row {
            background: #fff7e5;
          }

          .em-table-scroll tbody tr:hover {
            background: #fffaf0;
          }

          .em-detail-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #fff;
            border: 1px solid #dde1e6;
            border-radius: 6px;
            padding: 6px 9px;
            font-size: 11px;
            font-weight: 650;
            color: var(--em-navy);
          }

          .em-detail-btn:hover,
          .em-btn:hover {
            border-color: #ffbf42;
          }

          .em-empty,
          .em-loading {
            min-height: 180px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 9px;
            text-align: center;
            padding: 25px;
            color: #8390a4;
          }

          .em-empty strong {
            color: var(--em-navy);
          }

          .em-empty span {
            max-width: 320px;
            line-height: 1.5;
          }

          .em-pagination {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 12px 15px;
            min-height: 62px;
            color: var(--em-muted);
            font-size: 12px;
          }

          .em-page-buttons {
            display: flex;
            align-items: center;
            gap: 6px;
          }

          .em-page-buttons button {
            min-width: 30px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #e4e6eb;
            background: #fff;
            border-radius: 7px;
            color: var(--em-navy);
          }

          .em-page-buttons button:disabled {
            opacity: 0.4;
            cursor: not-allowed;
          }

          .em-page-buttons button.em-page-active {
            background: var(--em-amber);
            border-color: var(--em-amber);
            font-weight: 700;
          }

          .em-profile {
            display: flex;
            align-items: center;
            gap: 13px;
            padding: 22px 16px 20px;
            position: relative;
          }

          .em-avatar {
            flex-shrink: 0;
            width: 66px;
            height: 66px;
            border-radius: 50%;
            background: #ffedc6;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 23px;
          }

          .em-profile-text {
            min-width: 0;
          }

          .em-profile-name {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
          }

          .em-profile-name h2 {
            margin: 0;
            font-size: 18px;
            letter-spacing: -0.4px;
          }

          .em-profile p {
            margin: 6px 0;
            color: var(--em-muted);
          }

          .em-profile small {
            display: flex;
            align-items: center;
            gap: 7px;
            color: var(--em-muted);
            line-height: 1.5;
          }

          .em-close {
            position: absolute;
            right: 12px;
            top: 13px;
            background: transparent;
            border: 0;
            color: #52617c;
          }

          .em-tabs {
            margin: 0 12px;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            border: 1px solid #e5e7ec;
            background: #fafafa;
            border-radius: 8px;
            overflow: hidden;
          }

          .em-tabs button {
            border: 0;
            border-right: 1px solid #e7e8ec;
            background: transparent;
            padding: 12px 6px;
            color: #4b5d79;
            cursor: pointer;
            font: inherit;
          }

          .em-tabs button:last-child {
            border-right: 0;
          }

          .em-tabs .em-tab-active {
            background: #fff;
            box-shadow: inset 0 -2px var(--em-amber);
            color: var(--em-navy);
            font-weight: 650;
          }

          .em-details-body {
            padding: 18px 14px;
          }

          .em-details-body h3 {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0 0 12px;
            font-size: 14px;
          }

          .em-details-body dl {
            margin: 0;
          }

          .em-details-body dl div {
            display: grid;
            grid-template-columns: minmax(100px, 0.9fr) 1.2fr;
            gap: 10px;
            border-bottom: 1px solid #e9ebef;
            padding: 12px 0;
            font-size: 12px;
          }

          .em-details-body dt {
            color: var(--em-muted);
          }

          .em-details-body dd {
            margin: 0;
            overflow-wrap: anywhere;
            font-weight: 550;
          }

          .em-hint {
            border: 1px solid #e9ebef;
            background: #fafbfc;
            padding: 12px;
            line-height: 1.6;
            border-radius: 8px;
            color: var(--em-muted);
          }

          .em-device-card {
            display: flex;
            flex-direction: column;
            gap: 9px;
            padding: 12px;
            border: 1px solid #e8eaf0;
            border-radius: 9px;
            margin-bottom: 10px;
            color: var(--em-muted);
          }

          .em-device-card strong,
          .em-device-card span:last-child {
            display: flex;
            align-items: center;
            gap: 7px;
            color: var(--em-navy);
          }

          .em-detail-actions {
            display: flex;
            flex-direction: column;
            gap: 8px;
            padding: 10px 14px 18px;
          }

          .em-action-link {
            display: flex;
            align-items: center;
            gap: 9px;
            min-height: 38px;
            padding: 9px 12px;
            border: 1px solid #dce1e8;
            border-radius: 7px;
            text-decoration: none;
            font-size: 12px;
            color: var(--em-navy);
            background: white;
            font-weight: 650;
          }

          .em-action-link svg:last-child {
            margin-left: auto;
          }

          .em-primary-link {
            background: #142232;
            color: white;
            border-color: #142232;
          }

          .em-disabled-action {
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 12px;
            border: 1px solid #e5e7eb;
            border-radius: 7px;
            color: #8892a4;
            background: #f9fafb;
            font-size: 12px;
          }

          .em-footnote {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
            margin-top: 14px;
            font-size: 11px;
            color: #75839a;
          }

          .em-spinning {
            animation: em-spin 1s linear infinite;
          }

          @keyframes em-spin {
            to {
              transform: rotate(360deg);
            }
          }

          @media (max-width: 1270px) {
            .em-with-details {
              grid-template-columns: minmax(0, 1fr);
            }

            .em-panel-header {
              align-items: flex-start;
              flex-wrap: wrap;
            }
          }

          @media (max-width: 850px) {
            .em-summary {
              grid-template-columns: repeat(2, 1fr);
              gap: 16px 0;
            }

            .em-summary-item:nth-child(2) {
              border-right: 0;
            }

            .em-page-header {
              align-items: flex-start;
              flex-direction: column;
            }

            .em-table-filters {
              width: 100%;
              flex-wrap: wrap;
            }
          }

          @media (max-width: 520px) {
            .em-page {
              padding: 14px;
            }

            .em-page-header h1 {
              font-size: 24px;
            }

            .em-summary-item {
              gap: 8px;
            }

            .em-summary-item strong {
              font-size: 22px;
            }

            .em-summary-icon svg {
              width: 24px;
            }

            .em-pagination {
              flex-wrap: wrap;
            }
          }
        `}</style>
      </main>
    </WorkspaceRequired>
  );
}
