
"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Bell,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Download,
  Filter,
  Info,
  Laptop2,
  MoreHorizontal,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";

import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";
import {
  monitoringService,
  type MonitoringSnapshot,
} from "@/services/monitoring.service";

type Severity = "critical" | "high" | "medium" | "low" | "unknown";
type AlertStatus =
  | "open"
  | "acknowledged"
  | "resolved"
  | "dismissed"
  | "unknown";

type Alert = {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  status: AlertStatus;
  employee: string;
  employeeId: string;
  device: string;
  deviceId: string;
  department: string;
  category: string;
  source: string;
  assignedTo: string;
  resolutionNotes: string;
  createdAt: string;
  updatedAt: string;
};

type StatusFilter = AlertStatus | "all";
type SeverityFilter = Severity | "all";
type TimeFilter = "all" | "today" | "7days" | "30days";

const PAGE_SIZE = 10;

const asText = (value: unknown, fallback = ""): string => {
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  return fallback;
};

function timestamp(value: string): number {
  const result = new Date(value).getTime();
  return Number.isFinite(result) ? result : 0;
}

function normalizeSeverity(value: unknown): Severity {
  const raw = asText(value).trim().toLowerCase();

  if (raw === "critical" || raw === "severe") return "critical";
  if (raw === "high") return "high";
  if (raw === "medium" || raw === "moderate") return "medium";
  if (raw === "low" || raw === "info" || raw === "informational") {
    return "low";
  }
  return "unknown";
}

function normalizeStatus(value: unknown): AlertStatus {
  const raw = asText(value).trim().toLowerCase();

  if (raw === "open" || raw === "new" || raw === "active") {
    return "open";
  }
  if (raw === "acknowledged" || raw === "in_progress") {
    return "acknowledged";
  }
  if (raw === "resolved" || raw === "closed") {
    return "resolved";
  }
  if (raw === "dismissed") return "dismissed";
  return "unknown";
}

function normalizeAlert(
  record: Record<string, unknown>,
  index: number
): Alert {
  const createdAt = asText(
    record.created_at ??
      record.triggered_at ??
      record.detected_at ??
      record.captured_at ??
      record.timestamp
  );

  return {
    id: asText(
      record.alert_id ?? record.id,
      `alert-${index}`
    ),
    title: asText(
      record.title ??
        record.alert_title ??
        record.name ??
        record.message,
      "Monitoring alert"
    ),
    description: asText(
      record.description ??
        record.details ??
        record.message,
      "No additional details were provided."
    ),
    severity: normalizeSeverity(
      record.severity ?? record.priority
    ),
    status: normalizeStatus(record.status),
    employee: asText(
      record.employee_name ?? record.employee,
      "Unassigned"
    ),
    employeeId: asText(record.employee_id),
    device: asText(
      record.device_name ?? record.device,
      "Not specified"
    ),
    deviceId: asText(record.device_id),
    department: asText(
      record.department_name ?? record.department,
      "Not specified"
    ),
    category: asText(
      record.alert_type ??
        record.category ??
        record.event_type,
      "Monitoring"
    ),
    source: asText(record.source, "monitoring"),
    assignedTo: asText(
      record.assigned_to_name ?? record.assigned_to,
      "Unassigned"
    ),
    resolutionNotes: asText(
      record.resolution_notes ?? record.resolution
    ),
    createdAt,
    updatedAt: asText(
      record.updated_at ?? record.resolved_at,
      createdAt
    ),
  };
}

function formatDate(value: string): string {
  const time = timestamp(value);
  if (!time) return "Not reported";

  return new Date(time).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function relativeDate(value: string): string {
  const time = timestamp(value);
  if (!time) return "Unknown";

  const seconds = Math.max(
    0,
    Math.floor((Date.now() - time) / 1000)
  );

  if (seconds < 60) return "Just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;

  return new Date(time).toLocaleDateString();
}

function inTimeRange(value: string, range: TimeFilter): boolean {
  if (range === "all") return true;

  const time = timestamp(value);
  if (!time) return false;

  const now = new Date();
  const start = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate()
  );

  if (range === "today") return time >= start.getTime();

  start.setDate(
    start.getDate() - (range === "7days" ? 6 : 29)
  );

  return time >= start.getTime();
}

function csvEscape(value: string): string {
  const safe = /^[=+\-@\t\r]/.test(value)
    ? `'${value}`
    : value;

  return `"${safe.replaceAll('"', '""')}"`;
}

