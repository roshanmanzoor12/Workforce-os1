
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
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock3,
  Laptop2,
  LineChart,
  Monitor,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  Users,
  Wifi,
  WifiOff,
} from "lucide-react";

import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";
import {
  monitoringService,
  type MonitoringSnapshot,
} from "@/services/monitoring.service";

type RecordItem = Record<string, unknown>;
type Status = "online" | "idle" | "offline" | "unavailable";
type Period = "today" | "7days" | "30days";

interface MonitoringData {
  overview: MonitoringSnapshot | null;
  employees: MonitoringSnapshot | null;
  devices: MonitoringSnapshot | null;
  alerts: MonitoringSnapshot | null;
  activity: MonitoringSnapshot | null;
}

const EMPTY_DATA: MonitoringData = {
  overview: null,
  employees: null,
  devices: null,
  alerts: null,
  activity: null,
};

const COLORS = {
  online: "#2fba76",
  idle: "#ffbf29",
  offline: "#ff5454",
  unavailable: "#929baa",
};

const STATUS_LABELS: Record<Status, string> = {
  online: "Online",
  idle: "Idle",
  offline: "Offline",
  unavailable: "Unavailable",
};

const STATUS_COLORS: Record<Status, string> = COLORS;

function items(snapshot: MonitoringSnapshot | null): RecordItem[] {
  return Array.isArray(snapshot?.items) ? snapshot.items : [];
}

function text(value: unknown, fallback = "—"): string {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }

  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }

  return fallback;
}

function number(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return Math.max(0, value);
  }

  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);

    if (Number.isFinite(parsed)) {
      return Math.max(0, parsed);
    }
  }

  return null;
}

function summaryNumber(
  summary: Record<string, number | string> | undefined,
  ...keys: string[]
): number | null {
  for (const key of keys) {
    const result = number(summary?.[key]);

    if (result !== null) {
      return result;
    }
  }

  return null;
}

function statusOf(row: RecordItem): Status {
  const value = text(
    row.status ?? row.presence ?? row.monitoring_status,
    "unavailable",
  ).toLowerCase();

  if (["online", "active", "connected"].includes(value)) {
    return "online";
  }

  if (["idle", "away", "inactive"].includes(value)) {
    return "idle";
  }

  if (["offline", "disconnected"].includes(value)) {
    return "offline";
  }

  return "unavailable";
}

