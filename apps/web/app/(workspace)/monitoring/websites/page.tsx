
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
  BarChart3,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Download,
  ExternalLink,
  Globe2,
  Info,
  Laptop2,
  RefreshCw,
  Search,
  ShieldCheck,
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

type Range = "today" | "yesterday" | "7days" | "30days";
type DetailTab = "overview" | "employees" | "devices";

type WebsiteRecord = {
  id: string;
  domain: string;
  category: string;
  employeeId: string;
  employee: string;
  deviceId: string;
  device: string;
  observedAt: string;
  durationSeconds: number;
  source: string;
};

type DomainSummary = {
  domain: string;
  category: string;
  records: WebsiteRecord[];
  totalSeconds: number;
  employees: Set<string>;
  devices: Set<string>;
  lastSeen: number;
  observations: number;
};

type Breakdown = {
  id: string;
  label: string;
  seconds: number;
  observations: number;
};

const PAGE_SIZE = 10;

const DOMAIN_COLORS = [
  "#4d84ed",
  "#9268e9",
  "#27b981",
  "#f6ad26",
  "#eb6682",
  "#9aa7ba",
];

const str = (value: unknown, fallback = ""): string => {
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  return fallback;
};

const numberValue = (value: unknown): number => {
  const result = Number(value);
  return Number.isFinite(result) && result > 0
    ? result
    : 0;
};

function normalizeDomain(value: string): string {
  const raw = value.trim().toLowerCase();
  if (!raw) return "";

  try {
    const url = raw.includes("://")
      ? new URL(raw)
      : new URL(`https://${raw}`);

    const hostname = url.hostname
      .toLowerCase()
      .replace(/\.$/, "");

    if (
      !hostname ||
      hostname.length > 253 ||
      /[^a-z0-9.\-:\[\]]/.test(hostname)
    ) {
      return "";
    }

    return hostname;
  } catch {
    return "";
  }
}

function parseWebsite(
  item: Record<string, unknown>,
  index: number
): WebsiteRecord | null {
  const domain = normalizeDomain(
    str(
      item.domain ??
        item.hostname ??
        item.website ??
        item.host ??
        item.url ??
        item.website_url
    )
  );

  if (!domain) return null;

  const observedAt = str(
    item.observed_at ??
      item.started_at ??
      item.captured_at ??
      item.timestamp ??
      item.visited_at
  );

  if (
    !observedAt ||
    Number.isNaN(new Date(observedAt).getTime())
  ) {
    return null;
  }

  let durationSeconds = numberValue(
    item.duration_seconds ??
      item.active_seconds ??
      item.observed_seconds ??
      item.duration_sec
  );

  if (
    durationSeconds === 0 &&
    item.duration_minutes !== undefined
  ) {
    durationSeconds =
      numberValue(item.duration_minutes) * 60;
  }

  return {
    id: str(item.id, `website-${index}`),
    domain,
    category: str(
      item.category ?? item.website_category,
      "Uncategorized"
    ),
    employeeId: str(item.employee_id),
    employee: str(
      item.employee ?? item.employee_name,
      "Unassigned"
    ),
    deviceId: str(item.device_id),
    device: str(
      item.device ?? item.device_name,
      "Unknown device"
    ),
    observedAt,
    durationSeconds,
    source: str(item.source, "monitoring"),
  };
}

function inRange(value: string, range: Range): boolean {
  const time = new Date(value).getTime();
  if (!Number.isFinite(time)) return false;

  const now = new Date();
  const today = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate()
  );

  if (range === "today") {
    return time >= today.getTime() &&
      time <= now.getTime();
  }

  if (range === "yesterday") {
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    return (
      time >= yesterday.getTime() &&
      time < today.getTime()
    );
  }

  const cutoff = new Date(today);
  cutoff.setDate(
    cutoff.getDate() - (range === "7days" ? 6 : 29)
  );

  return (
    time >= cutoff.getTime() &&
    time <= now.getTime()
  );
}

function duration(seconds: number): string {
  if (seconds <= 0) return "0 min";

  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  }

  if (minutes > 0) return `${minutes} min`;
  return `${Math.floor(seconds)} sec`;
}

function relativeTime(timestamp: number): string {
  if (!timestamp) return "—";

  const difference = Math.max(
    0,
    Math.floor((Date.now() - timestamp) / 1000)
  );

  if (difference < 60) return "Just now";
  if (difference < 3600) {
    return `${Math.floor(difference / 60)} min ago`;
  }
  if (difference < 86400) {
    return `${Math.floor(difference / 3600)} hours ago`;
  }

  return new Date(timestamp).toLocaleDateString();
}

function formatObserved(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
}

function buildBreakdown(
  records: WebsiteRecord[],
  field: "employee" | "device"
): Breakdown[] {
  const groups = new Map<string, Breakdown>();

  for (const record of records) {
    const id =
      field === "employee"
        ? record.employeeId || record.employee
        : record.deviceId || record.device;

    const label =
      field === "employee"
        ? record.employee
        : record.device;

    const existing = groups.get(id) || {
      id,
      label,
      seconds: 0,
      observations: 0,
    };

    existing.seconds += record.durationSeconds;
    existing.observations += 1;
    groups.set(id, existing);
  }

  return [...groups.values()].sort(
    (a, b) =>
      b.seconds - a.seconds ||
      b.observations - a.observations
  );
}