function exportCsv(rows: Alert[]): void {
  const data = [
    [
      "Alert ID",
      "Title",
      "Description",
      "Severity",
      "Status",
      "Category",
      "Employee",
      "Employee ID",
      "Device",
      "Device ID",
      "Department",
      "Assigned To",
      "Detected At",
      "Updated At",
      "Source",
      "Resolution Notes",
    ],
    ...rows.map((alert) => [
      alert.id,
      alert.title,
      alert.description,
      alert.severity,
      alert.status,
      alert.category,
      alert.employee,
      alert.employeeId,
      alert.device,
      alert.deviceId,
      alert.department,
      alert.assignedTo,
      alert.createdAt,
      alert.updatedAt,
      alert.source,
      alert.resolutionNotes,
    ]),
  ];

  const csv = data
    .map((row) => row.map(csvEscape).join(","))
    .join("\r\n");

  const blob = new Blob(["\uFEFF", csv], {
    type: "text/csv;charset=utf-8",
  });

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = "workforce-monitoring-alerts.csv";

  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function SeverityBadge({ severity }: { severity: Severity }) {
  const label = severity.charAt(0).toUpperCase() +
    severity.slice(1);

  return (
    <span className={`al-severity al-severity-${severity}`}>
      <span className="al-severity-dot" />
      {label}
    </span>
  );
}

function StatusBadge({ status }: { status: AlertStatus }) {
  const labels: Record<AlertStatus, string> = {
    open: "Open",
    acknowledged: "Acknowledged",
    resolved: "Resolved",
    dismissed: "Dismissed",
    unknown: "Unknown",
  };

  return (
    <span className={`al-status al-status-${status}`}>
      {status === "resolved" ? (
        <CheckCircle2 size={13} />
      ) : (
        <span className="al-status-dot" />
      )}
      {labels[status]}
    </span>
  );
}

function SummaryMetric({
  icon,
  label,
  value,
  detail,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  detail: string;
  tone: "red" | "orange" | "yellow" | "blue";
}) {
  return (
    <div className="al-metric">
      <span className={`al-metric-icon al-tone-${tone}`}>
        {icon}
      </span>

      <div>
        <strong>{value}</strong>
        <span>{label}</span>
        <small>{detail}</small>
      </div>
    </div>
  );
}

export default function MonitoringAlertsPage() {
  const {
    workspaceId,
    permissions,
    navigationView,
  } = useWorkspace();

  const canRead = hasAnyPermission(
    permissions,
    [
      "monitoring.all.read",
      "monitoring.team.read",
      "monitoring.self.read",
    ],
    navigationView
  );

  const [snapshot, setSnapshot] =
    useState<MonitoringSnapshot | null>(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] =
    useState<SeverityFilter>("all");
  const [statusFilter, setStatusFilter] =
    useState<StatusFilter>("all");
  const [departmentFilter, setDepartmentFilter] =
    useState("all");
  const [timeFilter, setTimeFilter] =
    useState<TimeFilter>("all");
  const [page, setPage] = useState(1);

  const [selectedId, setSelectedId] =
    useState<string | null>(null);
  const [detailsTab, setDetailsTab] =
    useState<"details" | "activity">("details");
  const [showFilters, setShowFilters] = useState(true);

  const load = useCallback(
    async (quiet = false) => {
      if (!workspaceId || !canRead) {
        setSnapshot(null);
        setLoading(false);
        return;
      }

      if (quiet) setRefreshing(true);
      else setLoading(true);

      try {
        const response = await monitoringService.alerts(
          workspaceId
        );

        setSnapshot(response);
        setError("");
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to retrieve monitoring alerts."
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [workspaceId, canRead]
  );

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!workspaceId || !canRead) return;

    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void load(true);
      }
    }, 30000);

    return () => window.clearInterval(timer);
  }, [workspaceId, canRead, load]);

  const alerts = useMemo(() => {
    return (snapshot?.items ?? [])
      .map(normalizeAlert)
      .sort(
        (a, b) =>
          timestamp(b.createdAt) -
          timestamp(a.createdAt)
      );
  }, [snapshot]);

  const departments = useMemo(
    () =>
      [...new Set(alerts.map((a) => a.department))]
        .filter((item) => item !== "Not specified")
        .sort(),
    [alerts]
  );

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();

    return alerts.filter((alert) => {
      const matchesSearch =
        !needle ||
        [
          alert.title,
          alert.description,
          alert.employee,
          alert.device,
          alert.category,
          alert.id,
        ]
          .join(" ")
          .toLowerCase()
          .includes(needle);

      return (
        matchesSearch &&
        (severityFilter === "all" ||
          alert.severity === severityFilter) &&
        (statusFilter === "all" ||
          alert.status === statusFilter) &&
        (departmentFilter === "all" ||
          alert.department === departmentFilter) &&
        inTimeRange(alert.createdAt, timeFilter)
      );
    });
  }, [
    alerts,
    search,
    severityFilter,
    statusFilter,
    departmentFilter,
    timeFilter,
  ]);

  const totals = useMemo(
    () => ({
      open: alerts.filter((a) => a.status === "open").length,
      high: alerts.filter(
        (a) =>
          (a.severity === "high" ||
            a.severity === "critical") &&
          a.status !== "resolved" &&
          a.status !== "dismissed"
      ).length,
      medium: alerts.filter(
        (a) =>
          a.severity === "medium" &&
          a.status !== "resolved" &&
          a.status !== "dismissed"
      ).length,
      low: alerts.filter(
        (a) =>
          a.severity === "low" &&
          a.status !== "resolved" &&
          a.status !== "dismissed"
      ).length,
    }),
    [alerts]
  );

  const pages = Math.max(
    1,
    Math.ceil(filtered.length / PAGE_SIZE)
  );
  const currentPage = Math.min(page, pages);

  const visible = filtered.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const selected =
    alerts.find((item) => item.id === selectedId) ||
    alerts[0] ||
    null;

  const recentAlerts = useMemo(
    () => alerts.slice(0, 6),
    [alerts]
  );

  const clearFilters = () => {
    setSearch("");
    setSeverityFilter("all");
    setStatusFilter("all");
    setDepartmentFilter("all");
    setTimeFilter("all");
    setPage(1);
  };

  return (
    <WorkspaceRequired>
      <main className="al-page">
        <header className="al-page-header">
          <div>
            <h1>Monitoring Alerts</h1>
            <p>
              Track monitoring exceptions, review alerts,
              and identify devices or employees that
              need attention.
            </p>
          </div>

          <div className="al-header-actions">
            <button
              type="button"
              className="al-btn al-btn-outline"
              disabled={!canRead || refreshing}
              onClick={() => void load(true)}
            >
              <RefreshCw
                size={16}
                className={refreshing ? "al-spin" : ""}
              />
              Refresh
            </button>

            <button
              type="button"
              className="al-btn al-btn-dark"
              disabled={!canRead || filtered.length === 0}
              onClick={() => exportCsv(filtered)}
            >
              <Download size={16} />
              Export alerts
            </button>
          </div>
        </header>

        {!canRead ? (
          <div className="al-error">
            <AlertTriangle size={18} />
            You do not have permission to view monitoring
            alerts.
          </div>
        ) : (
          <>
            {error && (
              <div className="al-error">
                <AlertTriangle size={18} />
                <span>{error}</span>
                <button
                  type="button"
                  onClick={() => void load()}
                >
                  Retry
                </button>
              </div>
            )}

            <section className="al-summary">
              <SummaryMetric
                icon={<Bell size={28} />}
                label="Open alerts"
                value={totals.open}
                detail="Awaiting attention"
                tone="red"
              />
              <SummaryMetric
                icon={<ShieldAlert size={28} />}
                label="High priority"
                value={totals.high}
                detail="High and critical severity"
                tone="orange"
              />
              <SummaryMetric
                icon={<AlertTriangle size={28} />}
                label="Medium priority"
                value={totals.medium}
                detail="Medium-severity alerts"
                tone="yellow"
              />
              <SummaryMetric
                icon={<Info size={28} />}
                label="Low priority"
                value={totals.low}
                detail="Low-severity alerts"
                tone="blue"
              />
            </section>

            <div className="al-toolbar">
              <label className="al-search">
                <Search size={17} />
                <input
                  type="search"
                  placeholder="Search alert, employee, device..."
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                  }}
                />
              </label>

              <button
                type="button"
                className="al-filter-toggle"
                aria-expanded={showFilters}
                onClick={() =>
                  setShowFilters((value) => !value)
                }
              >
                <Filter size={17} />
                Filters
                <ChevronDown size={15} />
              </button>

              <label className="al-time-filter">
                <CalendarDays size={16} />
                <select
                  aria-label="Filter time period"
                  value={timeFilter}
                  onChange={(event) => {
                    setTimeFilter(
                      event.target.value as TimeFilter
                    );
                    setPage(1);
                  }}
                >
                  <option value="all">All available</option>
                  <option value="today">Today</option>
                  <option value="7days">Last 7 days</option>
                  <option value="30days">Last 30 days</option>
                </select>
              </label>

              <button
                type="button"
                className="al-clear"
                onClick={clearFilters}
              >
                Clear filters
              </button>
            </div>

            {showFilters && (
              <div className="al-filter-row">
                <label>
                  Severity
                  <select
                    value={severityFilter}
                    onChange={(event) => {
                      setSeverityFilter(
                        event.target.value as SeverityFilter
                      );
                      setPage(1);
                    }}
                  >
                    <option value="all">All severities</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </label>

                <label>
                  Status
                  <select
                    value={statusFilter}
                    onChange={(event) => {
                      setStatusFilter(
                        event.target.value as StatusFilter
                      );
                      setPage(1);
                    }}
                  >
                    <option value="all">All statuses</option>
                    <option value="open">Open</option>
                    <option value="acknowledged">
                      Acknowledged
                    </option>
                    <option value="resolved">Resolved</option>
                    <option value="dismissed">Dismissed</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </label>

                <label>
                  Department
                  <select
                    value={departmentFilter}
                    onChange={(event) => {
                      setDepartmentFilter(event.target.value);
                      setPage(1);
                    }}
                  >
                    <option value="all">All departments</option>
                    {departments.map((department) => (
                      <option
                        key={department}
                        value={department}
                      >
                        {department}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            )}

            <div className="al-layout">
              <section className="al-card al-table-card">
                <div className="al-card-heading">
                  <h2>
                    <ShieldAlert size={21} />
                    Alert inventory
                  </h2>
                  <span>
                    Showing {filtered.length} alerts
                  </span>
                </div>

                <div className="al-table-wrap">
                  <table className="al-table">
                    <thead>
                      <tr>
                        <th>Alert</th>
                        <th>Severity</th>
                        <th>Employee / device</th>
                        <th>Detected</th>
                        <th>Status</th>
                        <th>Assigned to</th>
                        <th />
                      </tr>
                    </thead>

                    <tbody>
                      {visible.map((alert) => (
                        <tr
                          key={alert.id}
                          className={
                            selected?.id === alert.id
                              ? "al-row-selected"
                              : ""
                          }
                        >
                          <td>
                            <button
                              type="button"
                              className="al-alert-title"
                              onClick={() => {
                                setSelectedId(alert.id);
                                setDetailsTab("details");
                              }}
                            >
                              <span className="al-alert-icon">
                                <AlertTriangle size={18} />
                              </span>
                              <span>
                                <strong>{alert.title}</strong>
                                <small>{alert.category}</small>
                              </span>
                            </button>
                          </td>

                          <td>
                            <SeverityBadge
                              severity={alert.severity}
                            />
                          </td>

                          <td>
                            <div className="al-identity">
                              <strong>{alert.employee}</strong>
                              <small>{alert.device}</small>
                            </div>
                          </td>

                          <td className="al-muted">
                            {relativeDate(alert.createdAt)}
                          </td>

                          <td>
                            <StatusBadge
                              status={alert.status}
                            />
                          </td>

                          <td>{alert.assignedTo}</td>

                          <td>
                            <button
                              type="button"
                              className="al-row-more"
                              aria-label={`View ${alert.title}`}
                              onClick={() => {
                                setSelectedId(alert.id);
                                setDetailsTab("details");
                              }}
                            >
                              <MoreHorizontal size={19} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {loading && (
                    <div className="al-empty">
                      <RefreshCw
                        size={27}
                        className="al-spin"
                      />
                      <strong>Loading alerts...</strong>
                    </div>
                  )}

                  {!loading && visible.length === 0 && (
                    <div className="al-empty">
                      <ShieldCheck size={33} />
                      <strong>
                        {alerts.length
                          ? "No matching alerts"
                          : "No monitoring alerts returned"}
                      </strong>
                      <p>
                        {alerts.length
                          ? "Try adjusting the severity, status, department or date filters."
                          : "The backend returned no monitoring alert events. This does not prove every monitoring subsystem is healthy."}
                      </p>
                    </div>
                  )}
                </div>

                <footer className="al-pagination">
                  <span>
                    {filtered.length === 0
                      ? 0
                      : (currentPage - 1) *
                          PAGE_SIZE +
                        1}
                    –
                    {Math.min(
                      currentPage * PAGE_SIZE,
                      filtered.length
                    )}{" "}
                    of {filtered.length}
                  </span>

                  <div>
                    <button
                      type="button"
                      aria-label="Previous page"
                      disabled={currentPage <= 1}
                      onClick={() =>
                        setPage((value) =>
                          Math.max(1, value - 1)
                        )
                      }
                    >
                      <ChevronLeft size={16} />
                    </button>

                    <span>
                      Page {currentPage} / {pages}
                    </span>

                    <button
                      type="button"
                      aria-label="Next page"
                      disabled={currentPage >= pages}
                      onClick={() =>
                        setPage((value) =>
                          Math.min(pages, value + 1)
                        )
                      }
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </footer>
              </section>

              <aside className="al-side">
                <section className="al-card al-detail">
                  <div className="al-card-heading">
                    <h2>
                      <AlertCircle size={21} />
                      Alert details
                    </h2>
                    {selected && (
                      <button
                        type="button"
                        className="al-icon-button"
                        aria-label="Clear selection"
                        onClick={() => setSelectedId(null)}
                      >
                        <X size={18} />
                      </button>
                    )}
                  </div>

                  {selected ? (
                    <>
                      <div className="al-detail-head">
                        <span className="al-detail-icon">
                          <ShieldAlert size={27} />
                        </span>

                        <div>
                          <h3>{selected.title}</h3>
                          <span>{selected.category}</span>
                        </div>
                      </div>

                      <div className="al-detail-badges">
                        <SeverityBadge
                          severity={selected.severity}
                        />
                        <StatusBadge
                          status={selected.status}
                        />
                      </div>

                      <div className="al-tabs">
                        <button
                          type="button"
                          className={
                            detailsTab === "details"
                              ? "al-tab-active"
                              : ""
                          }
                          onClick={() =>
                            setDetailsTab("details")
                          }
                        >
                          Details
                        </button>
                        <button
                          type="button"
                          className={
                            detailsTab === "activity"
                              ? "al-tab-active"
                              : ""
                          }
                          onClick={() =>
                            setDetailsTab("activity")
                          }
                        >
                          Event information
                        </button>
                      </div>

                      {detailsTab === "details" ? (
                        <>
                          <div className="al-description">
                            <h4>Description</h4>
                            <p>{selected.description}</p>
                          </div>

                          <dl className="al-facts">
                            <div>
                              <dt>Detected</dt>
                              <dd>
                                {formatDate(
                                  selected.createdAt
                                )}
                              </dd>
                            </div>
                            <div>
                              <dt>Employee</dt>
                              <dd>{selected.employee}</dd>
                            </div>
                            <div>
                              <dt>Device</dt>
                              <dd>{selected.device}</dd>
                            </div>
                            <div>
                              <dt>Department</dt>
                              <dd>{selected.department}</dd>
                            </div>
                            <div>
                              <dt>Assigned to</dt>
                              <dd>{selected.assignedTo}</dd>
                            </div>
                            <div>
                              <dt>Source</dt>
                              <dd>{selected.source}</dd>
                            </div>
                          </dl>

                          {selected.resolutionNotes && (
                            <div className="al-resolution">
                              <h4>Recorded resolution notes</h4>
                              <p>
                                {selected.resolutionNotes}
                              </p>
                            </div>
                          )}
                        </>
                      ) : (
                        <div className="al-event-info">
                          <div className="al-event-entry">
                            <span>
                              <Activity size={17} />
                            </span>
                            <div>
                              <strong>
                                Alert record detected
                              </strong>
                              <small>
                                {formatDate(
                                  selected.createdAt
                                )}
                              </small>
                            </div>
                          </div>

                          <div className="al-event-entry">
                            <span>
                              <Clock3 size={17} />
                            </span>
                            <div>
                              <strong>
                                Last reported update
                              </strong>
                              <small>
                                {formatDate(
                                  selected.updatedAt
                                )}
                              </small>
                            </div>
                          </div>

                          <div className="al-event-entry">
                            <span>
                              <Laptop2 size={17} />
                            </span>
                            <div>
                              <strong>Source identifiers</strong>
                              <small>
                                Employee:{" "}
                                {selected.employeeId || "—"}
                              </small>
                              <small>
                                Device:{" "}
                                {selected.deviceId || "—"}
                              </small>
                            </div>
                          </div>

                          <div className="al-event-note">
                            These entries summarize existing
                            alert fields, not a separate
                            verified audit history.
                          </div>
                        </div>
                      )}

                      <div className="al-actions-unavailable">
                        <Info size={17} />
                        <span>
                          Alert assignment, acknowledgment,
                          and resolution require backend
                          mutation endpoints. They are not
                          enabled in this page yet.
                        </span>
                      </div>
                    </>
                  ) : (
                    <div className="al-empty al-side-empty">
                      <Bell size={30} />
                      <strong>No alert selected</strong>
                      <p>
                        Choose an alert to inspect its
                        details.
                      </p>
                    </div>
                  )}
                </section>

                <section className="al-card">
                  <div className="al-card-heading">
                    <h2>
                      <Activity size={20} />
                      Recent alerts
                    </h2>
                  </div>

                  {recentAlerts.length ? (
                    <div className="al-recent-list">
                      {recentAlerts.map((alert) => (
                        <button
                          type="button"
                          key={alert.id}
                          className="al-recent-item"
                          onClick={() => {
                            setSelectedId(alert.id);
                            setDetailsTab("details");
                          }}
                        >
                          <span
                            className={`al-recent-icon al-recent-${alert.severity}`}
                          >
                            <AlertTriangle size={17} />
                          </span>

                          <span>
                            <strong>{alert.title}</strong>
                            <small>
                              {alert.employee} ·{" "}
                              {relativeDate(alert.createdAt)}
                            </small>
                          </span>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="al-recent-empty">
                      No recent alert records
                    </div>
                  )}
                </section>
              </aside>
            </div>

            <div className="al-data-note">
              <Info size={16} />
              This dashboard displays up to 100 alerts
              returned by the workspace monitoring-events
              endpoint. Counts and filters apply to that
              returned sample, not necessarily every
              historical alert.
              {snapshot?.generated_at &&
                ` Last refreshed ${formatDate(
                  snapshot.generated_at
                )}.`}
            </div>
          </>
        )}

        <style jsx global>{`
          .al-page {
            --al-text: #101c3a;
            --al-muted: #71809a;
            --al-line: #e6e9ed;
            background: #fbfaf8;
            color: var(--al-text);
            padding: 21px 21px 35px;
            min-height: 100%;
            font-size: 12px;
          }

          .al-page * {
            box-sizing: border-box;
          }

          .al-page button,
          .al-page input,
          .al-page select {
            font: inherit;
          }

          .al-page button {
            cursor: pointer;
          }

          .al-page button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
          }

          .al-page-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 20px;
          }

          .al-page-header h1 {
            margin: 0;
            font-size: 29px;
            font-weight: 750;
            line-height: 1.18;
            letter-spacing: -0.75px;
          }

          .al-page-header p {
            margin: 5px 0 0;
            color: var(--al-muted);
            font-size: 14px;
          }

          .al-header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
          }

          .al-btn {
            height: 38px;
            border-radius: 7px;
            padding: 0 14px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            white-space: nowrap;
            font-weight: 650 !important;
          }

          .al-btn-outline {
            background: white;
            border: 1px solid #dfe3e9;
            color: var(--al-text);
          }

          .al-btn-dark {
            background: #172431;
            border: 1px solid #172431;
            color: white;
          }

          .al-summary {
            display: grid;
            grid-template-columns:
              repeat(4, minmax(0, 1fr));
            gap: 13px;
            margin-bottom: 17px;
          }

          .al-metric {
            display: flex;
            align-items: center;
            gap: 15px;
            min-height: 111px;
            padding: 18px;
            border-radius: 11px;
            border: 1px solid #eae6de;
            background: #fffefa;
          }

          .al-metric-icon {
            height: 57px;
            width: 57px;
            border-radius: 50%;
            flex-shrink: 0;
            display: grid;
            place-items: center;
          }

          .al-tone-red {
            background: #ffe9e9;
            color: #f0474d;
          }

          .al-tone-orange {
            background: #fff0d8;
            color: #ef9328;
          }

          .al-tone-yellow {
            background: #fff5d8;
            color: #dda400;
          }

          .al-tone-blue {
            background: #e9f0ff;
            color: #4980e0;
          }

          .al-metric > div {
            display: flex;
            flex-direction: column;
            gap: 4px;
            min-width: 0;
          }

          .al-metric strong {
            font-size: 27px;
            letter-spacing: -0.7px;
            line-height: 1.1;
          }

          .al-metric div > span {
            font-size: 13px;
            font-weight: 700;
          }

          .al-metric small {
            color: var(--al-muted);
            font-size: 11px;
          }

          .al-toolbar {
            display: flex;
            align-items: center;
            gap: 9px;
            margin-bottom: 12px;
            flex-wrap: wrap;
          }

          .al-search {
            display: flex;
            align-items: center;
            gap: 10px;
            height: 40px;
            min-width: 225px;
            flex: 1 1 260px;
            padding: 0 12px;
            border: 1px solid #e1e5eb;
            background: white;
            border-radius: 8px;
            color: #74839b;
          }

          .al-search input {
            width: 100%;
            min-width: 0;
            background: transparent;
            border: 0;
            outline: 0;
            color: var(--al-text);
          }

          .al-filter-toggle,
          .al-time-filter {
            display: flex;
            align-items: center;
            gap: 9px;
            height: 40px;
            padding: 0 12px;
            border: 1px solid #e1e5eb;
            background: white;
            border-radius: 8px;
          }

          .al-time-filter select {
            background: transparent;
            color: var(--al-text);
            border: 0;
            outline: 0;
          }

          .al-clear {
            border: 0;
            background: transparent;
            color: #546681;
            text-decoration: underline;
            padding: 8px;
          }

          .al-filter-row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 15px;
            flex-wrap: wrap;
          }

          .al-filter-row label {
            display: flex;
            align-items: center;
            gap: 9px;
            color: #596a85;
          }

          .al-filter-row select {
            height: 37px;
            border: 1px solid #e0e4eb;
            background: white;
            border-radius: 7px;
            color: var(--al-text);
            padding: 0 10px;
          }

          .al-layout {
            display: grid;
            grid-template-columns:
              minmax(0, 1.72fr)
              minmax(330px, 0.87fr);
            align-items: start;
            gap: 15px;
          }

          .al-card {
            background: #fffefa;
            border: 1px solid var(--al-line);
            border-radius: 11px;
            overflow: hidden;
            min-width: 0;
          }

          .al-side {
            display: flex;
            flex-direction: column;
            gap: 14px;
            min-width: 0;
          }

          .al-card-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            min-height: 56px;
            padding: 12px 15px;
          }

          .al-card-heading h2 {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0;
            font-size: 17px;
            font-weight: 750;
            letter-spacing: -0.3px;
          }

          .al-card-heading > span {
            color: var(--al-muted);
          }

          .al-table-wrap {
            width: 100%;
            overflow-x: auto;
            min-height: 350px;
          }

          .al-table {
            width: 100%;
            min-width: 825px;
            border-collapse: collapse;
            text-align: left;
          }

          .al-table th {
            background: #f7f7f7;
            padding: 12px 10px;
            font-size: 10px;
            font-weight: 700;
            white-space: nowrap;
          }

          .al-table td {
            border-top: 1px solid #e9ebef;
            padding: 11px 10px;
            font-size: 11px;
            white-space: nowrap;
          }

          .al-table tr.al-row-selected {
            background: #fff6e6;
            outline: 1px solid #ffdb95;
            outline-offset: -1px;
          }

          .al-alert-title {
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--al-text);
            border: 0;
            background: transparent;
            padding: 0;
            text-align: left;
          }

          .al-alert-title > span:last-child,
          .al-identity {
            display: flex;
            flex-direction: column;
            gap: 5px;
          }

          .al-alert-title strong {
            max-width: 190px;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .al-alert-title small,
          .al-identity small {
            color: var(--al-muted);
          }

          .al-alert-icon {
            width: 34px;
            height: 34px;
            border-radius: 8px;
            display: grid;
            place-items: center;
            background: #fff1dc;
            color: #db8b00;
            flex-shrink: 0;
          }

          .al-severity,
          .al-status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            border-radius: 20px;
            white-space: nowrap;
            font-size: 11px;
            font-weight: 600;
          }

          .al-severity-dot,
          .al-status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
          }

          .al-severity-critical {
            background: #ffe2e4;
            color: #b52a37;
          }

          .al-severity-high {
            background: #ffeddf;
            color: #cb652a;
          }

          .al-severity-medium {
            background: #fff2d1;
            color: #ae7a00;
          }

          .al-severity-low {
            background: #e8f1ff;
            color: #386fb9;
          }

          .al-severity-unknown {
            background: #eff0f2;
            color: #788397;
          }

          .al-status-open {
            color: #bf533a;
            background: #fff0e6;
          }

          .al-status-acknowledged {
            color: #8e6b15;
            background: #fff4d8;
          }

          .al-status-resolved {
            color: #15824e;
            background: #def7e7;
          }

          .al-status-dismissed {
            color: #6d788b;
            background: #edf0f4;
          }

          .al-status-unknown {
            color: #778397;
            background: #edf0f4;
          }

          .al-muted {
            color: var(--al-muted);
          }

          .al-row-more {
            border: 0;
            background: transparent;
            color: #50617d;
          }

          .al-pagination {
            min-height: 63px;
            padding: 12px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            color: var(--al-muted);
          }

          .al-pagination > div {
            display: flex;
            align-items: center;
            gap: 9px;
          }

          .al-pagination button {
            width: 32px;
            height: 32px;
            display: grid;
            place-items: center;
            background: white;
            border: 1px solid #e4e7ed;
            border-radius: 7px;
          }

          .al-icon-button {
            border: 0;
            background: transparent;
            color: #596983;
          }

          .al-detail-head {
            padding: 4px 16px 12px;
            display: flex;
            align-items: center;
            gap: 12px;
          }

          .al-detail-icon {
            flex-shrink: 0;
            width: 49px;
            height: 49px;
            display: grid;
            place-items: center;
            color: #e68d27;
            background: #fff0da;
            border-radius: 10px;
          }

          .al-detail-head > div {
            min-width: 0;
          }

          .al-detail-head h3 {
            margin: 0;
            font-size: 16px;
            overflow-wrap: anywhere;
          }

          .al-detail-head div span {
            display: block;
            margin-top: 6px;
            color: var(--al-muted);
          }

          .al-detail-badges {
            display: flex;
            gap: 8px;
            padding: 0 16px 15px;
            flex-wrap: wrap;
          }

          .al-tabs {
            display: grid;
            grid-template-columns: 1fr 1fr;
            border-bottom: 1px solid #e7e9ed;
            padding: 0 15px;
          }

          .al-tabs button {
            border: 0;
            background: transparent;
            height: 41px;
            color: #718099;
          }

          .al-tabs .al-tab-active {
            border-bottom: 2px solid #ffb51d;
            font-weight: 700;
            color: var(--al-text);
          }

          .al-description {
            padding: 17px 16px 10px;
          }

          .al-description h4,
          .al-resolution h4 {
            font-size: 13px;
            margin: 0 0 9px;
          }

          .al-description p,
          .al-resolution p {
            color: #5d6e88;
            line-height: 1.6;
            margin: 0;
            overflow-wrap: anywhere;
          }

          .al-facts {
            margin: 0 16px;
            border-top: 1px solid #ebedf0;
            padding: 9px 0 13px;
          }

          .al-facts > div {
            display: grid;
            grid-template-columns: 1fr 1.15fr;
            gap: 10px;
            padding: 9px 0;
          }

          .al-facts dt {
            color: var(--al-muted);
          }

          .al-facts dd {
            margin: 0;
            font-weight: 650;
            overflow-wrap: anywhere;
          }

          .al-resolution {
            padding: 14px 16px;
            border-top: 1px solid #ebedf0;
          }

          .al-event-info {
            padding: 16px;
          }

          .al-event-entry {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px 0;
            border-bottom: 1px solid #e9ecf0;
          }

          .al-event-entry > span {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #fff1d5;
            display: grid;
            place-items: center;
            flex-shrink: 0;
          }

          .al-event-entry > div {
            display: flex;
            flex-direction: column;
            gap: 6px;
          }

          .al-event-entry small {
            color: var(--al-muted);
            overflow-wrap: anywhere;
          }

          .al-event-note {
            margin-top: 14px;
            color: var(--al-muted);
            line-height: 1.6;
          }

          .al-actions-unavailable {
            display: flex;
            align-items: flex-start;
            gap: 9px;
            padding: 12px;
            margin: 0 15px 16px;
            background: #f3f6fa;
            border: 1px solid #e1e7ef;
            color: #687994;
            border-radius: 8px;
            line-height: 1.6;
          }

          .al-actions-unavailable svg {
            flex-shrink: 0;
          }

          .al-recent-list {
            padding: 0 12px 12px;
          }

          .al-recent-item {
            display: flex;
            align-items: center;
            gap: 11px;
            width: 100%;
            padding: 12px 8px;
            background: transparent;
            border: 0;
            border-bottom: 1px solid #edf0f2;
            text-align: left;
            color: var(--al-text);
          }

          .al-recent-item:last-child {
            border-bottom: 0;
          }

          .al-recent-item > span:last-child {
            display: flex;
            flex-direction: column;
            gap: 5px;
            min-width: 0;
          }

          .al-recent-item strong {
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .al-recent-item small {
            color: var(--al-muted);
          }

          .al-recent-icon {
            flex-shrink: 0;
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: #f0f2f5;
            color: #67758e;
          }

          .al-recent-critical,
          .al-recent-high {
            background: #ffe8e4;
            color: #e25745;
          }

          .al-recent-medium {
            background: #fff1d5;
            color: #d99a09;
          }

          .al-recent-low {
            background: #e8f1ff;
            color: #4d86de;
          }

          .al-recent-empty {
            color: var(--al-muted);
            padding: 22px 16px;
            text-align: center;
          }

          .al-empty {
            min-height: 275px;
            display: flex;
            align-items: center;
            flex-direction: column;
            justify-content: center;
            gap: 12px;
            color: #8795aa;
            padding: 25px;
            text-align: center;
          }

          .al-empty strong {
            color: var(--al-text);
          }

          .al-empty p {
            margin: 0;
            max-width: 310px;
            line-height: 1.6;
          }

          .al-side-empty {
            min-height: 290px;
          }

          .al-data-note {
            color: var(--al-muted);
            display: flex;
            align-items: flex-start;
            gap: 9px;
            line-height: 1.6;
            margin-top: 15px;
          }

          .al-data-note svg {
            flex-shrink: 0;
            margin-top: 2px;
          }

          .al-error {
            color: #b62f31;
            background: #fff0f0;
            border: 1px solid #f1baba;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 12px 14px;
            margin-bottom: 15px;
          }

          .al-error span {
            flex: 1;
          }

          .al-error button {
            background: white;
            border: 1px solid #eeb8b8;
            border-radius: 6px;
            padding: 6px 10px;
          }

          .al-spin {
            animation: al-spin 1s linear infinite;
          }

          @keyframes al-spin {
            to {
              transform: rotate(360deg);
            }
          }

          @media (max-width: 1250px) {
            .al-layout {
              grid-template-columns: 1fr;
            }

            .al-side {
              display: grid;
              grid-template-columns:
                repeat(2, minmax(0, 1fr));
            }
          }

          @media (max-width: 950px) {
            .al-summary {
              grid-template-columns:
                repeat(2, minmax(0, 1fr));
            }

            .al-side {
              grid-template-columns: 1fr;
            }
          }

          @media (max-width: 720px) {
            .al-page-header {
              flex-direction: column;
              align-items: flex-start;
            }
          }

          @media (max-width: 520px) {
            .al-page {
              padding: 15px 12px 25px;
            }

            .al-page-header h1 {
              font-size: 24px;
            }

            .al-summary {
              grid-template-columns: 1fr;
            }

            .al-filter-row label {
              width: 100%;
              justify-content: space-between;
            }

            .al-filter-row select {
              flex: 1;
              max-width: 230px;
            }
          }
        `}</style>
      </main>
    </WorkspaceRequired>
  );
}
