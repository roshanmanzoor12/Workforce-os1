
"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Activity,
  AlertTriangle,
  AppWindow,
  ArrowRight,
  BarChart3,
  ChevronRight,
  Clock3,
  Download,
  Info,
  Laptop2,
  Monitor,
  RefreshCw,
  Search,
  UsersRound,
  X,
} from "lucide-react";

import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";
import {
  monitoringService,
  type MonitoringSnapshot,
} from "@/services/monitoring.service";

type AppRecord = {
  id: string;
  name: string;
  category: string;
  employee: string;
  employeeId: string;
  device: string;
  deviceId: string;
  observedAt: string;
  durationSeconds: number;
  source: string;
};

type AppGroup = {
  name: string;
  category: string;
  durationSeconds: number;
  devices: Set<string>;
  employees: Set<string>;
  lastSeen: number;
  records: AppRecord[];
};

type DetailTab = "overview" | "devices" | "employees";
type Period = "today" | "yesterday" | "7days" | "30days";

const COLORS = [
  "#4588f6",
  "#9662e9",
  "#ff507a",
  "#ff7449",
  "#ffb81b",
  "#aab5c6",
];

const text = (value: unknown, fallback = ""): string =>
  typeof value === "string"
    ? value
    : typeof value === "number"
      ? String(value)
      : fallback;

const positiveNumber = (value: unknown): number => {
  const number = Number(value);
  return Number.isFinite(number) && number > 0
    ? number
    : 0;
};

function parseRecord(
  raw: Record<string, unknown>,
  index: number
): AppRecord | null {
  const name = text(
    raw.application_name ??
      raw.app_name ??
      raw.process_name ??
      raw.application ??
      raw.app
  ).trim();

  if (!name) return null;

  const observedAt = text(
    raw.observed_at ??
      raw.started_at ??
      raw.captured_at ??
      raw.last_observed ??
      raw.timestamp
  );

  if (
    !observedAt ||
    Number.isNaN(new Date(observedAt).getTime())
  ) {
    return null;
  }

  let durationSeconds = positiveNumber(
    raw.duration_seconds ??
      raw.observed_seconds ??
      raw.active_seconds ??
      raw.duration_sec
  );

  if (
    durationSeconds === 0 &&
    raw.duration_minutes != null
  ) {
    durationSeconds =
      positiveNumber(raw.duration_minutes) * 60;
  }

  return {
    id: text(raw.id, `row-${index}`),
    name,
    category: text(
      raw.category ?? raw.app_category,
      "Uncategorized"
    ),
    employee: text(
      raw.employee ?? raw.employee_name,
      "Unassigned"
    ),
    employeeId: text(raw.employee_id),
    device: text(
      raw.device ?? raw.device_name,
      "Unknown device"
    ),
    deviceId: text(raw.device_id),
    observedAt,
    durationSeconds,
    source: text(raw.source, "monitoring"),
  };
}

function durationLabel(seconds: number): string {
  if (!seconds) return "0 min";
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;

  if (!hours) {
    if (minutes === 0) return `${Math.floor(seconds)} sec`;
    return `${minutes} min`;
  }

  return `${hours}h ${remainder}m`;
}

function relativeDate(value: number): string {
  if (!value) return "—";

  const seconds = Math.max(
    0,
    Math.floor((Date.now() - value) / 1000)
  );

  if (seconds < 60) return "Just now";
  if (seconds < 3600)
    return `${Math.floor(seconds / 60)} min ago`;
  if (seconds < 86400)
    return `${Math.floor(seconds / 3600)} hours ago`;

  return new Date(value).toLocaleDateString();
}

function inPeriod(dateValue: string, period: Period): boolean {
  const date = new Date(dateValue);
  const now = new Date();

  const todayStart = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate()
  );

  if (period === "today") {
    return date >= todayStart && date <= now;
  }

  if (period === "yesterday") {
    const yesterdayStart = new Date(todayStart);
    yesterdayStart.setDate(yesterdayStart.getDate() - 1);

    return date >= yesterdayStart && date < todayStart;
  }

  const cutoff = new Date(todayStart);
  cutoff.setDate(
    cutoff.getDate() - (period === "7days" ? 6 : 29)
  );

  return date >= cutoff && date <= now;
}

function escapeCsv(value: string): string {
  const safe = /^[=+\-@\t\r]/.test(value)
    ? `'${value}`
    : value;

  return `"${safe.replaceAll('"', '""')}"`;
}