function csvCell(value: string): string {
  const safe = /^[=+\-@\t\r]/.test(value)
    ? `'${value}`
    : value;

  return `"${safe.replaceAll('"', '""')}"`;
}

function exportWebsiteCsv(records: WebsiteRecord[]) {
  const data = [
    [
      "Domain",
      "Category",
      "Employee",
      "Employee ID",
      "Device",
      "Device ID",
      "Observed at",
      "Duration seconds",
      "Source",
    ],
    ...records.map((record) => [
      record.domain,
      record.category,
      record.employee,
      record.employeeId,
      record.device,
      record.deviceId,
      record.observedAt,
      String(record.durationSeconds),
      record.source,
    ]),
  ];

  const csv = data
    .map((row) => row.map(csvCell).join(","))
    .join("\r\n");

  const blob = new Blob(["\uFEFF", csv], {
    type: "text/csv;charset=utf-8",
  });

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "workforce-website-activity.csv";

  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  window.setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 1000);
}

function MetricCard({
  icon,
  label,
  value,
  note,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="wa-metric">
      <span className="wa-metric-icon">{icon}</span>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{note}</small>
      </div>
    </div>
  );
}

function Empty({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="wa-empty">
      <Globe2 size={32} />
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}

export default function MonitoringWebsitesPage() {
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

  const [range, setRange] = useState<Range>("today");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [employeeFilter, setEmployeeFilter] =
    useState("all");
  const [page, setPage] = useState(1);

  const [selectedDomain, setSelectedDomain] =
    useState<string | null>(null);
  const [detailTab, setDetailTab] =
    useState<DetailTab>("overview");

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
        const result = await monitoringService.websites(
          workspaceId
        );
        setSnapshot(result);
        setError("");
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to retrieve website activity."
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

  const allRecords = useMemo(() => {
    return (snapshot?.items ?? [])
      .map((item, index) =>
        parseWebsite(item, index)
      )
      .filter(
        (item): item is WebsiteRecord => item !== null
      );
  }, [snapshot]);

  const periodRecords = useMemo(() => {
    return allRecords.filter((record) =>
      inRange(record.observedAt, range)
    );
  }, [allRecords, range]);

  const categories = useMemo(() => {
    return [
      ...new Set(
        periodRecords.map((record) => record.category)
      ),
    ].sort();
  }, [periodRecords]);

  const employees = useMemo(() => {
    const map = new Map<string, string>();

    for (const record of periodRecords) {
      if (record.employeeId) {
        map.set(record.employeeId, record.employee);
      }
    }

    return [...map.entries()].sort((a, b) =>
      a[1].localeCompare(b[1])
    );
  }, [periodRecords]);

  const filteredRecords = useMemo(() => {
    return periodRecords.filter((record) => {
      return (
        (category === "all" ||
          record.category === category) &&
        (employeeFilter === "all" ||
          record.employeeId === employeeFilter)
      );
    });
  }, [periodRecords, category, employeeFilter]);

  const domains = useMemo(() => {
    const grouped = new Map<string, DomainSummary>();

    for (const record of filteredRecords) {
      let entry = grouped.get(record.domain);

      if (!entry) {
        entry = {
          domain: record.domain,
          category: record.category,
          records: [],
          totalSeconds: 0,
          employees: new Set<string>(),
          devices: new Set<string>(),
          lastSeen: 0,
          observations: 0,
        };
        grouped.set(record.domain, entry);
      }

      entry.records.push(record);
      entry.totalSeconds += record.durationSeconds;
      entry.observations += 1;

      entry.lastSeen = Math.max(
        entry.lastSeen,
        new Date(record.observedAt).getTime()
      );

      if (record.employeeId) {
        entry.employees.add(record.employeeId);
      }

      if (record.deviceId) {
        entry.devices.add(record.deviceId);
      }
    }

    return [...grouped.values()].sort(
      (a, b) =>
        b.totalSeconds - a.totalSeconds ||
        b.observations - a.observations
    );
  }, [filteredRecords]);

  const visibleDomains = useMemo(() => {
    const needle = search.trim().toLowerCase();

    return domains.filter((item) =>
      `${item.domain} ${item.category}`
        .toLowerCase()
        .includes(needle)
    );
  }, [domains, search]);

  const totalPages = Math.max(
    1,
    Math.ceil(visibleDomains.length / PAGE_SIZE)
  );

  const currentPage = Math.min(page, totalPages);

  const pageRows = visibleDomains.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const selected = useMemo(() => {
    if (!selectedDomain) return null;

    return (
      domains.find(
        (item) => item.domain === selectedDomain
      ) || null
    );
  }, [domains, selectedDomain]);

  const totalSeconds = filteredRecords.reduce(
    (sum, item) => sum + item.durationSeconds,
    0
  );

  const hasDurations = filteredRecords.some(
    (record) => record.durationSeconds > 0
  );

  const deviceCount = new Set(
    filteredRecords
      .map((record) => record.deviceId)
      .filter(Boolean)
  ).size;

  const employeeCount = new Set(
    filteredRecords
      .map((record) => record.employeeId)
      .filter(Boolean)
  ).size;

  const maxDomainSeconds = Math.max(
    1,
    ...domains.map((item) => item.totalSeconds)
  );

  const hourly = useMemo(() => {
    const buckets = Array.from(
      { length: 12 },
      (_, index) => ({
        hour: index + 7,
        seconds: 0,
        count: 0,
      })
    );

    for (const record of filteredRecords) {
      const hour = new Date(record.observedAt).getHours();
      const bucket = buckets.find(
        (entry) => entry.hour === hour
      );

      if (!bucket) continue;

      bucket.seconds += record.durationSeconds;
      bucket.count += 1;
    }

    return buckets;
  }, [filteredRecords]);

  const maxHourly = Math.max(
    1,
    ...hourly.map((item) => item.seconds)
  );

  const selectedHourly = useMemo(() => {
    const result = Array.from(
      { length: 12 },
      (_, index) => ({
        hour: index + 7,
        seconds: 0,
      })
    );

    if (!selected) return result;

    for (const record of selected.records) {
      const hour = new Date(record.observedAt).getHours();
      const bucket = result.find(
        (item) => item.hour === hour
      );

      if (bucket) {
        bucket.seconds += record.durationSeconds;
      }
    }

    return result;
  }, [selected]);

  const selectedHourlyMax = Math.max(
    1,
    ...selectedHourly.map((item) => item.seconds)
  );

  const selectedEmployees = useMemo(
    () =>
      selected
        ? buildBreakdown(
            selected.records,
            "employee"
          )
        : [],
    [selected]
  );

  const selectedDevices = useMemo(
    () =>
      selected
        ? buildBreakdown(selected.records, "device")
        : [],
    [selected]
  );

  function clearFilters() {
    setSearch("");
    setCategory("all");
    setEmployeeFilter("all");
    setPage(1);
  }

  function hourLabel(hour: number) {
    if (hour === 12) return "12 PM";
    if (hour > 12) return `${hour - 12} PM`;
    return `${hour} AM`;
  }

  return (
    <WorkspaceRequired>
      <main className="wa-page">
        <header className="wa-page-header">
          <div>
            <h1>Website Activity</h1>
            <p>
              Monitor authorized website activity and
              browsing-duration records across the
              workspace.
            </p>
          </div>

          <div className="wa-header-actions">
            <label className="wa-range">
              <CalendarDays size={16} />
              <select
                aria-label="Report period"
                value={range}
                onChange={(event) => {
                  setRange(event.target.value as Range);
                  setPage(1);
                  setSelectedDomain(null);
                }}
              >
                <option value="today">Today</option>
                <option value="yesterday">
                  Yesterday
                </option>
                <option value="7days">
                  Last 7 days
                </option>
                <option value="30days">
                  Last 30 days
                </option>
              </select>
            </label>

            <button
              type="button"
              className="wa-btn wa-btn-white"
              disabled={refreshing || !canRead}
              onClick={() => void load(true)}
            >
              <RefreshCw
                size={16}
                className={refreshing ? "wa-spin" : ""}
              />
              Refresh
            </button>

            <button
              type="button"
              className="wa-btn wa-btn-dark"
              disabled={
                !canRead || filteredRecords.length === 0
              }
              onClick={() =>
                exportWebsiteCsv(filteredRecords)
              }
            >
              <Download size={16} />
              Export report
            </button>
          </div>
        </header>

        {!canRead ? (
          <div className="wa-error">
            <AlertTriangle size={18} />
            You do not have permission to read website
            monitoring information.
          </div>
        ) : (
          <>
            {error && (
              <div className="wa-error">
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

            <section className="wa-summary">
              <MetricCard
                icon={<Globe2 size={28} />}
                label="Websites visited"
                value={String(domains.length)}
                note="Distinct domains in returned data"
              />
              <MetricCard
                icon={<Clock3 size={28} />}
                label="Recorded browsing time"
                value={
                  hasDurations
                    ? duration(totalSeconds)
                    : "—"
                }
                note={
                  hasDurations
                    ? "Sum of reported durations"
                    : "Duration not available"
                }
              />
              <MetricCard
                icon={<UsersRound size={28} />}
                label="Employees reporting"
                value={String(employeeCount)}
                note="Employees with attributed records"
              />
              <MetricCard
                icon={<Laptop2 size={28} />}
                label="Reporting devices"
                value={String(deviceCount)}
                note="Distinct device identifiers"
              />
            </section>

            <div className="wa-layout">
              <div className="wa-left">
                <section className="wa-panel">
                  <div className="wa-panel-heading">
                    <h2>
                      <Activity size={20} />
                      Website activity trend
                    </h2>
                    <span>Reported duration by hour</span>
                  </div>

                  {hasDurations ? (
                    <div className="wa-main-chart">
                      <div className="wa-y-axis">
                        <span>
                          {duration(maxHourly)}
                        </span>
                        <span>
                          {duration(maxHourly / 2)}
                        </span>
                        <span>0</span>
                      </div>

                      <div className="wa-chart-bars">
                        {hourly.map((item) => (
                          <div
                            className="wa-chart-col"
                            key={item.hour}
                            title={`${hourLabel(
                              item.hour
                            )}: ${duration(item.seconds)}`}
                          >
                            <div className="wa-chart-track">
                              <div
                                style={{
                                  height: `${
                                    (item.seconds /
                                      maxHourly) *
                                    100
                                  }%`,
                                }}
                              />
                            </div>
                            <small>
                              {hourLabel(item.hour)}
                            </small>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <Empty
                      title="No browsing-duration chart"
                      description="A website-usage aggregation endpoint is needed before real duration trends can be displayed."
                    />
                  )}

                  <div className="wa-chart-note">
                    <Info size={16} />
                    Duration bars represent the reported
                    observation times. They are not
                    verified productive working hours.
                  </div>
                </section>

                <section className="wa-panel wa-domain-panel">
                  <div className="wa-panel-heading">
                    <h2>
                      <Globe2 size={20} />
                      Website usage
                    </h2>
                    <span>
                      {visibleDomains.length} domains
                    </span>
                  </div>

                  <div className="wa-filters">
                    <label className="wa-search">
                      <Search size={17} />
                      <input
                        placeholder="Search websites..."
                        value={search}
                        onChange={(event) => {
                          setSearch(event.target.value);
                          setPage(1);
                        }}
                      />
                    </label>

                    <select
                      aria-label="Filter category"
                      value={category}
                      onChange={(event) => {
                        setCategory(event.target.value);
                        setPage(1);
                      }}
                    >
                      <option value="all">
                        All categories
                      </option>
                      {categories.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>

                    <select
                      aria-label="Filter employee"
                      value={employeeFilter}
                      onChange={(event) => {
                        setEmployeeFilter(
                          event.target.value
                        );
                        setPage(1);
                      }}
                    >
                      <option value="all">
                        All employees
                      </option>
                      {employees.map(([id, name]) => (
                        <option key={id} value={id}>
                          {name}
                        </option>
                      ))}
                    </select>

                    <button
                      type="button"
                      className="wa-clear"
                      onClick={clearFilters}
                    >
                      Clear
                    </button>
                  </div>

                  <div className="wa-table-wrap">
                    <table className="wa-usage-table">
                      <thead>
                        <tr>
                          <th>Website / Domain</th>
                          <th>Category</th>
                          <th>Recorded time</th>
                          <th>Employees</th>
                          <th>Last observed</th>
                          <th />
                        </tr>
                      </thead>

                      <tbody>
                        {pageRows.map(
                          (item, index) => (
                            <tr
                              key={item.domain}
                              className={
                                selected?.domain ===
                                item.domain
                                  ? "wa-selected-row"
                                  : ""
                              }
                            >
                              <td>
                                <button
                                  type="button"
                                  className="wa-domain-name"
                                  onClick={() => {
                                    setSelectedDomain(
                                      item.domain
                                    );
                                    setDetailTab(
                                      "overview"
                                    );
                                  }}
                                >
                                  <span
                                    className="wa-domain-icon"
                                    style={{
                                      background:
                                        DOMAIN_COLORS[
                                          index %
                                            DOMAIN_COLORS.length
                                        ],
                                    }}
                                  >
                                    {item.domain
                                      .charAt(0)
                                      .toUpperCase()}
                                  </span>
                                  <span>
                                    {item.domain}
                                  </span>
                                </button>
                              </td>

                              <td>
                                <span className="wa-category">
                                  {item.category}
                                </span>
                              </td>

                              <td>
                                <div className="wa-time-cell">
                                  <span>
                                    {item.totalSeconds > 0
                                      ? duration(
                                          item.totalSeconds
                                        )
                                      : "—"}
                                  </span>
                                  <div>
                                    <i
                                      style={{
                                        width: `${
                                          (item.totalSeconds /
                                            maxDomainSeconds) *
                                          100
                                        }%`,
                                      }}
                                    />
                                  </div>
                                </div>
                              </td>

                              <td>
                                {item.employees.size}
                              </td>

                              <td className="wa-muted">
                                {relativeTime(
                                  item.lastSeen
                                )}
                              </td>

                              <td>
                                <button
                                  type="button"
                                  className="wa-open"
                                  aria-label={`View ${item.domain} details`}
                                  onClick={() => {
                                    setSelectedDomain(
                                      item.domain
                                    );
                                    setDetailTab(
                                      "overview"
                                    );
                                  }}
                                >
                                  <ChevronRight size={17} />
                                </button>
                              </td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>

                    {loading && (
                      <div className="wa-empty">
                        <RefreshCw
                          size={27}
                          className="wa-spin"
                        />
                        <strong>
                          Loading website activity...
                        </strong>
                      </div>
                    )}

                    {!loading &&
                      pageRows.length === 0 && (
                        <Empty
                          title={
                            domains.length === 0
                              ? "No website records returned"
                              : "No matching websites"
                          }
                          description={
                            domains.length === 0
                              ? "The workspace monitoring API has not returned website-usage records for this date range."
                              : "Try adjusting your search or filters."
                          }
                        />
                      )}
                  </div>

                  <footer className="wa-pagination">
                    <span>
                      Showing{" "}
                      {visibleDomains.length
                        ? (currentPage - 1) *
                            PAGE_SIZE +
                          1
                        : 0}
                      –
                      {Math.min(
                        currentPage * PAGE_SIZE,
                        visibleDomains.length
                      )}{" "}
                      of {visibleDomains.length}
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
                        <ChevronLeft size={17} />
                      </button>

                      <span>
                        {currentPage} / {totalPages}
                      </span>

                      <button
                        type="button"
                        aria-label="Next page"
                        disabled={
                          currentPage >= totalPages
                        }
                        onClick={() =>
                          setPage((value) =>
                            Math.min(
                              totalPages,
                              value + 1
                            )
                          )
                        }
                      >
                        <ChevronRight size={17} />
                      </button>
                    </div>
                  </footer>
                </section>
              </div>

              <aside className="wa-panel wa-details">
                <div className="wa-details-heading">
                  {selected ? (
                    <>
                      <span className="wa-detail-icon">
                        <Globe2 size={26} />
                      </span>

                      <div>
                        <h2>{selected.domain}</h2>
                        <p>{selected.category}</p>
                      </div>

                      <button
                        type="button"
                        aria-label="Close details"
                        onClick={() =>
                          setSelectedDomain(null)
                        }
                      >
                        <X size={19} />
                      </button>
                    </>
                  ) : (
                    <div>
                      <h2>Website details</h2>
                      <p>
                        Select a domain to view
                        its activity.
                      </p>
                    </div>
                  )}
                </div>

                {selected ? (
                  <>
                    <div className="wa-tabs">
                      {(
                        [
                          "overview",
                          "employees",
                          "devices",
                        ] as const
                      ).map((tab) => (
                        <button
                          key={tab}
                          type="button"
                          className={
                            detailTab === tab
                              ? "wa-tab-active"
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
                        <div className="wa-detail-metrics">
                          <div>
                            <Clock3 size={20} />
                            <small>
                              Browsing duration
                            </small>
                            <strong>
                              {selected.totalSeconds > 0
                                ? duration(
                                    selected.totalSeconds
                                  )
                                : "—"}
                            </strong>
                          </div>

                          <div>
                            <UsersRound size={20} />
                            <small>Employees</small>
                            <strong>
                              {selected.employees.size}
                            </strong>
                          </div>

                          <div>
                            <Laptop2 size={20} />
                            <small>Devices</small>
                            <strong>
                              {selected.devices.size}
                            </strong>
                          </div>
                        </div>

                        <div className="wa-detail-section">
                          <div className="wa-detail-title">
                            <h3>
                              <BarChart3 size={18} />
                              Domain activity
                            </h3>
                            <span>By hour</span>
                          </div>

                          {selected.totalSeconds > 0 ? (
                            <div className="wa-mini-chart">
                              {selectedHourly.map(
                                (bucket) => (
                                  <div
                                    key={bucket.hour}
                                    title={`${hourLabel(
                                      bucket.hour
                                    )}: ${duration(
                                      bucket.seconds
                                    )}`}
                                  >
                                    <div className="wa-mini-track">
                                      <i
                                        style={{
                                          height: `${
                                            (bucket.seconds /
                                              selectedHourlyMax) *
                                            100
                                          }%`,
                                        }}
                                      />
                                    </div>
                                    <small>
                                      {hourLabel(
                                        bucket.hour
                                      )}
                                    </small>
                                  </div>
                                )
                              )}
                            </div>
                          ) : (
                            <p className="wa-hint">
                              No duration information
                              available for this domain.
                            </p>
                          )}
                        </div>

                        <div className="wa-detail-section">
                          <h3>
                            <UsersRound size={18} />
                            Top employees
                          </h3>

                          <BreakdownTable
                            rows={selectedEmployees.slice(
                              0,
                              5
                            )}
                          />
                        </div>

                        <div className="wa-detail-section">
                          <h3>
                            <ShieldCheck size={18} />
                            Domain information
                          </h3>

                          <dl className="wa-facts">
                            <div>
                              <dt>Category</dt>
                              <dd>
                                {selected.category}
                              </dd>
                            </div>
                            <div>
                              <dt>Observations</dt>
                              <dd>
                                {selected.observations}
                              </dd>
                            </div>
                            <div>
                              <dt>Last observed</dt>
                              <dd>
                                {relativeTime(
                                  selected.lastSeen
                                )}
                              </dd>
                            </div>
                            <div>
                              <dt>Domain</dt>
                              <dd>
                                {selected.domain}
                              </dd>
                            </div>
                          </dl>
                        </div>

                        <a
                          className="wa-external"
                          href={`https://${selected.domain}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <ExternalLink size={16} />
                          Open domain in browser
                        </a>
                      </>
                    )}

                    {detailTab === "employees" && (
                      <div className="wa-detail-section">
                        <h3>
                          <UsersRound size={18} />
                          Employee website usage
                        </h3>
                        <BreakdownTable
                          rows={selectedEmployees}
                        />
                      </div>
                    )}

                    {detailTab === "devices" && (
                      <div className="wa-detail-section">
                        <h3>
                          <Laptop2 size={18} />
                          Device website usage
                        </h3>
                        <BreakdownTable
                          rows={selectedDevices}
                        />
                      </div>
                    )}
                  </>
                ) : (
                  <Empty
                    title="No website selected"
                    description="Choose a domain from the website usage table to view its history and employee/device breakdown."
                  />
                )}
              </aside>
            </div>

            <div className="wa-footer">
              <Info size={16} />
              Website visits are limited to authorized
              records returned by the backend. A domain
              observed once is not assumed to be active
              for the entire hour. Historical observations
              do not indicate live browsing.
              {snapshot?.generated_at &&
                ` Updated ${new Date(
                  snapshot.generated_at
                ).toLocaleString()}.`}
            </div>
          </>
        )}

        <style jsx global>{`
          .wa-page {
            --wa-ink: #0c1939;
            --wa-muted: #697a95;
            --wa-border: #e5e8ed;
            background: #fbfaf8;
            color: var(--wa-ink);
            min-height: 100%;
            padding: 20px 21px 34px;
            font-size: 12px;
          }

          .wa-page * {
            box-sizing: border-box;
          }

          .wa-page button,
          .wa-page input,
          .wa-page select {
            font: inherit;
          }

          .wa-page button {
            cursor: pointer;
          }

          .wa-page button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
          }

          .wa-page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            margin-bottom: 18px;
          }

          .wa-page-header h1 {
            font-size: 29px;
            font-weight: 750;
            letter-spacing: -0.8px;
            line-height: 1.2;
            margin: 0;
          }

          .wa-page-header p {
            font-size: 14px;
            color: var(--wa-muted);
            margin: 5px 0 0;
          }

          .wa-header-actions {
            display: flex;
            align-items: center;
            gap: 9px;
            flex-wrap: wrap;
          }

          .wa-range {
            height: 38px;
            border: 1px solid #dfe4eb;
            background: white;
            border-radius: 7px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 0 10px;
          }

          .wa-range select {
            border: 0;
            outline: 0;
            background: transparent;
            color: var(--wa-ink);
          }

          .wa-btn {
            height: 38px;
            padding: 0 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 9px;
            border-radius: 7px;
            font-weight: 650 !important;
            white-space: nowrap;
          }

          .wa-btn-white {
            border: 1px solid #dfe4ea;
            background: white;
            color: var(--wa-ink);
          }

          .wa-btn-dark {
            background: #182330;
            border: 1px solid #182330;
            color: white;
          }

          .wa-summary {
            display: grid;
            grid-template-columns:
              repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 15px;
          }

          .wa-metric {
            border: 1px solid #eee4d2;
            background: linear-gradient(
              110deg,
              #fff9ed,
              #fffefa
            );
            min-height: 101px;
            border-radius: 11px;
            padding: 15px;
            display: flex;
            align-items: center;
            gap: 13px;
          }

          .wa-metric-icon {
            width: 51px;
            height: 51px;
            border-radius: 50%;
            flex-shrink: 0;
            display: grid;
            place-items: center;
            background: #ffefd0;
          }

          .wa-metric > div {
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 4px;
          }

          .wa-metric > div > span {
            font-size: 12px;
            font-weight: 650;
          }

          .wa-metric strong {
            font-size: 25px;
            line-height: 1.1;
            letter-spacing: -0.6px;
          }

          .wa-metric small {
            font-size: 11px;
            color: var(--wa-muted);
            line-height: 1.3;
          }

          .wa-layout {
            display: grid;
            grid-template-columns:
              minmax(0, 1.55fr)
              minmax(330px, 0.9fr);
            gap: 14px;
            align-items: start;
          }

          .wa-left {
            display: flex;
            flex-direction: column;
            gap: 14px;
            min-width: 0;
          }

          .wa-panel {
            border: 1px solid var(--wa-border);
            border-radius: 11px;
            background: #fffefa;
            overflow: hidden;
            min-width: 0;
          }

          .wa-panel-heading {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            min-height: 55px;
            padding: 12px 15px;
          }

          .wa-panel-heading h2 {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 17px;
            font-weight: 750;
            letter-spacing: -0.3px;
            margin: 0;
          }

          .wa-panel-heading > span {
            color: var(--wa-muted);
          }

          .wa-main-chart {
            height: 248px;
            display: flex;
            gap: 10px;
            padding: 18px 16px 5px;
          }

          .wa-y-axis {
            height: 199px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            font-size: 10px;
            color: var(--wa-muted);
            white-space: nowrap;
          }

          .wa-chart-bars {
            display: grid;
            grid-template-columns:
              repeat(12, minmax(0, 1fr));
            gap: 6px;
            flex: 1;
            height: 199px;
            border-bottom: 1px solid #b7c2d1;
            background: repeating-linear-gradient(
              to top,
              transparent 0,
              transparent calc(25% - 1px),
              #e8ebf0 calc(25% - 1px),
              #e8ebf0 25%
            );
          }

          .wa-chart-col {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
            min-width: 0;
          }

          .wa-chart-track {
            height: calc(100% - 28px);
            width: min(100%, 33px);
            display: flex;
            align-items: flex-end;
          }

          .wa-chart-track > div {
            width: 100%;
            border-radius: 3px 3px 0 0;
            background: #4a86f0;
          }

          .wa-chart-col small {
            display: block;
            height: 28px;
            padding-top: 7px;
            font-size: 9px;
            color: #62718d;
            white-space: nowrap;
          }

          .wa-chart-note {
            border-top: 1px solid #edf0f3;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            color: var(--wa-muted);
            line-height: 1.5;
          }

          .wa-filters {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 0 14px 14px;
            flex-wrap: wrap;
          }

          .wa-search {
            min-width: 170px;
            flex: 1 1 170px;
            height: 36px;
            border: 1px solid #e0e4ea;
            background: white;
            border-radius: 7px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 0 10px;
            color: #71829d;
          }

          .wa-search input {
            width: 100%;
            min-width: 0;
            border: 0;
            outline: 0;
            background: transparent;
            color: var(--wa-ink);
          }

          .wa-filters select {
            height: 36px;
            max-width: 165px;
            border: 1px solid #e0e4ea;
            background: white;
            border-radius: 7px;
            padding: 0 9px;
            color: var(--wa-ink);
          }

          .wa-clear {
            background: transparent;
            border: 0;
            text-decoration: underline;
            color: #516383;
          }

          .wa-table-wrap {
            overflow-x: auto;
          }

          .wa-usage-table {
            width: 100%;
            min-width: 640px;
            border-collapse: collapse;
            text-align: left;
          }

          .wa-usage-table th {
            background: #f7f7f7;
            padding: 11px 10px;
            font-size: 10px;
            font-weight: 700;
            white-space: nowrap;
          }

          .wa-usage-table td {
            padding: 11px 10px;
            font-size: 11px;
            border-top: 1px solid #e9ecf0;
            white-space: nowrap;
          }

          .wa-usage-table tr.wa-selected-row {
            background: #fff6e4;
          }

          .wa-domain-name {
            border: 0;
            padding: 0;
            background: transparent;
            display: inline-flex;
            align-items: center;
            gap: 9px;
            color: var(--wa-ink);
            font-weight: 700 !important;
          }

          .wa-domain-name > span:last-child {
            max-width: 180px;
            text-overflow: ellipsis;
            overflow: hidden;
          }

          .wa-domain-icon {
            height: 29px;
            width: 29px;
            display: grid;
            place-items: center;
            border-radius: 7px;
            color: white;
            flex-shrink: 0;
            font-weight: 750;
          }

          .wa-category {
            background: #eaf0ff;
            color: #3766b4;
            padding: 5px 8px;
            border-radius: 5px;
          }

          .wa-time-cell {
            display: flex;
            align-items: center;
            gap: 10px;
          }

          .wa-time-cell > div {
            width: 93px;
            height: 10px;
            border-radius: 7px;
            overflow: hidden;
            background: #edf0f4;
          }

          .wa-time-cell i {
            display: block;
            background: #fdb62a;
            height: 100%;
            border-radius: inherit;
          }

          .wa-muted {
            color: var(--wa-muted);
          }

          .wa-open {
            background: transparent;
            border: 0;
            color: #475a79;
          }

          .wa-pagination {
            padding: 14px 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            min-height: 63px;
            color: var(--wa-muted);
          }

          .wa-pagination > div {
            display: flex;
            align-items: center;
            gap: 9px;
          }

          .wa-pagination button {
            border: 1px solid #e4e7ed;
            background: #fff;
            border-radius: 7px;
            width: 32px;
            height: 32px;
            display: grid;
            place-items: center;
            color: var(--wa-ink);
          }

          .wa-details-heading {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 17px 15px;
          }

          .wa-detail-icon {
            display: grid;
            place-items: center;
            width: 52px;
            height: 52px;
            border-radius: 10px;
            background: #edf3ff;
            color: #3b72cf;
          }

          .wa-details-heading > div {
            min-width: 0;
            flex: 1;
          }

          .wa-details-heading h2 {
            font-size: 18px;
            margin: 0;
            overflow-wrap: anywhere;
          }

          .wa-details-heading p {
            color: var(--wa-muted);
            margin: 6px 0 0;
          }

          .wa-details-heading > button {
            align-self: flex-start;
            background: transparent;
            border: 0;
          }

          .wa-tabs {
            margin: 0 13px;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            border-bottom: 1px solid #e7e9ed;
          }

          .wa-tabs button {
            height: 39px;
            background: transparent;
            border: 0;
            color: #687790;
          }

          .wa-tabs .wa-tab-active {
            color: var(--wa-ink);
            border-bottom: 2px solid #ffae12;
            font-weight: 700;
          }

          .wa-detail-metrics {
            display: grid;
            grid-template-columns:
              repeat(3, minmax(0, 1fr));
            padding: 19px 10px;
            gap: 6px;
            border-bottom: 1px solid #e9ebee;
          }

          .wa-detail-metrics > div {
            display: flex;
            align-items: center;
            flex-direction: column;
            gap: 9px;
            text-align: center;
            border-right: 1px solid #e7e9ed;
          }

          .wa-detail-metrics > div:last-child {
            border-right: 0;
          }

          .wa-detail-metrics small {
            font-size: 10px;
            color: var(--wa-muted);
          }

          .wa-detail-metrics strong {
            font-size: 17px;
          }

          .wa-detail-section {
            padding: 15px 13px 8px;
          }

          .wa-detail-section h3,
          .wa-detail-title h3 {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 0 0 12px;
            font-size: 13px;
          }

          .wa-detail-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
          }

          .wa-detail-title span {
            color: var(--wa-muted);
          }

          .wa-mini-chart {
            display: grid;
            grid-template-columns:
              repeat(12, minmax(0, 1fr));
            gap: 3px;
            height: 165px;
          }

          .wa-mini-chart > div {
            min-width: 0;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: center;
          }

          .wa-mini-track {
            height: 135px;
            width: min(100%, 25px);
            display: flex;
            align-items: flex-end;
          }

          .wa-mini-track i {
            display: block;
            background: #547fe5;
            width: 100%;
          }

          .wa-mini-chart small {
            height: 30px;
            padding-top: 8px;
            font-size: 8px;
            color: #61718c;
            white-space: nowrap;
          }

          .wa-breakdown-table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
          }

          .wa-breakdown-table th {
            background: #f7f7f7;
            padding: 10px;
            font-size: 10px;
          }

          .wa-breakdown-table td {
            padding: 10px;
            border-top: 1px solid #e9ebef;
            font-size: 11px;
          }

          .wa-hint {
            color: var(--wa-muted);
            line-height: 1.6;
          }

          .wa-facts {
            margin: 0;
          }

          .wa-facts > div {
            display: grid;
            grid-template-columns: 0.9fr 1.1fr;
            gap: 10px;
            padding: 9px 0;
            border-bottom: 1px solid #e9ebee;
          }

          .wa-facts dt {
            color: var(--wa-muted);
          }

          .wa-facts dd {
            margin: 0;
            font-weight: 650;
            overflow-wrap: anywhere;
          }

          .wa-external {
            margin: 10px 13px 17px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 11px;
            border-radius: 7px;
            text-decoration: none;
            background: #182532;
            color: white;
            font-weight: 650;
          }

          .wa-empty {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            gap: 10px;
            padding: 28px;
            color: #8494a9;
            min-height: 225px;
          }

          .wa-empty strong {
            color: var(--wa-ink);
          }

          .wa-empty p {
            max-width: 300px;
            line-height: 1.6;
            margin: 0;
          }

          .wa-footer {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            line-height: 1.6;
            color: var(--wa-muted);
            margin-top: 14px;
          }

          .wa-footer svg {
            flex-shrink: 0;
            margin-top: 2px;
          }

          .wa-error {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 14px;
            border: 1px solid #efb8b8;
            background: #fff1f1;
            color: #b62e30;
            border-radius: 8px;
            margin-bottom: 15px;
          }

          .wa-error span {
            flex: 1;
          }

          .wa-error button {
            border: 1px solid #efb8b8;
            background: white;
            padding: 6px 10px;
            border-radius: 6px;
          }

          .wa-spin {
            animation: wa-spin 1s linear infinite;
          }

          @keyframes wa-spin {
            to {
              transform: rotate(360deg);
            }
          }

          @media (max-width: 1250px) {
            .wa-layout {
              grid-template-columns: minmax(0, 1fr);
            }
          }

          @media (max-width: 950px) {
            .wa-summary {
              grid-template-columns: repeat(2, 1fr);
            }
          }

          @media (max-width: 700px) {
            .wa-page-header {
              flex-direction: column;
              align-items: flex-start;
            }
            .wa-header-actions {
              width: 100%;
            }
          }

          @media (max-width: 520px) {
            .wa-page {
              padding: 15px 12px;
            }
            .wa-page-header h1 {
              font-size: 24px;
            }
            .wa-summary {
              grid-template-columns: 1fr;
            }
            .wa-panel-heading {
              flex-wrap: wrap;
            }
            .wa-detail-metrics {
              grid-template-columns: 1fr;
            }
            .wa-detail-metrics > div {
              border-right: 0;
              border-bottom: 1px solid #e7e9ed;
              padding: 12px;
            }
          }
        `}</style>
      </main>
    </WorkspaceRequired>
  );
}

function BreakdownTable({
  rows,
}: {
  rows: Breakdown[];
}) {
  if (!rows.length) {
    return (
      <p className="wa-hint">
        No attributed usage records available.
      </p>
    );
  }

  return (
    <table className="wa-breakdown-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Recorded time</th>
          <th>Observations</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id}>
            <td>{row.label}</td>
            <td>
              {row.seconds > 0
                ? duration(row.seconds)
                : "—"}
            </td>
            <td>{row.observations}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