function dateText(value: unknown): string {
  if (typeof value !== "string") {
    return "No signal";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value || "No signal";
  }

  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function countText(value: number | null): string {
  return value === null ? "—" : value.toLocaleString();
}

function percent(part: number | null, total: number | null): string {
  if (part === null || total === null || total <= 0) {
    return "—";
  }

  return `${((part / total) * 100).toFixed(1)}%`;
}

function StatusDot({ status }: { status: Status }) {
  return (
    <span
      className="wmo-status-dot"
      style={{ backgroundColor: STATUS_COLORS[status] }}
      aria-hidden="true"
    />
  );
}

function EmptyArea({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="wmo-empty">
      <CheckCircle2 size={27} strokeWidth={1.8} />
      <strong>{title}</strong>
      <span>{description}</span>
    </div>
  );
}

export default function MonitoringOverviewPage() {
  const { workspaceId, permissions, navigationView } = useWorkspace();

  const allowed = hasAnyPermission(
    permissions,
    [
      "monitoring.all.read",
      "monitoring.team.read",
      "monitoring.self.read",
    ],
    navigationView,
  );

  const [data, setData] = useState<MonitoringData>(EMPTY_DATA);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [period, setPeriod] = useState<Period>("today");
  const [department, setDepartment] = useState("all");
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  const load = useCallback(
    async (background = false) => {
      if (!workspaceId || !allowed) {
        setLoading(false);
        setRefreshing(false);
        return;
      }

      if (background) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const jobs = [
        monitoringService.overview(workspaceId),
        monitoringService.employees(workspaceId),
        monitoringService.devices(workspaceId),
        monitoringService.alerts(workspaceId),
        monitoringService.activity(workspaceId),
      ];

      const results = await Promise.allSettled(jobs);

      const get = (index: number): MonitoringSnapshot | null => {
        const result = results[index];

        return result?.status === "fulfilled" ? result.value : null;
      };

      const next: MonitoringData = {
        overview: get(0),
        employees: get(1),
        devices: get(2),
        alerts: get(3),
        activity: get(4),
      };

      setData(next);

      const failures = results.filter(
        (result) => result.status === "rejected",
      );

      if (failures.length === results.length) {
        const first = failures[0];

        const message =
          first?.status === "rejected" &&
          first.reason instanceof Error
            ? first.reason.message
            : "Monitoring service is unavailable.";

        setError(message);
      } else if (failures.length > 0) {
        setError(
          "Some monitoring sections could not be loaded. Available records are shown.",
        );
      } else {
        setError("");
      }

      setUpdatedAt(new Date());
      setLoading(false);
      setRefreshing(false);
    },
    [workspaceId, allowed],
  );

  useEffect(() => {
    setData(EMPTY_DATA);
    setUpdatedAt(null);

    if (!workspaceId || !allowed) {
      setLoading(false);
      return;
    }

    void load();

    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void load(true);
      }
    }, 30000);

    return () => window.clearInterval(timer);
  }, [workspaceId, allowed, load]);

  const employees = useMemo(
    () => items(data.employees),
    [data.employees],
  );

  const devices = useMemo(
    () => items(data.devices),
    [data.devices],
  );

  const alerts = useMemo(
    () => items(data.alerts),
    [data.alerts],
  );

  const activity = useMemo(
    () => items(data.activity),
    [data.activity],
  );

  const departments = useMemo(() => {
    const names = employees
      .map((row) => text(row.department, ""))
      .filter(Boolean);

    return Array.from(new Set(names)).sort();
  }, [employees]);

  const filteredEmployees = useMemo(() => {
    const search = query.trim().toLowerCase();

    return employees.filter((row) => {
      const matchesDepartment =
        department === "all" ||
        text(row.department) === department;

      const matchesSearch =
        !search ||
        [
          row.name,
          row.employee,
          row.employee_name,
          row.department,
          row.device,
          row.device_name,
        ]
          .map((value) => text(value, "").toLowerCase())
          .some((value) => value.includes(search));

      return matchesDepartment && matchesSearch;
    });
  }, [employees, department, query]);

  const summary = data.overview?.summary;

  const total =
    summaryNumber(summary, "employees", "total_employees") ??
    (data.employees ? employees.length : null);

  const online =
    summaryNumber(summary, "online", "online_employees") ??
    (data.employees
      ? employees.filter((row) => statusOf(row) === "online").length
      : null);

  const idle =
    summaryNumber(summary, "idle", "idle_employees") ??
    (data.employees
      ? employees.filter((row) => statusOf(row) === "idle").length
      : null);

  const offline =
    summaryNumber(summary, "offline", "offline_employees") ??
    (data.employees
      ? employees.filter((row) => statusOf(row) === "offline").length
      : null);

  const deviceTotal = data.devices ? devices.length : null;

  const deviceReady = data.devices
    ? devices.filter((row) =>
        ["connected", "ready", "online", "active"].includes(
          text(row.agent_status ?? row.status, "").toLowerCase(),
        ),
      ).length
    : null;

  const deviceUpdates = data.devices
    ? devices.filter((row) =>
        ["outdated", "update_required", "needs_update"].includes(
          text(row.agent_status ?? row.status, "").toLowerCase(),
        ),
      ).length
    : null;

  const liveReady = data.devices
    ? devices.filter((row) =>
        row.live_ready === true ||
        row.live_available === true ||
        row.live_screen_available === true,
      ).length
    : null;

  const deviceUnavailable =
    deviceTotal !== null && deviceReady !== null
      ? Math.max(
          0,
          deviceTotal - deviceReady - (deviceUpdates ?? 0),
        )
      : null;

  const alertTotal =
    summaryNumber(data.alerts?.summary, "total", "alerts") ??
    (data.alerts ? number(data.alerts.total) ?? alerts.length : null);

  const recentAlerts = alerts.slice(0, 3);

  const trend = useMemo(() => {
    const rows = activity
      .map((row) => {
        const date = new Date(
          text(row.captured_at ?? row.started_at, ""),
        );

        if (Number.isNaN(date.getTime())) {
          return null;
        }

        return {
          date,
          status: statusOf(row),
        };
      })
      .filter(
        (
          row,
        ): row is { date: Date; status: Status } => row !== null,
      );

    const now = updatedAt ?? new Date();

    const start = new Date(now);

    if (period === "today") {
      start.setHours(0, 0, 0, 0);
    } else {
      start.setDate(start.getDate() - (period === "7days" ? 7 : 30));
    }

    const buckets = new Map<
      string,
      { label: string; online: number; idle: number; offline: number }
    >();

    rows
      .filter((row) => row.date >= start && row.date <= now)
      .forEach(({ date, status }) => {
        const key =
          period === "today"
            ? `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}`
            : `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;

        const label =
          period === "today"
            ? date.toLocaleTimeString([], {
                hour: "numeric",
              })
            : date.toLocaleDateString([], {
                month: "short",
                day: "numeric",
              });

        const bucket = buckets.get(key) ?? {
          label,
          online: 0,
          idle: 0,
          offline: 0,
        };

        if (status !== "unavailable") {
          bucket[status]++;
        }

        buckets.set(key, bucket);
      });

    return Array.from(buckets.values()).slice(-12);
  }, [activity, period, updatedAt]);

  const chartMaximum = Math.max(
    1,
    ...trend.map(
      (point) => point.online + point.idle + point.offline,
    ),
  );

  const summaryCards = [
    {
      label: "Employees",
      value: total,
      detail: "Total employees",
      icon: Users,
      status: null,
    },
    {
      label: "Online",
      value: online,
      detail: `${percent(online, total)} of employees`,
      icon: Wifi,
      status: "online" as Status,
    },
    {
      label: "Idle",
      value: idle,
      detail: `${percent(idle, total)} of employees`,
      icon: Clock3,
      status: "idle" as Status,
    },
    {
      label: "Offline",
      value: offline,
      detail: `${percent(offline, total)} of employees`,
      icon: WifiOff,
      status: "offline" as Status,
    },
  ];

  return (
    <WorkspaceRequired>
      <main className="wmo">
        <header className="wmo-heading">
          <div>
            <h1>Monitoring Overview</h1>
            <p>
              Device and employee monitoring status across your
              organization.
            </p>
          </div>

          <div className="wmo-heading-actions">
            <div className="wmo-date">
              <CalendarDays size={17} />
              <span>
                {updatedAt
                  ? updatedAt.toLocaleDateString("en-GB", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })
                  : "—"}
              </span>
            </div>

            <label className="wmo-select-wrap">
              <select
                aria-label="Monitoring period"
                value={period}
                onChange={(event) =>
                  setPeriod(event.target.value as Period)
                }
              >
                <option value="today">Today</option>
                <option value="7days">Last 7 days</option>
                <option value="30days">Last 30 days</option>
              </select>
              <ChevronDown size={15} />
            </label>

            <label className="wmo-select-wrap wmo-department">
              <select
                aria-label="Department"
                value={department}
                onChange={(event) =>
                  setDepartment(event.target.value)
                }
              >
                <option value="all">Company (All departments)</option>
                {departments.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
              <ChevronDown size={15} />
            </label>

            <Link
              href="/monitoring/alerts"
              className="wmo-dark-button"
            >
              <Settings2 size={17} />
              Monitoring
            </Link>
          </div>
        </header>

        {!allowed ? (
          <div className="wmo-error" role="alert">
            <AlertTriangle size={19} />
            You do not have permission to view workspace monitoring
            records.
          </div>
        ) : (
          <>
            {error && (
              <div className="wmo-error" role="alert">
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

            <section
              className="wmo-summary"
              aria-label="Employee presence summary"
            >
              {summaryCards.map((card) => {
                const Icon = card.icon;

                return (
                  <article className="wmo-summary-item" key={card.label}>
                    <Icon size={33} strokeWidth={1.7} />

                    <div>
                      <div className="wmo-summary-value">
                        {card.status && (
                          <StatusDot status={card.status} />
                        )}
                        <strong>{countText(card.value)}</strong>
                      </div>

                      <b>{card.label}</b>
                      <span>{card.detail}</span>
                    </div>
                  </article>
                );
              })}
            </section>

            <section className="wmo-health">
              <article className="wmo-card wmo-health-card">
                <span className="wmo-circle">
                  <ShieldCheck size={35} />
                </span>

                <div>
                  <h2>
                    Monitoring ready
                    <span title="Connected monitoring agents">
                      <CheckCircle2 size={15} />
                    </span>
                  </h2>

                  <strong>
                    {countText(deviceReady)}/{countText(deviceTotal)}
                  </strong>

                  <b>devices</b>
                  <p>{percent(deviceReady, deviceTotal)} ready</p>
                </div>
              </article>

              <article className="wmo-card wmo-health-card">
                <span className="wmo-circle">
                  <Laptop2 size={35} />
                </span>

                <div>
                  <h2>
                    Live ready
                    <span title="Devices reporting live-screen availability">
                      <CheckCircle2 size={15} />
                    </span>
                  </h2>

                  <strong>
                    {countText(liveReady)}/{countText(deviceTotal)}
                  </strong>

                  <b>devices</b>
                  <p>
                    {percent(liveReady, deviceTotal)} available
                  </p>
                </div>
              </article>

              <article className="wmo-card wmo-health-card">
                <span className="wmo-circle wmo-warning-circle">
                  <AlertTriangle size={35} />
                </span>

                <div>
                  <h2>Alerts</h2>
                  <strong className="wmo-danger">
                    {countText(alertTotal)}
                  </strong>
                  <b>total</b>
                  <p>Require attention</p>
                </div>
              </article>

              <article className="wmo-card wmo-readiness">
                <div className="wmo-panel-heading">
                  <h2>
                    <Monitor size={22} />
                    Device readiness
                  </h2>
                  <Link href="/monitoring/devices">
                    View all <ArrowRight size={16} />
                  </Link>
                </div>

                {[
                  {
                    label: "Agent connected",
                    value: deviceReady,
                    color: COLORS.online,
                  },
                  {
                    label: "Updates required",
                    value: deviceUpdates,
                    color: COLORS.idle,
                  },
                  {
                    label: "Unavailable",
                    value: deviceUnavailable,
                    color: COLORS.unavailable,
                  },
                ].map((item) => (
                  <div className="wmo-readiness-row" key={item.label}>
                    <span
                      className="wmo-dot"
                      style={{ background: item.color }}
                    />
                    <span>{item.label}</span>
                    <strong>{countText(item.value)}</strong>
                    <small>{percent(item.value, deviceTotal)}</small>
                  </div>
                ))}
              </article>
            </section>

            <section className="wmo-card wmo-trend">
              <div className="wmo-panel-heading">
                <h2>
                  <LineChart size={23} />
                  Employee status trend
                </h2>

                <div className="wmo-chart-controls">
                  <div className="wmo-legend">
                    {(
                      ["online", "idle", "offline"] as Status[]
                    ).map((status) => (
                      <span key={status}>
                        <StatusDot status={status} />
                        {STATUS_LABELS[status]}
                      </span>
                    ))}
                  </div>

                  <label className="wmo-select-wrap">
                    <select
                      aria-label="Chart time period"
                      value={period}
                      onChange={(event) =>
                        setPeriod(event.target.value as Period)
                      }
                    >
                      <option value="today">Today</option>
                      <option value="7days">7 days</option>
                      <option value="30days">30 days</option>
                    </select>
                    <ChevronDown size={15} />
                  </label>
                </div>
              </div>

              {trend.length > 0 ? (
                <div className="wmo-chart">
                  <div className="wmo-chart-axis">
                    {[100, 75, 50, 25, 0].map((value) => (
                      <span key={value}>
                        {Math.round((chartMaximum * value) / 100)}
                      </span>
                    ))}
                  </div>

                  <div className="wmo-chart-plot">
                    <div className="wmo-chart-grid">
                      {[0, 1, 2, 3, 4].map((line) => (
                        <span key={line} />
                      ))}
                    </div>

                    <div className="wmo-bars">
                      {trend.map((point, index) => (
                        <div className="wmo-bar-column" key={index}>
                          <div
                            className="wmo-bar"
                            title={`${point.label}: ${point.online} online, ${point.idle} idle, ${point.offline} offline`}
                          >
                            <span
                              style={{
                                height: `${
                                  (point.online / chartMaximum) * 100
                                }%`,
                                background: COLORS.online,
                              }}
                            />
                            <span
                              style={{
                                height: `${
                                  (point.idle / chartMaximum) * 100
                                }%`,
                                background: COLORS.idle,
                              }}
                            />
                            <span
                              style={{
                                height: `${
                                  (point.offline / chartMaximum) * 100
                                }%`,
                                background: COLORS.offline,
                              }}
                            />
                          </div>
                          <small>{point.label}</small>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <EmptyArea
                  title="No trend data available"
                  description="Status history will appear when authorized monitoring events are received."
                />
              )}
            </section>

            <section className="wmo-bottom-grid">
              <article className="wmo-card wmo-employees">
                <div className="wmo-panel-heading wmo-table-heading">
                  <h2>
                    <Users size={21} />
                    Employee monitoring status
                  </h2>

                  <div className="wmo-filters">
                    <label className="wmo-search">
                      <Search size={16} />
                      <input
                        value={query}
                        onChange={(event) =>
                          setQuery(event.target.value)
                        }
                        placeholder="Search employees..."
                        aria-label="Search employees"
                      />
                    </label>

                    <label className="wmo-select-wrap">
                      <select
                        aria-label="Filter employee department"
                        value={department}
                        onChange={(event) =>
                          setDepartment(event.target.value)
                        }
                      >
                        <option value="all">All departments</option>
                        {departments.map((name) => (
                          <option key={name} value={name}>
                            {name}
                          </option>
                        ))}
                      </select>
                      <ChevronDown size={15} />
                    </label>
                  </div>
                </div>

                {filteredEmployees.length > 0 ? (
                  <div className="wmo-table-scroll">
                    <table className="wmo-table">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Department</th>
                          <th>Device</th>
                          <th>Status</th>
                          <th>Last signal</th>
                          <th>Actions</th>
                        </tr>
                      </thead>

                      <tbody>
                        {filteredEmployees.slice(0, 10).map((row, index) => {
                          const status = statusOf(row);

                          return (
                            <tr key={text(row.id, String(index))}>
                              <td className="wmo-name">
                                {text(
                                  row.name ??
                                    row.employee_name ??
                                    row.employee,
                                )}
                              </td>

                              <td>{text(row.department)}</td>

                              <td>
                                {text(
                                  row.device ??
                                    row.device_name ??
                                    row.platform,
                                )}
                              </td>

                              <td>
                                <span className="wmo-status">
                                  <StatusDot status={status} />
                                  {STATUS_LABELS[status]}
                                </span>
                              </td>

                              <td>
                                {dateText(
                                  row.last_signal ??
                                    row.last_heartbeat ??
                                    row.last_seen,
                                )}
                              </td>

                              <td>
                                <Link
                                  className="wmo-detail-button"
                                  href="/monitoring/employees"
                                >
                                  View details
                                  <ChevronRight size={15} />
                                </Link>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyArea
                    title={
                      loading
                        ? "Loading monitoring records"
                        : "No monitoring records returned"
                    }
                    description="Connect an authorized agent or adjust your filters to view employee monitoring."
                  />
                )}
              </article>

              <article className="wmo-card wmo-alerts">
                <div className="wmo-panel-heading">
                  <h2>
                    <AlertTriangle size={22} color="#ff3c38" />
                    Alerts and issues
                  </h2>

                  <Link href="/monitoring/alerts">
                    View all <ArrowRight size={16} />
                  </Link>
                </div>

                {recentAlerts.length > 0 ? (
                  recentAlerts.map((alert, index) => {
                    const severity = text(
                      alert.severity,
                      "warning",
                    ).toLowerCase();

                    const color =
                      severity === "critical" ||
                      severity === "high"
                        ? COLORS.offline
                        : COLORS.idle;

                    return (
                      <div
                        className="wmo-alert-row"
                        key={text(alert.id, String(index))}
                      >
                        <span
                          className="wmo-dot"
                          style={{ background: color }}
                        />

                        <div>
                          <strong>
                            {text(
                              alert.title ??
                                alert.message ??
                                alert.type,
                              "Monitoring alert")}
                          </strong>

                          <p>
                            {text(
                              alert.description ??
                                alert.details ??
                                alert.status,
                              "Review this monitoring event.",
                            )}
                          </p>
                        </div>

                        <ChevronRight size={17} />
                      </div>
                    );
                  })
                ) : (
                  <EmptyArea
                    title="No alerts returned"
                    description="Monitoring alerts will appear here when reported by the backend."
                  />
                )}
              </article>
            </section>

            <footer className="wmo-footer">
              <span>
                <Activity size={14} />
                {updatedAt
                  ? `Last refreshed ${updatedAt.toLocaleTimeString()}`
                  : "Awaiting monitoring data"}
              </span>

              <button
                type="button"
                onClick={() => void load(true)}
                disabled={refreshing || loading}
              >
                <RefreshCw
                  size={14}
                  className={refreshing ? "wmo-spin" : ""}
                />
                {refreshing ? "Refreshing..." : "Refresh data"}
              </button>
            </footer>
          </>
        )}

        <style jsx global>{`
          .wmo {
            --wmo-text: #0c1935;
            --wmo-muted: #687994;
            --wmo-border: #e8e5de;
            width: 100%;
            min-width: 0;
            min-height: 100%;
            padding: 18px 20px 22px;
            background: #fbfaf7;
            color: var(--wmo-text);
            font-size: 13px;
          }

          .wmo-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 18px;
          }

          .wmo-heading h1 {
            font-size: 27px;
            line-height: 1.2;
            font-weight: 700;
            letter-spacing: -0.8px;
          }

          .wmo-heading p {
            margin-top: 4px;
            color: var(--wmo-muted);
            font-size: 14px;
          }

          .wmo-heading-actions,
          .wmo-chart-controls,
          .wmo-filters {
            display: flex;
            align-items: center;
            gap: 12px;
          }

          .wmo-date {
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--wmo-muted);
            white-space: nowrap;
          }

          .wmo-select-wrap {
            position: relative;
            display: inline-flex;
            align-items: center;
            min-width: 95px;
            height: 36px;
            background: #fff;
            border: 1px solid #dedfe3;
            border-radius: 8px;
          }

          .wmo-select-wrap select {
            width: 100%;
            height: 100%;
            padding: 0 33px 0 13px;
            appearance: none;
            border: 0;
            background: transparent;
            color: var(--wmo-text);
            font-size: 12px;
            cursor: pointer;
          }

          .wmo-select-wrap > svg {
            position: absolute;
            right: 11px;
            pointer-events: none;
            color: #61728b;
          }

          .wmo-department {
            min-width: 205px;
          }

          .wmo-dark-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 9px;
            min-height: 36px;
            padding: 0 15px;
            border-radius: 7px;
            background: #1b2936;
            color: #fff;
            font-weight: 600;
            font-size: 12px;
            white-space: nowrap;
          }

          .wmo-summary {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            min-height: 94px;
            margin-bottom: 15px;
            padding: 14px 0;
            border: 1px solid #f0e7d6;
            border-radius: 13px;
            background: linear-gradient(110deg, #fffaf0, #fffcf7);
          }

          .wmo-summary-item {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 23px;
            min-width: 0;
            padding: 0 15px;
            border-right: 1px solid #eee6db;
          }

          .wmo-summary-item:last-child {
            border-right: 0;
          }

          .wmo-summary-item > svg {
            flex-shrink: 0;
          }

          .wmo-summary-item > div {
            display: flex;
            flex-direction: column;
          }

          .wmo-summary-value {
            display: flex;
            align-items: center;
            gap: 10px;
          }

          .wmo-summary-value strong {
            font-size: 25px;
            line-height: 1;
            font-weight: 700;
          }

          .wmo-summary-item b {
            margin-top: 3px;
            font-size: 12px;
          }

          .wmo-summary-item > div > span {
            margin-top: 4px;
            color: var(--wmo-muted);
            font-size: 12px;
          }

          .wmo-status-dot,
          .wmo-dot {
            display: inline-block;
            width: 11px;
            height: 11px;
            flex: 0 0 11px;
            border-radius: 50%;
          }

          .wmo-card {
            min-width: 0;
            overflow: hidden;
            border: 1px solid var(--wmo-border);
            border-radius: 12px;
            background: #fffdfa;
          }

          .wmo-health {
            display: grid;
            grid-template-columns: 1.05fr 0.95fr 0.88fr 1.58fr;
            gap: 13px;
            margin-bottom: 14px;
          }

          .wmo-health-card {
            display: flex;
            align-items: flex-start;
            gap: 14px;
            min-height: 139px;
            padding: 19px 14px;
          }

          .wmo-circle {
            display: grid;
            width: 65px;
            height: 65px;
            flex: 0 0 65px;
            place-items: center;
            border-radius: 50%;
            background: #fff0c6;
            color: #a66c00;
          }

          .wmo-warning-circle {
            color: #f03232;
          }

          .wmo-health-card h2 {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 1px 0 8px;
            font-size: 12px;
            font-weight: 650;
            white-space: nowrap;
          }

          .wmo-health-card h2 span {
            color: #687994;
          }

          .wmo-health-card strong {
            display: block;
            font-size: 27px;
            font-weight: 700;
            line-height: 1.05;
            letter-spacing: -0.6px;
          }

          .wmo-health-card b {
            display: block;
            margin-top: 3px;
            font-size: 12px;
            font-weight: 500;
          }

          .wmo-health-card p {
            margin-top: 7px;
            color: var(--wmo-muted);
            font-size: 12px;
          }

          .wmo-danger {
            color: #e52f31;
          }

          .wmo-readiness {
            padding: 13px 16px;
          }

          .wmo-panel-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
          }

          .wmo-panel-heading h2 {
            display: flex;
            align-items: center;
            gap: 11px;
            min-width: 0;
            font-size: 15px;
            font-weight: 700;
          }

          .wmo-panel-heading > a {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #d48d00;
            font-size: 12px;
            white-space: nowrap;
          }

          .wmo-readiness .wmo-panel-heading {
            padding-bottom: 10px;
            border-bottom: 1px solid var(--wmo-border);
          }

          .wmo-readiness-row {
            display: grid;
            grid-template-columns: 12px minmax(0, 1fr) 35px 50px;
            align-items: center;
            gap: 9px;
            padding: 8px 4px;
            border-bottom: 1px solid #eeece8;
            font-size: 12px;
          }

          .wmo-readiness-row:last-child {
            border-bottom: 0;
          }

          .wmo-readiness-row strong {
            text-align: right;
          }

          .wmo-readiness-row small {
            color: var(--wmo-muted);
            text-align: right;
          }

          .wmo-trend {
            min-height: 229px;
            margin-bottom: 14px;
            padding: 13px 15px 17px;
          }

          .wmo-trend > .wmo-panel-heading {
            margin-bottom: 18px;
          }

          .wmo-legend {
            display: flex;
            align-items: center;
            gap: 21px;
            margin-right: 24px;
          }

          .wmo-legend > span {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #42546d;
            font-size: 12px;
          }

          .wmo-chart {
            display: flex;
            height: 155px;
            gap: 12px;
          }

          .wmo-chart-axis {
            display: flex;
            width: 23px;
            flex-direction: column;
            justify-content: space-between;
            align-items: flex-end;
            padding-bottom: 22px;
            color: #60718a;
            font-size: 11px;
          }

          .wmo-chart-plot {
            position: relative;
            min-width: 0;
            flex: 1;
          }

          .wmo-chart-grid {
            position: absolute;
            inset: 0 0 22px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
          }

          .wmo-chart-grid span {
            width: 100%;
            border-top: 1px dashed #e3e5e8;
          }

          .wmo-bars {
            position: relative;
            z-index: 1;
            display: flex;
            justify-content: space-around;
            gap: 8px;
            height: 100%;
          }

          .wmo-bar-column {
            display: flex;
            min-width: 0;
            flex: 1;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
          }

          .wmo-bar {
            display: flex;
            width: min(46px, 76%);
            height: calc(100% - 22px);
            flex-direction: column-reverse;
            justify-content: flex-start;
          }

          .wmo-bar span {
            display: block;
            width: 100%;
            flex-shrink: 0;
          }

          .wmo-bar-column small {
            display: flex;
            height: 22px;
            align-items: flex-end;
            color: #485b77;
            font-size: 10px;
            white-space: nowrap;
          }

          .wmo-bottom-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.88fr) minmax(290px, 1fr);
            gap: 14px;
          }

          .wmo-employees,
          .wmo-alerts {
            min-height: 280px;
          }

          .wmo-table-heading {
            min-height: 49px;
            padding: 10px 15px;
          }

          .wmo-filters {
            gap: 9px;
          }

          .wmo-search {
            display: flex;
            align-items: center;
            gap: 8px;
            width: 175px;
            height: 32px;
            padding: 0 10px;
            border: 1px solid #dfe2e7;
            border-radius: 7px;
            color: #71819b;
            background: #fff;
          }

          .wmo-search input {
            width: 100%;
            min-width: 0;
            border: 0;
            outline: 0;
            background: transparent;
            color: var(--wmo-text);
            font-size: 11px;
          }

          .wmo-filters .wmo-select-wrap {
            height: 32px;
          }

          .wmo-table-scroll {
            width: 100%;
            overflow-x: auto;
          }

          .wmo-table {
            width: 100%;
            min-width: 690px;
            border-collapse: collapse;
          }

          .wmo-table th {
            height: 30px;
            padding: 6px 14px;
            background: #f6f5f2;
            color: #17233d;
            font-size: 11px;
            font-weight: 500;
            text-align: left;
          }

          .wmo-table td {
            height: 30px;
            padding: 5px 14px;
            border-top: 1px solid #ebe9e5;
            color: #4b5b73;
            font-size: 11px;
            white-space: nowrap;
          }

          .wmo-table .wmo-name {
            color: var(--wmo-text);
            font-weight: 600;
          }

          .wmo-status {
            display: inline-flex;
            align-items: center;
            gap: 7px;
          }

          .wmo-status .wmo-status-dot {
            width: 9px;
            height: 9px;
            flex-basis: 9px;
          }

          .wmo-detail-button {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 5px 10px;
            border: 1px solid #dee0e4;
            border-radius: 6px;
            background: #fff;
            color: #17233d;
            font-size: 11px;
          }

          .wmo-alerts {
            padding: 13px 15px;
          }

          .wmo-alerts .wmo-panel-heading {
            padding-bottom: 14px;
            border-bottom: 1px solid var(--wmo-border);
          }

          .wmo-alert-row {
            display: flex;
            align-items: center;
            gap: 15px;
            min-height: 65px;
            padding: 12px 4px;
            border-bottom: 1px solid #eceae6;
          }

          .wmo-alert-row > div {
            min-width: 0;
            flex: 1;
          }

          .wmo-alert-row strong {
            display: block;
            font-size: 12px;
            font-weight: 600;
          }

          .wmo-alert-row p {
            margin-top: 4px;
            color: var(--wmo-muted);
            font-size: 11px;
            line-height: 1.45;
          }

          .wmo-alert-row > svg {
            flex-shrink: 0;
            color: #687994;
          }

          .wmo-empty {
            display: flex;
            min-height: 155px;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 22px;
            color: #71819b;
            text-align: center;
          }

          .wmo-empty strong {
            color: var(--wmo-text);
            font-size: 13px;
          }

          .wmo-empty span {
            max-width: 330px;
            line-height: 1.5;
            font-size: 12px;
          }

          .wmo-error {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
            padding: 12px 15px;
            border: 1px solid #ffc2c2;
            border-radius: 9px;
            background: #fff0f0;
            color: #a72d2d;
          }

          .wmo-error span {
            flex: 1;
          }

          .wmo-error button {
            padding: 7px 12px;
            border: 1px solid #f0baba;
            border-radius: 7px;
            background: #fff;
            cursor: pointer;
          }

          .wmo-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-top: 13px;
            color: #7b8797;
            font-size: 11px;
          }

          .wmo-footer span,
          .wmo-footer button {
            display: inline-flex;
            align-items: center;
            gap: 7px;
          }

          .wmo-footer button {
            border: 0;
            background: transparent;
            color: #465a78;
            cursor: pointer;
          }

          .wmo-footer button:disabled {
            cursor: not-allowed;
            opacity: 0.6;
          }

          .wmo-spin {
            animation: wmo-rotate 1s linear infinite;
          }

          @keyframes wmo-rotate {
            to {
              transform: rotate(360deg);
            }
          }

          @media (max-width: 1300px) {
            .wmo-heading {
              align-items: flex-start;
              flex-direction: column;
            }

            .wmo-heading-actions {
              flex-wrap: wrap;
            }

            .wmo-health {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
          }

          @media (max-width: 1000px) {
            .wmo-bottom-grid {
              grid-template-columns: minmax(0, 1fr);
            }

            .wmo-table-heading {
              align-items: flex-start;
              flex-wrap: wrap;
            }
          }

          @media (max-width: 700px) {
            .wmo {
              padding: 15px;
            }

            .wmo-heading h1 {
              font-size: 24px;
            }

            .wmo-summary {
              grid-template-columns: repeat(2, minmax(0, 1fr));
              row-gap: 18px;
            }

            .wmo-summary-item:nth-child(2) {
              border-right: 0;
            }

            .wmo-summary-item {
              justify-content: flex-start;
              gap: 13px;
              padding-left: 19px;
            }

            .wmo-health {
              grid-template-columns: minmax(0, 1fr);
            }

            .wmo-chart-controls {
              flex-wrap: wrap;
              justify-content: flex-end;
            }

            .wmo-legend {
              gap: 10px;
              margin-right: 0;
            }

            .wmo-trend > .wmo-panel-heading {
              align-items: flex-start;
              flex-direction: column;
            }

            .wmo-filters {
              flex-wrap: wrap;
              width: 100%;
            }

            .wmo-search {
              flex: 1;
            }

            .wmo-bar-column small {
              font-size: 9px;
            }
          }

          @media (max-width: 420px) {
            .wmo-heading-actions {
              width: 100%;
            }

            .wmo-department {
              min-width: 100%;
            }

            .wmo-summary-item > svg {
              width: 25px;
            }

            .wmo-summary-value strong {
              font-size: 22px;
            }
          }
        `}</style>
      </main>
    </WorkspaceRequired>
  );
}