function downloadCsv(rows: AppRecord[]): void {
  const headers = [
    "Application",
    "Category",
    "Employee",
    "Employee ID",
    "Device",
    "Device ID",
    "Observed time",
    "Duration seconds",
    "Source",
  ];

  const data = [
    headers,
    ...rows.map((row) => [
      row.name,
      row.category,
      row.employee,
      row.employeeId,
      row.device,
      row.deviceId,
      row.observedAt,
      String(row.durationSeconds),
      row.source,
    ]),
  ];

  const contents = data
    .map((row) => row.map(escapeCsv).join(","))
    .join("\r\n");

  const blob = new Blob(["\uFEFF", contents], {
    type: "text/csv;charset=utf-8",
  });

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = "workforce-application-activity.csv";

  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Metric({
  icon,
  title,
  value,
  detail,
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="aa-metric">
      <div className="aa-metric-icon">{icon}</div>
      <div>
        <span>{title}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
      <Info size={15} className="aa-metric-info" />
    </div>
  );
}

function ChartEmpty({ label }: { label: string }) {
  return (
    <div className="aa-chart-empty">
      <BarChart3 size={28} />
      <strong>{label}</strong>
      <p>
        Chart data will appear when the backend returns
        authorized application-duration observations.
      </p>
    </div>
  );
}

export default function MonitoringApplicationsPage() {
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

  const [period, setPeriod] = useState<Period>("today");
  const [search, setSearch] = useState("");
  const [selectedName, setSelectedName] = useState<string | null>(
    null
  );
  const [detailTab, setDetailTab] =
    useState<DetailTab>("overview");

  const load = useCallback(
    async (quiet = false) => {
      if (!workspaceId || !canRead) {
        setLoading(false);
        return;
      }

      if (quiet) setRefreshing(true);
      else setLoading(true);

      try {
        const response =
          await monitoringService.applications(workspaceId);

        setSnapshot(response);
        setError("");
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load application monitoring data."
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

    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void load(true);
      }
    }, 30000);

    return () => window.clearInterval(interval);
  }, [workspaceId, canRead, load]);

  const records = useMemo(
    () =>
      (snapshot?.items || [])
        .map((item, index) => parseRecord(item, index))
        .filter((item): item is AppRecord => item !== null),
    [snapshot]
  );

  const periodRecords = useMemo(
    () =>
      records.filter((record) =>
        inPeriod(record.observedAt, period)
      ),
    [records, period]
  );

  const apps = useMemo(() => {
    const groups = new Map<string, AppGroup>();

    for (const record of periodRecords) {
      const key = record.name.toLowerCase();
      let group = groups.get(key);

      if (!group) {
        group = {
          name: record.name,
          category: record.category,
          durationSeconds: 0,
          devices: new Set<string>(),
          employees: new Set<string>(),
          lastSeen: 0,
          records: [],
        };
        groups.set(key, group);
      }

      group.durationSeconds += record.durationSeconds;
      group.lastSeen = Math.max(
        group.lastSeen,
        new Date(record.observedAt).getTime()
      );
      group.records.push(record);

      if (record.deviceId) {
        group.devices.add(record.deviceId);
      }

      if (record.employeeId) {
        group.employees.add(record.employeeId);
      }
    }

    return [...groups.values()].sort(
      (a, b) =>
        b.durationSeconds - a.durationSeconds ||
        b.records.length - a.records.length
    );
  }, [periodRecords]);

  const filteredApps = useMemo(() => {
    const needle = search.trim().toLowerCase();

    return apps.filter((app) =>
      [app.name, app.category]
        .join(" ")
        .toLowerCase()
        .includes(needle)
    );
  }, [apps, search]);

  const selectedApp = useMemo(
    () =>
      apps.find(
        (app) =>
          app.name.toLowerCase() ===
          selectedName?.toLowerCase()
      ) ||
      apps[0] ||
      null,
    [apps, selectedName]
  );

  const reportingDevices = new Set(
    periodRecords
      .map((record) => record.deviceId)
      .filter(Boolean)
  ).size;

  const totalSeconds = periodRecords.reduce(
    (total, record) => total + record.durationSeconds,
    0
  );

  const hasDurationData = periodRecords.some(
    (record) => record.durationSeconds > 0
  );

  const maxDuration = Math.max(
    1,
    ...apps.map((app) => app.durationSeconds)
  );

  const hourly = useMemo(() => {
    const buckets = Array.from(
      { length: 10 },
      (_, index) => ({
        hour: index + 8,
        total: 0,
        byApp: new Map<string, number>(),
      })
    );

    for (const record of periodRecords) {
      const hour = new Date(record.observedAt).getHours();
      const bucket = buckets.find(
        (item) => item.hour === hour
      );

      if (!bucket) continue;

      bucket.total += record.durationSeconds;
      bucket.byApp.set(
        record.name,
        (bucket.byApp.get(record.name) || 0) +
          record.durationSeconds
      );
    }

    return buckets;
  }, [periodRecords]);

  const hourlyMax = Math.max(
    1,
    ...hourly.map((bucket) => bucket.total)
  );

  const selectedHourly = useMemo(
    () =>
      hourly.map((bucket) => ({
        hour: bucket.hour,
        value: selectedApp
          ? bucket.byApp.get(selectedApp.name) || 0
          : 0,
      })),
    [hourly, selectedApp]
  );

  const selectedHourlyMax = Math.max(
    1,
    ...selectedHourly.map((bucket) => bucket.value)
  );

  const selectedDeviceRows = useMemo(() => {
    if (!selectedApp) return [];

    const groups = new Map<
      string,
      { id: string; name: string; seconds: number }
    >();

    for (const record of selectedApp.records) {
      const key = record.deviceId || record.device;

      const item = groups.get(key) || {
        id: key,
        name: record.device,
        seconds: 0,
      };

      item.seconds += record.durationSeconds;
      groups.set(key, item);
    }

    return [...groups.values()].sort(
      (a, b) => b.seconds - a.seconds
    );
  }, [selectedApp]);

  const selectedEmployeeRows = useMemo(() => {
    if (!selectedApp) return [];

    const groups = new Map<
      string,
      { id: string; name: string; seconds: number }
    >();

    for (const record of selectedApp.records) {
      const key = record.employeeId || record.employee;

      const item = groups.get(key) || {
        id: key,
        name: record.employee,
        seconds: 0,
      };

      item.seconds += record.durationSeconds;
      groups.set(key, item);
    }

    return [...groups.values()].sort(
      (a, b) => b.seconds - a.seconds
    );
  }, [selectedApp]);

  const formatHour = (hour: number) =>
    hour === 12
      ? "12 PM"
      : hour > 12
        ? `${hour - 12} PM`
        : `${hour} AM`;

  return (
    <WorkspaceRequired>
      <main className="aa-page">
        <header className="aa-header">
          <div>
            <h1>Application Activity</h1>
            <p>
              Overview of authorized application usage
              across your organization.
            </p>
          </div>

          <div className="aa-header-actions">
            <select
              aria-label="Period"
              value={period}
              onChange={(event) =>
                setPeriod(event.target.value as Period)
              }
            >
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
              <option value="7days">Last 7 days</option>
              <option value="30days">Last 30 days</option>
            </select>

            <button
              type="button"
              className="aa-btn aa-btn-white"
              disabled={refreshing || !canRead}
              onClick={() => void load(true)}
            >
              <RefreshCw
                size={16}
                className={refreshing ? "aa-spin" : ""}
              />
              Refresh
            </button>

            <button
              type="button"
              className="aa-btn aa-btn-dark"
              disabled={!canRead || periodRecords.length === 0}
              onClick={() => downloadCsv(periodRecords)}
            >
              <Download size={17} />
              Export report
            </button>
          </div>
        </header>

        {!canRead ? (
          <div className="aa-error">
            <AlertTriangle size={18} />
            You do not have access to application monitoring.
          </div>
        ) : (
          <>
            {error && (
              <div className="aa-error">
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

            <section className="aa-metrics">
              <Metric
                icon={<Laptop2 size={28} />}
                title="Reporting devices"
                value={String(reportingDevices)}
                detail="Distinct devices in returned records"
              />
              <Metric
                icon={<AppWindow size={28} />}
                title="Unique applications"
                value={String(apps.length)}
                detail="Across authorized records"
              />
              <Metric
                icon={<Clock3 size={29} />}
                title="Recorded application time"
                value={
                  hasDurationData
                    ? durationLabel(totalSeconds)
                    : "—"
                }
                detail={
                  hasDurationData
                    ? "Sum of reported durations"
                    : "Duration data unavailable"
                }
              />
            </section>

            <div className="aa-layout">
              <div className="aa-left">
                <section className="aa-panel">
                  <div className="aa-panel-heading">
                    <h2>
                      <BarChart3 size={21} />
                      Application activity trend
                    </h2>

                    <span className="aa-secondary">
                      Recorded duration by hour
                    </span>
                  </div>

                  {hasDurationData ? (
                    <div className="aa-main-chart">
                      <div className="aa-y-labels">
                        <span>{durationLabel(hourlyMax)}</span>
                        <span>
                          {durationLabel(hourlyMax / 2)}
                        </span>
                        <span>0</span>
                      </div>

                      <div className="aa-bars">
                        {hourly.map((bucket) => (
                          <div
                            className="aa-bar-col"
                            key={bucket.hour}
                          >
                            <div className="aa-bar-stack">
                              {apps
                                .slice(0, 5)
                                .map((app, index) => {
                                  const seconds =
                                    bucket.byApp.get(
                                      app.name
                                    ) || 0;

                                  return (
                                    <div
                                      key={app.name}
                                      title={`${app.name}: ${durationLabel(seconds)}`}
                                      style={{
                                        height: `${
                                          (seconds / hourlyMax) *
                                          100
                                        }%`,
                                        backgroundColor:
                                          COLORS[index],
                                      }}
                                    />
                                  );
                                })}

                              <div
                                title="Other applications"
                                style={{
                                  height: `${
                                    (Math.max(
                                      0,
                                      bucket.total -
                                        apps
                                          .slice(0, 5)
                                          .reduce(
                                            (sum, app) =>
                                              sum +
                                              (bucket.byApp.get(
                                                app.name
                                              ) || 0),
                                            0
                                          )
                                    ) /
                                      hourlyMax) *
                                    100
                                  }%`,
                                  backgroundColor:
                                    COLORS[5],
                                }}
                              />
                            </div>
                            <small>
                              {formatHour(bucket.hour)}
                            </small>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <ChartEmpty label="No application duration data" />
                  )}

                  <div className="aa-legend">
                    {apps.slice(0, 5).map((app, index) => (
                      <span key={app.name}>
                        <i
                          style={{
                            backgroundColor: COLORS[index],
                          }}
                        />
                        {app.name}
                      </span>
                    ))}
                    {apps.length > 5 && (
                      <span>
                        <i
                          style={{
                            backgroundColor: COLORS[5],
                          }}
                        />
                        Other applications
                      </span>
                    )}
                  </div>
                </section>

                <section className="aa-panel aa-usage">
                  <div className="aa-panel-heading">
                    <h2>
                      <AppWindow size={21} />
                      Application usage
                    </h2>

                    <label className="aa-search">
                      <Search size={17} />
                      <input
                        value={search}
                        onChange={(event) =>
                          setSearch(event.target.value)
                        }
                        placeholder="Search applications..."
                      />
                    </label>
                  </div>

                  <div className="aa-table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Application</th>
                          <th>Category</th>
                          <th>Observed duration</th>
                          <th>Devices</th>
                          <th>Last observed</th>
                          <th />
                        </tr>
                      </thead>

                      <tbody>
                        {filteredApps.map((app) => (
                          <tr
                            key={app.name}
                            className={
                              selectedApp?.name === app.name
                                ? "aa-selected"
                                : ""
                            }
                          >
                            <td>
                              <button
                                type="button"
                                className="aa-app-name"
                                onClick={() => {
                                  setSelectedName(app.name);
                                  setDetailTab("overview");
                                }}
                              >
                                <span className="aa-app-icon">
                                  {app.name
                                    .slice(0, 1)
                                    .toUpperCase()}
                                </span>
                                {app.name}
                              </button>
                            </td>

                            <td>
                              <span className="aa-category">
                                {app.category}
                              </span>
                            </td>

                            <td>
                              <div className="aa-duration">
                                <span>
                                  {app.durationSeconds > 0
                                    ? durationLabel(
                                        app.durationSeconds
                                      )
                                    : "—"}
                                </span>
                                <div>
                                  <i
                                    style={{
                                      width: `${
                                        (app.durationSeconds /
                                          maxDuration) *
                                        100
                                      }%`,
                                    }}
                                  />
                                </div>
                              </div>
                            </td>

                            <td>{app.devices.size}</td>
                            <td className="aa-muted">
                              {relativeDate(app.lastSeen)}
                            </td>

                            <td>
                              <button
                                type="button"
                                aria-label={`Select ${app.name}`}
                                onClick={() =>
                                  setSelectedName(app.name)
                                }
                              >
                                <ChevronRight size={17} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    {!loading && filteredApps.length === 0 && (
                      <div className="aa-empty-table">
                        <AppWindow size={29} />
                        <strong>
                          {apps.length === 0
                            ? "No application activity returned"
                            : "No matching applications"}
                        </strong>
                        <p>
                          {apps.length === 0
                            ? "Application history will appear when authorized app-usage data is exposed through the workspace monitoring API."
                            : "Try a different search term."}
                        </p>
                      </div>
                    )}

                    {loading && (
                      <div className="aa-empty-table">
                        <RefreshCw
                          size={25}
                          className="aa-spin"
                        />
                        Loading applications...
                      </div>
                    )}
                  </div>

                  <div className="aa-table-footer">
                    Showing {filteredApps.length} applications
                  </div>
                </section>
              </div>

              <aside className="aa-panel aa-detail">
                <div className="aa-detail-heading">
                  {selectedApp ? (
                    <>
                      <div className="aa-app-icon aa-large-icon">
                        {selectedApp.name
                          .slice(0, 1)
                          .toUpperCase()}
                      </div>

                      <div>
                        <h2>{selectedApp.name}</h2>
                        <p>{selectedApp.category}</p>
                      </div>

                      <button
                        type="button"
                        className="aa-close"
                        aria-label="Close selected application"
                        onClick={() => setSelectedName(null)}
                      >
                        <X size={19} />
                      </button>
                    </>
                  ) : (
                    <div>
                      <h2>Application details</h2>
                      <p>Select an application to inspect.</p>
                    </div>
                  )}
                </div>

                {selectedApp ? (
                  <>
                    <div className="aa-tabs">
                      {(
                        [
                          "overview",
                          "devices",
                          "employees",
                        ] as const
                      ).map((tab) => (
                        <button
                          key={tab}
                          type="button"
                          className={
                            detailTab === tab
                              ? "aa-active-tab"
                              : ""
                          }
                          onClick={() =>
                            setDetailTab(tab)
                          }
                        >
                          {tab.charAt(0).toUpperCase() +
                            tab.slice(1)}
                        </button>
                      ))}
                    </div>

                    {detailTab === "overview" && (
                      <>
                        <div className="aa-detail-metrics">
                          <div>
                            <Clock3 size={20} />
                            <span>Observed duration</span>
                            <strong>
                              {selectedApp.durationSeconds > 0
                                ? durationLabel(
                                    selectedApp.durationSeconds
                                  )
                                : "—"}
                            </strong>
                          </div>
                          <div>
                            <Monitor size={20} />
                            <span>Devices reporting</span>
                            <strong>
                              {selectedApp.devices.size}
                            </strong>
                          </div>
                          <div>
                            <Activity size={20} />
                            <span>Last observed</span>
                            <strong>
                              {relativeDate(
                                selectedApp.lastSeen
                              )}
                            </strong>
                          </div>
                        </div>

                        <div className="aa-detail-chart-head">
                          <h3>
                            <BarChart3 size={19} />
                            Application activity trend
                          </h3>
                          <span>By hour</span>
                        </div>

                        {selectedApp.durationSeconds > 0 ? (
                          <div className="aa-small-chart">
                            {selectedHourly.map((bucket) => (
                              <div key={bucket.hour}>
                                <div className="aa-small-bar-wrap">
                                  <div
                                    style={{
                                      height: `${
                                        (bucket.value /
                                          selectedHourlyMax) *
                                        100
                                      }%`,
                                    }}
                                  />
                                </div>
                                <span>
                                  {formatHour(bucket.hour)}
                                </span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <ChartEmpty label="No recorded duration" />
                        )}

                        <div className="aa-breakdown">
                          <h3>
                            <UsersRound size={19} />
                            Top employees using this application
                          </h3>
                          {selectedEmployeeRows.length ? (
                            <table>
                              <thead>
                                <tr>
                                  <th>Employee</th>
                                  <th>Observed duration</th>
                                </tr>
                              </thead>
                              <tbody>
                                {selectedEmployeeRows
                                  .slice(0, 5)
                                  .map((item) => (
                                    <tr key={item.id}>
                                      <td>{item.name}</td>
                                      <td>
                                        {durationLabel(
                                          item.seconds
                                        )}
                                      </td>
                                    </tr>
                                  ))}
                              </tbody>
                            </table>
                          ) : (
                            <p className="aa-hint">
                              No attributed employee
                              records available.
                            </p>
                          )}
                        </div>
                      </>
                    )}

                    {detailTab === "devices" && (
                      <div className="aa-tab-content">
                        <h3>
                          <Laptop2 size={19} />
                          Reporting devices
                        </h3>
                        {selectedDeviceRows.length ? (
                          <table>
                            <thead>
                              <tr>
                                <th>Device</th>
                                <th>Duration</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedDeviceRows.map(
                                (item) => (
                                  <tr key={item.id}>
                                    <td>{item.name}</td>
                                    <td>
                                      {durationLabel(
                                        item.seconds
                                      )}
                                    </td>
                                  </tr>
                                )
                              )}
                            </tbody>
                          </table>
                        ) : (
                          <p className="aa-hint">
                            No device attribution available.
                          </p>
                        )}
                      </div>
                    )}

                    {detailTab === "employees" && (
                      <div className="aa-tab-content">
                        <h3>
                          <UsersRound size={19} />
                          Employee breakdown
                        </h3>

                        {selectedEmployeeRows.length ? (
                          <table>
                            <thead>
                              <tr>
                                <th>Employee</th>
                                <th>Duration</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedEmployeeRows.map(
                                (item) => (
                                  <tr key={item.id}>
                                    <td>{item.name}</td>
                                    <td>
                                      {durationLabel(
                                        item.seconds
                                      )}
                                    </td>
                                  </tr>
                                )
                              )}
                            </tbody>
                          </table>
                        ) : (
                          <p className="aa-hint">
                            No employee attribution available.
                          </p>
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="aa-detail-empty">
                    <AppWindow size={31} />
                    <strong>No application selected</strong>
                    <p>
                      Choose an application from the usage
                      table to view more details.
                    </p>
                  </div>
                )}
              </aside>
            </div>

            <div className="aa-footer-note">
              <Info size={16} />
              Application duration is based on returned
              usage records. Missing time, unreported
              devices, and unattributed observations
              are not automatically counted as activity.
              {snapshot?.generated_at &&
                ` Updated ${new Date(
                  snapshot.generated_at
                ).toLocaleString()}.`}
            </div>
          </>
        )}

        <style jsx global>{`
          .aa-page {
            --aa-ink: #0d1a3b;
            --aa-muted: #6c7a94;
            --aa-border: #e5e8ed;
            padding: 20px 21px 35px;
            min-height: 100%;
            background: #fbfaf8;
            color: var(--aa-ink);
            font-size: 12px;
          }

          .aa-page * {
            box-sizing: border-box;
          }

          .aa-page button,
          .aa-page select,
          .aa-page input {
            font: inherit;
          }

          .aa-page button {
            cursor: pointer;
          }

          .aa-page button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
          }

          .aa-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            margin-bottom: 19px;
          }

          .aa-header h1 {
            margin: 0;
            font-size: 29px;
            line-height: 1.2;
            font-weight: 750;
            letter-spacing: -0.8px;
          }

          .aa-header p {
            margin: 4px 0 0;
            font-size: 14px;
            color: var(--aa-muted);
          }

          .aa-header-actions {
            display: flex;
            align-items: center;
            gap: 9px;
          }

          .aa-header-actions select {
            height: 38px;
            border: 1px solid #e2e6eb;
            background: white;
            border-radius: 7px;
            padding: 0 12px;
            color: var(--aa-ink);
          }

          .aa-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 9px;
            border-radius: 7px;
            min-height: 38px;
            padding: 0 14px;
            font-weight: 650 !important;
            white-space: nowrap;
          }

          .aa-btn-white {
            background: white;
            color: var(--aa-ink);
            border: 1px solid #dfe3e9;
          }

          .aa-btn-dark {
            background: #172331;
            color: white;
            border: 1px solid #172331;
          }

          .aa-metrics {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 13px;
            margin-bottom: 14px;
          }

          .aa-metric {
            min-height: 102px;
            border: 1px solid #ece5d9;
            border-radius: 11px;
            background: linear-gradient(100deg, #fffaf0, #fffefd);
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 16px 18px;
            position: relative;
          }

          .aa-metric-icon {
            width: 61px;
            height: 61px;
            flex-shrink: 0;
            border-radius: 50%;
            background: #fff0d1;
            display: grid;
            place-items: center;
          }

          .aa-metric > div:nth-child(2) {
            display: flex;
            flex-direction: column;
            gap: 5px;
          }

          .aa-metric span {
            font-size: 13px;
            font-weight: 650;
          }

          .aa-metric strong {
            font-size: 26px;
            letter-spacing: -0.75px;
            line-height: 1.1;
          }

          .aa-metric small {
            font-size: 12px;
            color: var(--aa-muted);
          }

          .aa-metric-info {
            position: absolute;
            right: 16px;
            top: 13px;
            color: #7787a0;
          }

          .aa-layout {
            display: grid;
            grid-template-columns: minmax(0, 1.38fr) minmax(340px, 0.86fr);
            align-items: start;
            gap: 14px;
          }

          .aa-left {
            display: flex;
            flex-direction: column;
            gap: 13px;
            min-width: 0;
          }

          .aa-panel {
            background: #fffefa;
            border: 1px solid var(--aa-border);
            border-radius: 11px;
            overflow: hidden;
            min-width: 0;
          }

          .aa-panel-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            min-height: 57px;
            padding: 12px 15px;
          }

          .aa-panel-heading h2 {
            display: flex;
            align-items: center;
            gap: 9px;
            margin: 0;
            font-size: 17px;
            font-weight: 750;
            letter-spacing: -0.3px;
          }

          .aa-secondary {
            color: var(--aa-muted);
          }

          .aa-main-chart {
            height: 235px;
            display: flex;
            gap: 8px;
            padding: 18px 17px 4px;
          }

          .aa-y-labels {
            height: 188px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #63738f;
            white-space: nowrap;
            font-size: 10px;
          }

          .aa-bars {
            height: 188px;
            flex: 1;
            display: grid;
            grid-template-columns: repeat(10, minmax(0, 1fr));
            gap: 5px;
            border-bottom: 1px solid #bdc6d4;
            background: repeating-linear-gradient(
              to top,
              transparent 0,
              transparent calc(25% - 1px),
              #e5e8ee calc(25% - 1px),
              #e5e8ee 25%
            );
          }

          .aa-bar-col {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
            min-width: 0;
            height: 100%;
          }

          .aa-bar-stack {
            display: flex;
            flex-direction: column-reverse;
            width: min(100%, 43px);
            height: calc(100% - 26px);
            justify-content: flex-start;
          }

          .aa-bar-stack > div {
            width: 100%;
            flex-shrink: 0;
          }

          .aa-bar-col small {
            height: 26px;
            padding-top: 7px;
            color: #5d6d88;
            font-size: 10px;
            white-space: nowrap;
          }

          .aa-legend {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 14px;
            padding: 13px 15px 16px;
            color: var(--aa-muted);
          }

          .aa-legend span {
            display: inline-flex;
            align-items: center;
            gap: 6px;
          }

          .aa-legend i {
            width: 11px;
            height: 11px;
            border-radius: 50%;
          }

          .aa-chart-empty,
          .aa-empty-table,
          .aa-detail-empty {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            gap: 11px;
            color: #8897ac;
            padding: 25px;
            min-height: 220px;
          }

          .aa-chart-empty strong,
          .aa-empty-table strong,
          .aa-detail-empty strong {
            color: var(--aa-ink);
          }

          .aa-chart-empty p,
          .aa-empty-table p,
          .aa-detail-empty p {
            max-width: 290px;
            margin: 0;
            line-height: 1.6;
          }

          .aa-search {
            display: flex;
            align-items: center;
            gap: 8px;
            height: 36px;
            border: 1px solid #dfe4ea;
            background: white;
            border-radius: 7px;
            padding: 0 11px;
            color: #74849e;
          }

          .aa-search input {
            width: 150px;
            background: transparent;
            border: 0;
            outline: 0;
            color: var(--aa-ink);
          }

          .aa-table-wrap {
            width: 100%;
            overflow-x: auto;
          }

          .aa-table-wrap table,
          .aa-tab-content table,
          .aa-breakdown table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
          }

          .aa-table-wrap table {
            min-width: 600px;
          }

          .aa-table-wrap th,
          .aa-tab-content th,
          .aa-breakdown th {
            background: #f7f7f7;
            font-size: 10px;
            font-weight: 700;
            padding: 11px 10px;
            white-space: nowrap;
          }

          .aa-table-wrap td,
          .aa-tab-content td,
          .aa-breakdown td {
            border-top: 1px solid #e9ebef;
            padding: 10px;
            font-size: 11px;
          }

          .aa-table-wrap tr.aa-selected {
            background: #fff6e2;
          }

          .aa-app-name {
            display: inline-flex;
            align-items: center;
            gap: 9px;
            background: transparent;
            border: 0;
            color: var(--aa-ink);
            font-weight: 650 !important;
          }

          .aa-app-icon {
            width: 25px;
            height: 25px;
            border-radius: 6px;
            background: #202b45;
            color: #fff;
            display: grid;
            place-items: center;
            flex-shrink: 0;
            font-size: 13px;
            font-weight: 750;
          }

          .aa-category {
            display: inline-flex;
            background: #e8efff;
            color: #3165bc;
            padding: 5px 8px;
            border-radius: 5px;
            white-space: nowrap;
          }

          .aa-duration {
            display: flex;
            align-items: center;
            gap: 10px;
            white-space: nowrap;
          }

          .aa-duration > div {
            height: 11px;
            width: 105px;
            border-radius: 8px;
            background: #edf0f4;
            overflow: hidden;
          }

          .aa-duration > div i {
            display: block;
            height: 100%;
            background: #ffb518;
            border-radius: inherit;
          }

          .aa-muted {
            color: var(--aa-muted);
            white-space: nowrap;
          }

          .aa-table-wrap td > button:last-child {
            border: 0;
            background: transparent;
            color: #465a7a;
          }

          .aa-table-footer {
            padding: 13px 15px;
            color: var(--aa-muted);
          }

          .aa-detail-heading {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 17px 16px;
          }

          .aa-large-icon {
            width: 53px;
            height: 53px;
            font-size: 24px;
            border-radius: 10px;
          }

          .aa-detail-heading > div:nth-child(2) {
            flex: 1;
            min-width: 0;
          }

          .aa-detail-heading h2 {
            margin: 0;
            font-size: 19px;
            letter-spacing: -0.3px;
          }

          .aa-detail-heading p {
            color: var(--aa-muted);
            margin: 5px 0 0;
          }

          .aa-close {
            background: transparent;
            border: 0;
            align-self: flex-start;
          }

          .aa-tabs {
            margin: 0 14px;
            border-bottom: 1px solid #e7e9ed;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
          }

          .aa-tabs button {
            border: 0;
            background: transparent;
            height: 39px;
            color: #64748d;
          }

          .aa-tabs button.aa-active-tab {
            color: var(--aa-ink);
            border-bottom: 2px solid #ffa900;
            font-weight: 700;
          }

          .aa-detail-metrics {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            padding: 20px 13px;
            gap: 8px;
            border-bottom: 1px solid #e8eaee;
          }

          .aa-detail-metrics > div {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 9px;
            text-align: center;
            min-width: 0;
            border-right: 1px solid #e7e9ec;
          }

          .aa-detail-metrics > div:last-child {
            border-right: 0;
          }

          .aa-detail-metrics span {
            color: #677892;
            font-size: 11px;
          }

          .aa-detail-metrics strong {
            font-size: 17px;
            overflow-wrap: anywhere;
          }

          .aa-detail-chart-head {
            padding: 16px 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
          }

          .aa-detail-chart-head h3,
          .aa-breakdown h3,
          .aa-tab-content h3 {
            margin: 0;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 9px;
          }

          .aa-detail-chart-head span {
            color: var(--aa-muted);
          }

          .aa-small-chart {
            display: grid;
            grid-template-columns: repeat(10, minmax(0, 1fr));
            gap: 5px;
            height: 175px;
            padding: 8px 14px 0;
          }

          .aa-small-chart > div {
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: center;
            min-width: 0;
          }

          .aa-small-bar-wrap {
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            width: min(100%, 30px);
          }

          .aa-small-bar-wrap > div {
            background: #ff5574;
            width: 100%;
          }

          .aa-small-chart > div > span {
            font-size: 9px;
            color: #667791;
            height: 26px;
            padding-top: 7px;
            white-space: nowrap;
          }

          .aa-breakdown,
          .aa-tab-content {
            margin: 16px 13px;
          }

          .aa-breakdown h3,
          .aa-tab-content h3 {
            margin-bottom: 14px;
          }

          .aa-breakdown table,
          .aa-tab-content table {
            border: 1px solid #e8eaee;
            border-radius: 7px;
          }

          .aa-hint {
            padding: 17px 12px;
            color: var(--aa-muted);
            line-height: 1.6;
          }

          .aa-footer-note {
            display: flex;
            align-items: flex-start;
            gap: 9px;
            color: var(--aa-muted);
            line-height: 1.6;
            margin-top: 15px;
          }

          .aa-footer-note svg {
            flex-shrink: 0;
            margin-top: 2px;
          }

          .aa-error {
            border: 1px solid #f1baba;
            border-radius: 8px;
            background: #fff0f0;
            color: #b42e2e;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 14px;
            margin-bottom: 15px;
          }

          .aa-error span {
            flex: 1;
          }

          .aa-error button {
            border: 1px solid #f0bbbb;
            border-radius: 6px;
            background: white;
            padding: 6px 11px;
          }

          .aa-spin {
            animation: aa-spin 1s linear infinite;
          }

          @keyframes aa-spin {
            to {
              transform: rotate(360deg);
            }
          }

          @media (max-width: 1250px) {
            .aa-layout {
              grid-template-columns: minmax(0, 1fr);
            }
          }

          @media (max-width: 850px) {
            .aa-header {
              flex-direction: column;
              align-items: flex-start;
            }
            .aa-metrics {
              grid-template-columns: 1fr;
            }
          }

          @media (max-width: 540px) {
            .aa-page {
              padding: 15px 12px;
            }
            .aa-header h1 {
              font-size: 24px;
            }
            .aa-header-actions {
              flex-wrap: wrap;
            }
            .aa-panel-heading {
              flex-wrap: wrap;
            }
            .aa-detail-metrics {
              grid-template-columns: 1fr;
            }
            .aa-detail-metrics > div {
              border-right: 0;
              border-bottom: 1px solid #e8eaee;
              padding: 10px;
            }
          }
        `}</style>
      </main>
    </WorkspaceRequired>
  );
}
