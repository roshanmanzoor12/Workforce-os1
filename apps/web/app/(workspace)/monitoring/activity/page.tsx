
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
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Download,
  Info,
  Laptop2,
  List,
  Monitor,
  Play,
  RefreshCw,
  Search,
  Square,
  UserRound,
} from "lucide-react";

import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";
import {
  monitoringService,
  type MonitoringSnapshot,
} from "@/services/monitoring.service";

type Employee = {
  id: string;
  name: string;
  department: string;
};

type Observation = {
  id: string;
  employeeId: string;
  employeeName: string;
  deviceId: string;
  state: "active" | "idle";
  idleSeconds: number;
  observedAt: string;
  lastInputAt: string | null;
};

type Segment = {
  id: string;
  state: "active" | "idle" | "no-signal";
  deviceId: string;
  start: number;
  end: number;
  count: number;
};

const GAP_MS = 3 * 60 * 1000;
const PAGE_SIZE = 8;

function localDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function dayBounds(day: string) {
  const start = new Date(`${day}T00:00:00`);
  const end = new Date(`${day}T23:59:59.999`);
  return {
    start: start.getTime(),
    end: end.getTime(),
  };
}

function toText(value: unknown, fallback = ""): string {
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  return fallback;
}

function safeDate(value: string): number {
  const result = new Date(value).getTime();
  return Number.isFinite(result) ? result : 0;
}

function timeText(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "—";

  return new Date(value).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function duration(ms: number): string {
  const minutes = Math.max(0, Math.floor(ms / 60000));
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;

  if (!hours) return `${minutes} min`;
  return `${hours}h ${remainder}m`;
}

function dateShift(day: string, offset: number): string {
  const date = new Date(`${day}T12:00:00`);
  date.setDate(date.getDate() + offset);
  return localDate(date);
}

function parseEmployees(
  snapshot: MonitoringSnapshot
): Employee[] {
  return (snapshot.items ?? [])
    .map((row) => ({
      id: toText(row.employee_id ?? row.id),
      name: toText(
        row.employee ?? row.name,
        "Unknown employee"
      ),
      department: toText(
        row.department,
        "Unassigned"
      ),
    }))
    .filter((row) => row.id);
}

function parseObservations(
  snapshot: MonitoringSnapshot
): Observation[] {
  return (snapshot.items ?? [])
    .map((row) => {
      const rawState = toText(
        row.status ?? row.state
      ).toLowerCase();

      return {
        id: toText(row.id),
        employeeId: toText(row.employee_id),
        employeeName: toText(
          row.employee,
          "Unknown employee"
        ),
        deviceId: toText(row.device_id),
        state: rawState === "idle"
          ? ("idle" as const)
          : ("active" as const),
        idleSeconds: Math.max(
          0,
          Number(row.idle_seconds) || 0
        ),
        observedAt: toText(
          row.started_at ??
          row.observed_at ??
          row.captured_at
        ),
        lastInputAt: row.last_input_at
          ? toText(row.last_input_at)
          : null,
        validState: ["active", "idle"].includes(rawState),
      };
    })
    .filter(
      (row) =>
        row.id &&
        row.employeeId &&
        row.deviceId &&
        safeDate(row.observedAt) > 0 &&
        row.validState
    )
    .map(({ validState: _validState, ...row }) => row);
}

function buildSegments(rows: Observation[]): Segment[] {
  if (!rows.length) return [];

  const byDevice = new Map<string, Observation[]>();

  for (const row of rows) {
    const group = byDevice.get(row.deviceId) || [];
    group.push(row);
    byDevice.set(row.deviceId, group);
  }

  const result: Segment[] = [];

  for (const [deviceId, group] of byDevice) {
    const sorted = [...group].sort(
      (a, b) =>
        safeDate(a.observedAt) -
        safeDate(b.observedAt)
    );

    let current: Segment | null = null;

    for (const row of sorted) {
      const timestamp = safeDate(row.observedAt);

      if (!current) {
        current = {
          id: row.id,
          state: row.state,
          deviceId,
          start: timestamp,
          end: timestamp,
          count: 1,
        };
        continue;
      }

      const gap = timestamp - current.end;

      if (gap > GAP_MS) {
        result.push(current);
        result.push({
          id: `gap-${current.id}-${row.id}`,
          state: "no-signal",
          deviceId,
          start: current.end,
          end: timestamp,
          count: 0,
        });

        current = {
          id: row.id,
          state: row.state,
          deviceId,
          start: timestamp,
          end: timestamp,
          count: 1,
        };
      } else if (current.state === row.state) {
        current.end = timestamp;
        current.count += 1;
      } else {
        result.push(current);
        current = {
          id: row.id,
          state: row.state,
          deviceId,
          start: timestamp,
          end: timestamp,
          count: 1,
        };
      }
    }

    if (current) result.push(current);
  }

  return result.sort((a, b) => a.start - b.start);
}

function exportCsv(rows: Observation[]): void {
  const data = [
    [
      "Employee",
      "Employee ID",
      "Device ID",
      "State",
      "Idle seconds",
      "Observed at",
      "Last input at",
    ],
    ...rows.map((row) => [
      row.employeeName,
      row.employeeId,
      row.deviceId,
      row.state,
      String(row.idleSeconds),
      row.observedAt,
      row.lastInputAt || "",
    ]),
  ];

  const escapeCell = (text: string) => {
    const safe = /^[=+\-@\t\r]/.test(text)
      ? `'${text}`
      : text;
    return `"${safe.replaceAll('"', '""')}"`;
  };

  const csv = data
    .map((row) => row.map(escapeCell).join(","))
    .join("\r\n");

  const url = URL.createObjectURL(
    new Blob(["\uFEFF", csv], {
      type: "text/csv;charset=utf-8",
    })
  );

  const link = document.createElement("a");
  link.href = url;
  link.download = "workforce-activity-observations.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Metric({
  icon,
  label,
  value,
  description,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  description: string;
  tone: "green" | "red" | "blue" | "yellow";
}) {
  return (
    <div className="at-metric">
      <div className={`at-metric-icon at-tone-${tone}`}>
        {icon}
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{description}</small>
      </div>
    </div>
  );
}

export default function MonitoringActivityPage() {
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

  const [day, setDay] = useState(() =>
    localDate(new Date())
  );
  const [employeeId, setEmployeeId] = useState("");
  const [deviceId, setDeviceId] = useState("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const [employees, setEmployees] = useState<Employee[]>([]);
  const [observations, setObservations] = useState<
    Observation[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [generatedAt, setGeneratedAt] = useState("");

  const load = useCallback(
    async (quiet = false) => {
      if (!workspaceId || !canRead) {
        setLoading(false);
        return;
      }

      if (quiet) setRefreshing(true);
      else setLoading(true);

      try {
        const [employeeResult, activityResult] =
          await Promise.all([
            monitoringService.employees(workspaceId),
            monitoringService.activity(workspaceId),
          ]);

        setEmployees(parseEmployees(employeeResult));
        setObservations(parseObservations(activityResult));
        setGeneratedAt(activityResult.generated_at || "");
        setError("");
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load activity records."
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

  const selectedEmployee =
    employees.find((item) => item.id === employeeId) ||
    employees[0] ||
    null;

  const selectedEmployeeId = selectedEmployee?.id || "";
  const bounds = useMemo(() => dayBounds(day), [day]);

  const dayRows = useMemo(
    () =>
      observations
        .filter((row) => {
          const timestamp = safeDate(row.observedAt);
          return (
            row.employeeId === selectedEmployeeId &&
            timestamp >= bounds.start &&
            timestamp <= bounds.end
          );
        })
        .sort(
          (a, b) =>
            safeDate(a.observedAt) -
            safeDate(b.observedAt)
        ),
    [observations, selectedEmployeeId, bounds]
  );

  const availableDevices = useMemo(
    () =>
      [...new Set(
        dayRows.map((row) => row.deviceId)
      )].sort(),
    [dayRows]
  );

  const selectedRows = useMemo(
    () =>
      dayRows.filter(
        (row) =>
          deviceId === "all" ||
          row.deviceId === deviceId
      ),
    [dayRows, deviceId]
  );

  const segments = useMemo(
    () => buildSegments(selectedRows),
    [selectedRows]
  );

  const firstSignal = selectedRows[0];
  const lastSignal = selectedRows[
    selectedRows.length - 1
  ];

  const firstAt = firstSignal
    ? safeDate(firstSignal.observedAt)
    : null;
  const lastAt = lastSignal
    ? safeDate(lastSignal.observedAt)
    : null;

  const activeMs = segments
    .filter((segment) => segment.state === "active")
    .reduce(
      (total, segment) =>
        total + Math.max(0, segment.end - segment.start),
      0
    );

  const idleMs = segments
    .filter((segment) => segment.state === "idle")
    .reduce(
      (total, segment) =>
        total + Math.max(0, segment.end - segment.start),
      0
    );

  const noSignalMs = segments
    .filter((segment) => segment.state === "no-signal")
    .reduce(
      (total, segment) =>
        total + Math.max(0, segment.end - segment.start),
      0
    );

  const observedSpan =
    firstAt !== null && lastAt !== null
      ? Math.max(0, lastAt - firstAt)
      : 0;

  const hourlyBuckets = useMemo(() => {
    const values = Array.from({ length: 24 }, (_, hour) => ({
      hour,
      active: 0,
      idle: 0,
    }));

    for (const row of selectedRows) {
      const hour = new Date(row.observedAt).getHours();
      const bucket = values[hour];

      if (!bucket) continue;

      if (row.state === "active") bucket.active += 1;
      else bucket.idle += 1;
    }

    return values;
  }, [selectedRows]);

  const maxBucket = Math.max(
    1,
    ...hourlyBuckets.map(
      (bucket) => bucket.active + bucket.idle
    )
  );

  const chartRows = hourlyBuckets.filter(
    (bucket) => bucket.hour >= 8 && bucket.hour <= 18
  );

  const matchingObservations = useMemo(() => {
    const needle = search.trim().toLowerCase();

    return [...selectedRows]
      .reverse()
      .filter(
        (row) =>
          !needle ||
          [
            row.state,
            row.deviceId,
            row.employeeName,
            row.observedAt,
          ]
            .join(" ")
            .toLowerCase()
            .includes(needle)
      );
  }, [selectedRows, search]);

  const totalPages = Math.max(
    1,
    Math.ceil(matchingObservations.length / PAGE_SIZE)
  );
  const currentPage = Math.min(page, totalPages);

  const visibleObservations = matchingObservations.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  return (
    <WorkspaceRequired>
      <main className="at-page">
        <header className="at-header">
          <div>
            <h1>Activity Timeline</h1>
            <p>
              View device activity observations and
              recorded signal gaps for an employee.
            </p>
          </div>

          <div className="at-header-actions">
            <label className="at-date-control">
              <CalendarDays size={17} />
              <input
                type="date"
                aria-label="Activity date"
                value={day}
                onChange={(event) => {
                  setDay(event.target.value);
                  setPage(1);
                }}
              />
            </label>

            <button
              type="button"
              className="at-btn at-btn-dark"
              disabled={!canRead || refreshing}
              onClick={() => void load(true)}
            >
              <RefreshCw
                size={17}
                className={refreshing ? "at-spin" : ""}
              />
              Refresh
            </button>
          </div>
        </header>

        {!canRead ? (
          <div className="at-alert">
            <AlertTriangle size={18} />
            You do not have access to employee activity records.
          </div>
        ) : (
          <>
            {error && (
              <div className="at-alert">
                <AlertTriangle size={18} />
                {error}
                <button
                  type="button"
                  onClick={() => void load()}
                >
                  Retry
                </button>
              </div>
            )}

            <section className="at-filters-panel">
              <label>
                <UserRound size={20} />
                <strong>Employee</strong>
                <select
                  aria-label="Select employee"
                  value={selectedEmployeeId}
                  onChange={(event) => {
                    setEmployeeId(event.target.value);
                    setDeviceId("all");
                    setPage(1);
                  }}
                >
                  {employees.length === 0 && (
                    <option value="">No employees</option>
                  )}
                  {employees.map((employee) => (
                    <option
                      key={employee.id}
                      value={employee.id}
                    >
                      {employee.name}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <CalendarDays size={20} />
                <strong>Date</strong>
                <input
                  type="date"
                  aria-label="Selected date"
                  value={day}
                  onChange={(event) => {
                    setDay(event.target.value);
                    setPage(1);
                  }}
                />
              </label>

              <label>
                <Laptop2 size={20} />
                <strong>Device</strong>
                <select
                  aria-label="Select device"
                  value={
                    deviceId === "all" ||
                    availableDevices.includes(deviceId)
                      ? deviceId
                      : "all"
                  }
                  onChange={(event) => {
                    setDeviceId(event.target.value);
                    setPage(1);
                  }}
                >
                  <option value="all">All devices</option>
                  {availableDevices.map((device) => (
                    <option key={device} value={device}>
                      {device}
                    </option>
                  ))}
                </select>
              </label>
            </section>

            <section className="at-metrics">
              <Metric
                icon={<Play size={27} />}
                label="First signal"
                value={timeText(firstAt)}
                description="First observed device state"
                tone="green"
              />

              <Metric
                icon={<Square size={25} />}
                label="Last signal"
                value={timeText(lastAt)}
                description="Last observed device state"
                tone="red"
              />

              <Metric
                icon={<Clock3 size={30} />}
                label="Observed span"
                value={
                  selectedRows.length
                    ? duration(observedSpan)
                    : "—"
                }
                description="First to last observation"
                tone="blue"
              />

              <Metric
                icon={<Clock3 size={30} />}
                label="Idle intervals"
                value={
                  selectedRows.length
                    ? duration(idleMs)
                    : "—"
                }
                description="Estimated from sampled states"
                tone="yellow"
              />
            </section>

            <div className="at-upper-grid">
              <section className="at-card">
                <div className="at-card-heading">
                  <h2>
                    <List size={21} />
                    Timeline of activity
                  </h2>
                  <span>{selectedRows.length} signals</span>
                </div>

                <div className="at-timeline">
                  {loading ? (
                    <div className="at-empty">
                      <RefreshCw
                        size={25}
                        className="at-spin"
                      />
                      Loading activity...
                    </div>
                  ) : segments.length === 0 ? (
                    <div className="at-empty">
                      <Activity size={29} />
                      <strong>No activity for this selection</strong>
                      <p>
                        Only observations linked to an
                        authorized employee can appear here.
                      </p>
                    </div>
                  ) : (
                    segments.slice(0, 15).map((segment) => (
                      <div
                        className="at-timeline-row"
                        key={segment.id}
                      >
                        <time>{timeText(segment.start)}</time>
                        <span
                          className={`at-event-dot at-event-${segment.state}`}
                        />
                        <div>
                          <strong>
                            {segment.state === "active"
                              ? "Active signal"
                              : segment.state === "idle"
                                ? "Idle signal"
                                : "No signal"}
                          </strong>
                          <small>
                            {segment.state === "no-signal"
                              ? `No observations for ${duration(
                                  segment.end - segment.start
                                )}`
                              : `${segment.count} observation(s) • ${segment.deviceId}`}
                          </small>
                        </div>
                        <span className="at-event-source">
                          {segment.state === "no-signal"
                            ? "Inferred gap"
                            : "Device agent"}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </section>

              <section className="at-card">
                <div className="at-card-heading">
                  <h2>
                    <Activity size={21} />
                    Daily signal chart
                  </h2>
                  <div className="at-legend">
                    <span>
                      <i className="at-green" />
                      Active
                    </span>
                    <span>
                      <i className="at-yellow" />
                      Idle
                    </span>
                    <span>
                      <i className="at-gray" />
                      No data
                    </span>
                  </div>
                </div>

                <div className="at-chart">
                  <div className="at-y-axis">
                    <span>{maxBucket}</span>
                    <span>
                      {Math.ceil(maxBucket / 2)}
                    </span>
                    <span>0</span>
                  </div>

                  <div className="at-chart-grid">
                    {chartRows.map((bucket) => (
                      <div
                        className="at-bar-column"
                        key={bucket.hour}
                        title={`${bucket.hour}:00 — ${bucket.active} active, ${bucket.idle} idle observations`}
                      >
                        <div className="at-bar">
                          <div
                            className="at-bar-active"
                            style={{
                              height: `${
                                (bucket.active / maxBucket) *
                                100
                              }%`,
                            }}
                          />
                          <div
                            className="at-bar-idle"
                            style={{
                              height: `${
                                (bucket.idle / maxBucket) *
                                100
                              }%`,
                            }}
                          />
                        </div>
                        <span>
                          {bucket.hour > 12
                            ? `${bucket.hour - 12} PM`
                            : bucket.hour === 12
                              ? "12 PM"
                              : `${bucket.hour} AM`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="at-chart-note">
                  <Info size={17} />
                  Bars count recorded active/idle
                  observations. Empty hours indicate no
                  returned data, not confirmed inactivity.
                </div>
              </section>
            </div>

            <section className="at-card at-records">
              <div className="at-card-heading">
                <h2>
                  <Monitor size={21} />
                  Activity observations
                </h2>

                <div className="at-table-actions">
                  <label>
                    <Search size={16} />
                    <input
                      value={search}
                      onChange={(event) => {
                        setSearch(event.target.value);
                        setPage(1);
                      }}
                      placeholder="Search observations..."
                    />
                  </label>

                  <button
                    type="button"
                    disabled={selectedRows.length === 0}
                    onClick={() => exportCsv(selectedRows)}
                  >
                    <Download size={16} />
                    Export
                  </button>
                </div>
              </div>

              <div className="at-table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Observed time</th>
                      <th>Employee</th>
                      <th>Device</th>
                      <th>Signal state</th>
                      <th>Idle seconds</th>
                      <th>Last input</th>
                    </tr>
                  </thead>

                  <tbody>
                    {visibleObservations.map((row) => (
                      <tr key={row.id}>
                        <td>
                          {timeText(safeDate(row.observedAt))}
                        </td>
                        <td>{row.employeeName}</td>
                        <td className="at-muted">
                          {row.deviceId}
                        </td>
                        <td>
                          <span className="at-state">
                            <i
                              className={
                                row.state === "active"
                                  ? "at-green"
                                  : "at-yellow"
                              }
                            />
                            {row.state === "active"
                              ? "Active"
                              : "Idle"}
                          </span>
                        </td>
                        <td>{row.idleSeconds}s</td>
                        <td>
                          {row.lastInputAt
                            ? timeText(
                                safeDate(row.lastInputAt)
                              )
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {!loading &&
                  visibleObservations.length === 0 && (
                    <div className="at-empty">
                      <CheckCircle2 size={25} />
                      <strong>
                        No observations returned
                      </strong>
                      <p>
                        Try another employee, device, or
                        date.
                      </p>
                    </div>
                  )}
              </div>

              <footer className="at-pagination">
                <span>
                  Showing{" "}
                  {matchingObservations.length
                    ? (currentPage - 1) *
                        PAGE_SIZE +
                      1
                    : 0}
                  –
                  {Math.min(
                    currentPage * PAGE_SIZE,
                    matchingObservations.length
                  )}{" "}
                  of {matchingObservations.length}
                </span>

                <div>
                  <button
                    type="button"
                    disabled={currentPage === 1}
                    onClick={() =>
                      setPage((value) =>
                        Math.max(1, value - 1)
                      )
                    }
                  >
                    <ChevronLeft size={16} />
                  </button>

                  <span>
                    Page {currentPage} of {totalPages}
                  </span>

                  <button
                    type="button"
                    disabled={currentPage >= totalPages}
                    onClick={() =>
                      setPage((value) =>
                        Math.min(totalPages, value + 1)
                      )
                    }
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </footer>
            </section>

            <div className="at-footer-note">
              <Info size={16} />
              <span>
                Data is limited to records returned by
                the monitoring API. Active intervals:
                {` ${duration(activeMs)}`} • Idle intervals:
                {` ${duration(idleMs)}`} • Signal gaps:
                {` ${duration(noSignalMs)}`}.
                These are estimates derived from samples,
                not verified attendance or payable time.
                {generatedAt &&
                  ` Last API update: ${new Date(
                    generatedAt
                  ).toLocaleString()}.`}
              </span>
            </div>
          </>
        )}

        <style jsx global>{`
          .at-page {
            --at-ink: #0e1c3d;
            --at-muted: #71809b;
            --at-border: #e5e8ec;
            background: #fbfaf8;
            color: var(--at-ink);
            padding: 20px 21px 30px;
            font-size: 12px;
            min-height: 100%;
          }
          .at-page * {
            box-sizing: border-box;
          }
          .at-page button,
          .at-page select,
          .at-page input {
            font: inherit;
          }
          .at-page button {
            cursor: pointer;
          }
          .at-page button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
          }
          .at-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            margin-bottom: 19px;
          }
          .at-header h1 {
            font-size: 29px;
            font-weight: 750;
            letter-spacing: -0.75px;
            line-height: 1.15;
            margin: 0;
          }
          .at-header p {
            font-size: 14px;
            color: var(--at-muted);
            margin: 5px 0 0;
          }
          .at-header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
          }
          .at-date-control {
            border: 1px solid #e2e5eb;
            border-radius: 8px;
            background: #fff;
            display: flex;
            align-items: center;
            gap: 8px;
            height: 38px;
            padding: 0 11px;
          }
          .at-date-control input {
            background: transparent;
            border: 0;
            color: var(--at-ink);
            outline: none;
          }
          .at-btn {
            border: 1px solid #dfe3e9;
            background: #fff;
            border-radius: 7px;
            padding: 0 14px;
            height: 38px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-weight: 650 !important;
          }
          .at-btn-dark {
            border-color: #172331;
            background: #172331;
            color: white;
          }
          .at-filters-panel {
            display: grid;
            grid-template-columns: 1fr 1.3fr 1fr;
            gap: 20px;
            background: #fffdf7;
            border: 1px solid #eee9dc;
            border-radius: 11px;
            padding: 15px 20px;
            margin-bottom: 15px;
          }
          .at-filters-panel label {
            display: flex;
            align-items: center;
            gap: 11px;
            min-width: 0;
          }
          .at-filters-panel label > strong {
            white-space: nowrap;
            font-size: 13px;
          }
          .at-filters-panel select,
          .at-filters-panel input {
            height: 38px;
            min-width: 0;
            flex: 1;
            border: 1px solid #e0e4eb;
            background: #fff;
            border-radius: 7px;
            padding: 0 10px;
            color: var(--at-ink);
          }
          .at-metrics {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 13px;
            margin-bottom: 15px;
          }
          .at-metric {
            background: #fffefa;
            border: 1px solid var(--at-border);
            border-radius: 11px;
            min-height: 110px;
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 17px;
          }
          .at-metric-icon {
            width: 57px;
            height: 57px;
            border-radius: 50%;
            flex-shrink: 0;
            display: grid;
            place-items: center;
          }
          .at-tone-green {
            background: #e1f7e8;
            color: #1aae67;
          }
          .at-tone-red {
            background: #ffe8e8;
            color: #f34142;
          }
          .at-tone-blue {
            background: #e7f1ff;
            color: #087de3;
          }
          .at-tone-yellow {
            background: #fff0ca;
            color: #e99b00;
          }
          .at-metric > div:last-child {
            display: flex;
            flex-direction: column;
            gap: 4px;
            min-width: 0;
          }
          .at-metric span {
            font-size: 13px;
            font-weight: 650;
          }
          .at-metric strong {
            font-size: 26px;
            letter-spacing: -0.7px;
            line-height: 1.1;
          }
          .at-metric small {
            color: var(--at-muted);
            font-size: 11px;
            line-height: 1.4;
          }
          .at-upper-grid {
            display: grid;
            grid-template-columns: 0.9fr 1.1fr;
            gap: 14px;
            margin-bottom: 15px;
          }
          .at-card {
            background: #fffefa;
            border: 1px solid var(--at-border);
            border-radius: 11px;
            overflow: hidden;
            min-width: 0;
          }
          .at-card-heading {
            min-height: 57px;
            padding: 14px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            border-bottom: 1px solid #edf0f2;
          }
          .at-card-heading h2 {
            margin: 0;
            font-size: 17px;
            font-weight: 740;
            display: flex;
            align-items: center;
            gap: 10px;
            letter-spacing: -0.25px;
          }
          .at-card-heading > span {
            color: var(--at-muted);
          }
          .at-timeline {
            padding: 7px 20px 14px;
            min-height: 283px;
            max-height: 390px;
            overflow-y: auto;
          }
          .at-timeline-row {
            display: grid;
            grid-template-columns: 55px 14px minmax(0, 1fr) auto;
            align-items: start;
            gap: 13px;
            min-height: 65px;
            padding: 13px 0;
            border-bottom: 1px solid #ebedf0;
          }
          .at-timeline-row:last-child {
            border-bottom: 0;
          }
          .at-timeline-row time {
            font-weight: 650;
            font-size: 11px;
            white-space: nowrap;
          }
          .at-event-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-top: 1px;
          }
          .at-event-active {
            background: #27bd7d;
          }
          .at-event-idle {
            background: #ffb91f;
          }
          .at-event-no-signal {
            background: #aeb7c5;
          }
          .at-timeline-row > div {
            display: flex;
            flex-direction: column;
            min-width: 0;
            gap: 6px;
          }
          .at-timeline-row strong {
            font-size: 12px;
          }
          .at-timeline-row small {
            color: var(--at-muted);
            overflow-wrap: anywhere;
            line-height: 1.4;
          }
          .at-event-source {
            color: var(--at-muted);
            font-size: 10px;
          }
          .at-legend {
            display: flex;
            gap: 11px;
            flex-wrap: wrap;
          }
          .at-legend span,
          .at-state {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
            color: #596b86;
          }
          .at-legend i,
          .at-state i {
            height: 10px;
            width: 10px;
            border-radius: 50%;
            display: inline-block;
          }
          .at-green {
            background: #24bd79;
          }
          .at-yellow {
            background: #ffb71b;
          }
          .at-gray {
            background: #abb4c1;
          }
          .at-chart {
            height: 260px;
            padding: 20px 19px 8px;
            display: flex;
            gap: 8px;
          }
          .at-y-axis {
            height: 206px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #5d6e8c;
          }
          .at-chart-grid {
            flex: 1;
            display: grid;
            grid-template-columns: repeat(11, minmax(0, 1fr));
            gap: 7px;
            min-width: 0;
            border-bottom: 1px solid #b9c3d2;
            background: repeating-linear-gradient(
              to top,
              transparent 0,
              transparent calc(25% - 1px),
              #e8eaf0 calc(25% - 1px),
              #e8eaf0 25%
            );
            height: 206px;
          }
          .at-bar-column {
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
            min-width: 0;
            position: relative;
          }
          .at-bar {
            width: min(100%, 32px);
            height: calc(100% - 30px);
            display: flex;
            flex-direction: column-reverse;
            justify-content: flex-start;
          }
          .at-bar-active {
            width: 100%;
            background: #2bbd7c;
            min-height: 0;
          }
          .at-bar-idle {
            width: 100%;
            background: #ffbe26;
            min-height: 0;
          }
          .at-bar-column > span {
            height: 26px;
            padding-top: 7px;
            color: #5f7190;
            white-space: nowrap;
            font-size: 10px;
          }
          .at-chart-note {
            border-top: 1px solid #edf0f2;
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 13px 17px;
            color: var(--at-muted);
            line-height: 1.5;
          }
          .at-records {
            margin-bottom: 14px;
          }
          .at-table-actions {
            display: flex;
            align-items: center;
            gap: 9px;
          }
          .at-table-actions label {
            border: 1px solid #e2e6eb;
            border-radius: 7px;
            padding: 0 10px;
            background: #fff;
            height: 35px;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .at-table-actions input {
            border: 0;
            outline: 0;
            background: transparent;
            width: 155px;
            color: var(--at-ink);
          }
          .at-table-actions button {
            height: 35px;
            border: 1px solid #dfe3e9;
            border-radius: 7px;
            background: white;
            padding: 0 12px;
            display: inline-flex;
            align-items: center;
            gap: 7px;
            color: var(--at-ink);
          }
          .at-table-wrapper {
            overflow-x: auto;
          }
          .at-table-wrapper table {
            min-width: 780px;
            width: 100%;
            border-collapse: collapse;
            text-align: left;
          }
          .at-table-wrapper th {
            background: #f7f7f7;
            padding: 11px 15px;
            font-size: 11px;
            white-space: nowrap;
          }
          .at-table-wrapper td {
            border-top: 1px solid #e9ebef;
            padding: 10px 15px;
            font-size: 11px;
            white-space: nowrap;
          }
          .at-muted {
            color: var(--at-muted);
          }
          .at-pagination {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            min-height: 61px;
            padding: 12px 16px;
            color: var(--at-muted);
          }
          .at-pagination > div {
            display: flex;
            align-items: center;
            gap: 10px;
          }
          .at-pagination button {
            border: 1px solid #e3e6eb;
            border-radius: 7px;
            background: white;
            color: var(--at-ink);
            height: 32px;
            width: 34px;
            display: grid;
            place-items: center;
          }
          .at-footer-note {
            display: flex;
            align-items: flex-start;
            gap: 9px;
            color: var(--at-muted);
            line-height: 1.6;
          }
          .at-footer-note svg {
            flex-shrink: 0;
            margin-top: 2px;
          }
          .at-empty {
            min-height: 215px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 11px;
            padding: 22px;
            color: #8b97aa;
            text-align: center;
          }
          .at-empty strong {
            color: var(--at-ink);
          }
          .at-empty p {
            max-width: 295px;
            margin: 0;
            line-height: 1.6;
          }
          .at-alert {
            padding: 12px 15px;
            display: flex;
            align-items: center;
            gap: 9px;
            border: 1px solid #f0b4b4;
            border-radius: 8px;
            color: #b22d2d;
            background: #fff1f1;
            margin-bottom: 15px;
          }
          .at-alert button {
            margin-left: auto;
            padding: 5px 10px;
            border: 1px solid #efb9b9;
            background: white;
            border-radius: 6px;
          }
          .at-spin {
            animation: at-spin 1s linear infinite;
          }
          @keyframes at-spin {
            to {
              transform: rotate(360deg);
            }
          }
          @media (max-width: 1250px) {
            .at-upper-grid {
              grid-template-columns: 1fr;
            }
            .at-filters-panel {
              grid-template-columns: 1fr;
              gap: 10px;
            }
          }
          @media (max-width: 800px) {
            .at-metrics {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .at-header {
              flex-direction: column;
              align-items: flex-start;
            }
            .at-header-actions {
              flex-wrap: wrap;
            }
          }
          @media (max-width: 520px) {
            .at-page {
              padding: 15px 12px;
            }
            .at-header h1 {
              font-size: 24px;
            }
            .at-metrics {
              grid-template-columns: 1fr;
            }
            .at-card-heading {
              flex-wrap: wrap;
            }
            .at-pagination {
              flex-wrap: wrap;
            }
          }
        `}</style>
      </main>
    </WorkspaceRequired>
  );
}
