
"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  Download,
  Info,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  UserRound,
  UsersRound,
  X,
} from "lucide-react";

import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";
import { attendanceService } from "@/services/attendance.service";
import {
  employeesService,
  type Employee,
} from "@/services/employees.service";
import type {
  AttendanceEventPublic,
  AttendanceRecordPublic,
  AttendanceStatus,
} from "@/types/attendance";

type FilterStatus = AttendanceStatus | "all";
type ReviewFilter = "all" | "needs_review";

const PAGE_SIZE = 10;

const STATUS_LABELS: Record<AttendanceStatus, string> = {
  present: "Present",
  absent: "Absent",
  late: "Late",
  half_day: "Half day",
  on_leave: "On leave",
  holiday: "Holiday",
};

function localDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function timeString(value: string | null): string {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function dateTimeString(value: string | null): string {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function minutesString(value: number): string {
  const total = Math.max(0, Math.floor(value));
  const hours = Math.floor(total / 60);
  const minutes = total % 60;

  return `${hours}h ${String(minutes).padStart(2, "0")}m`;
}

function employeeName(employee?: Employee): string {
  if (!employee) return "Employee unavailable";

  return (
    employee.full_name?.trim() ||
    `${employee.first_name} ${employee.last_name}`.trim() ||
    employee.employee_code ||
    "Unknown employee"
  );
}

function initials(value: string): string {
  return value
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("") || "?";
}

function needsReview(row: AttendanceRecordPublic): boolean {
  return (
    (row.status === "present" ||
      row.status === "late" ||
      row.status === "half_day") &&
    (!row.check_in_at || !row.check_out_at)
  );
}

function reviewDescription(row: AttendanceRecordPublic): string {
  if (!row.check_in_at && !row.check_out_at) {
    return "Recorded attendance has no check-in or check-out.";
  }

  if (!row.check_in_at) {
    return "A check-out exists, but check-in is missing.";
  }

  return "A check-in exists, but check-out is missing.";
}

function exportCsv(
  records: AttendanceRecordPublic[],
  employees: Map<string, Employee>
) {
  const data = [
    [
      "Date",
      "Employee",
      "Employee ID",
      "Department ID",
      "Status",
      "Check in",
      "Check out",
      "Worked minutes",
      "Break minutes",
      "Source",
      "Notes",
      "Needs review",
    ],
    ...records.map((row) => {
      const employee = employees.get(row.employee_id);

      return [
        row.attendance_date,
        employeeName(employee),
        row.employee_id,
        employee?.department_id ?? "",
        row.status,
        row.check_in_at || "",
        row.check_out_at || "",
        String(row.worked_minutes),
        String(row.break_minutes),
        row.source,
        row.notes || "",
        needsReview(row) ? "Yes" : "No",
      ];
    }),
  ];

  const cell = (value: string): string => {
    const safe = /^[=+\-@\t\r]/.test(value)
      ? `'${value}`
      : value;

    return `"${safe.replaceAll('"', '""')}"`;
  };

  const csv = data
    .map((row) => row.map(cell).join(","))
    .join("\r\n");

  const blob = new Blob(["\uFEFF", csv], {
    type: "text/csv;charset=utf-8",
  });

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = "monitoring-attendance.csv";

  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Metric({
  icon,
  label,
  value,
  detail,
  tone,
}: {
  icon: ReactNode;
  label: string;
  value: number;
  detail: string;
  tone: "green" | "orange" | "red" | "purple";
}) {
  return (
    <div className="ma-metric">
      <div className={`ma-metric-icon ma-${tone}`}>
        {icon}
      </div>

      <div className="ma-metric-copy">
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: AttendanceStatus }) {
  return (
    <span className={`ma-status ma-status-${status}`}>
      <i />
      {STATUS_LABELS[status]}
    </span>
  );
}

export default function MonitoringAttendancePage() {
  const {
    workspaceId,
    permissions,
    navigationView,
  } = useWorkspace();

  const canRead = hasAnyPermission(
    permissions,
    [
      "attendance.all.read",
      "attendance.team.read",
      "attendance.self.read",
      "monitoring.all.read",
      "monitoring.team.read",
      "monitoring.self.read",
    ],
    navigationView
  );

  const canManage = hasAnyPermission(
    permissions,
    ["attendance.manage", "attendance.approve"],
    navigationView
  );

  const [day, setDay] = useState(() =>
    localDate(new Date())
  );

  const [status, setStatus] = useState<FilterStatus>("all");
  const [reviewFilter, setReviewFilter] =
    useState<ReviewFilter>("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const [employees, setEmployees] = useState<Employee[]>([]);
  const [records, setRecords] = useState<
    AttendanceRecordPublic[]
  >([]);

  const [selectedId, setSelectedId] = useState<string | null>(
    null
  );
  const [events, setEvents] = useState<
    AttendanceEventPublic[]
  >([]);
  const [detailLoading, setDetailLoading] = useState(false);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  const [editOpen, setEditOpen] = useState(false);
  const [editStatus, setEditStatus] =
    useState<AttendanceStatus>("present");
  const [editNotes, setEditNotes] = useState("");

  const employeeMap = useMemo(
    () =>
      new Map(
        employees.map((employee) => [
          employee.id,
          employee,
        ])
      ),
    [employees]
  );

  const load = useCallback(
    async (quiet = false) => {
      if (!workspaceId || !canRead) {
        setLoading(false);
        return;
      }

      if (quiet) setRefreshing(true);
      else setLoading(true);

      try {
        const [attendanceResponse, employeeResponse] =
          await Promise.all([
            attendanceService.list(workspaceId, {
              startDate: day,
              endDate: day,
            }),
            employeesService.list(workspaceId, {
              includeInactive: true,
            }),
          ]);

        setRecords(attendanceResponse.attendance ?? []);
        setEmployees(employeeResponse.employees ?? []);
        setError("");
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load attendance records."
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [workspaceId, canRead, day]
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

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();

    return records
      .filter((record) => {
        const employee = employeeMap.get(
          record.employee_id
        );

        const matchSearch =
          !needle ||
          [
            employeeName(employee),
            employee?.employee_code,
            employee?.job_title,
            record.employee_id,
          ]
            .join(" ")
            .toLowerCase()
            .includes(needle);

        return (
          matchSearch &&
          (status === "all" || record.status === status) &&
          (reviewFilter === "all" ||
            needsReview(record))
        );
      })
      .sort((a, b) =>
        employeeName(employeeMap.get(a.employee_id))
          .localeCompare(
            employeeName(employeeMap.get(b.employee_id))
          )
      );
  }, [
    records,
    employeeMap,
    search,
    status,
    reviewFilter,
  ]);

  const totals = useMemo(
    () => ({
      present: records.filter(
        (row) => row.status === "present"
      ).length,
      late: records.filter(
        (row) => row.status === "late"
      ).length,
      absent: records.filter(
        (row) => row.status === "absent"
      ).length,
      leave: records.filter(
        (row) => row.status === "on_leave"
      ).length,
      review: records.filter(needsReview).length,
    }),
    [records]
  );

  const issues = useMemo(
    () => records.filter(needsReview),
    [records]
  );

  const totalPages = Math.max(
    1,
    Math.ceil(filtered.length / PAGE_SIZE)
  );

  const currentPage = Math.min(page, totalPages);

  const visible = filtered.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const selected =
    records.find((row) => row.id === selectedId) ??
    issues[0] ??
    null;

  const selectedEmployee = selected
    ? employeeMap.get(selected.employee_id)
    : undefined;

  const canEditSelected =
    canManage && selected !== null;

  useEffect(() => {
    if (!workspaceId || !selected) {
      setEvents([]);
      return;
    }

    let cancelled = false;

    async function fetchDetail() {
      if (!workspaceId || !selected) return;

      setDetailLoading(true);

      try {
        const detail = await attendanceService.get(
          workspaceId,
          selected.id
        );

        if (!cancelled) {
          setEvents(detail.events ?? []);
        }
      } catch {
        if (!cancelled) setEvents([]);
      } finally {
        if (!cancelled) setDetailLoading(false);
      }
    }

    void fetchDetail();

    return () => {
      cancelled = true;
    };
  }, [workspaceId, selected?.id]);

  function openEdit(record: AttendanceRecordPublic) {
    setSelectedId(record.id);
    setEditStatus(record.status);
    setEditNotes(record.notes ?? "");
    setSaveMessage("");
    setEditOpen(true);
  }

  async function saveReview() {
    if (!workspaceId || !selected || !canEditSelected) {
      return;
    }

    setSaving(true);
    setSaveMessage("");

    try {
      await attendanceService.update(
        workspaceId,
        selected.id,
        {
          status: editStatus,
          notes: editNotes.trim() || null,
        }
      );

      setEditOpen(false);
      setSaveMessage("Attendance record updated.");
      await load(true);
    } catch (cause) {
      setSaveMessage(
        cause instanceof Error
          ? cause.message
          : "Unable to update attendance record."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <WorkspaceRequired>
      <main className="ma-page">
        <header className="ma-page-header">
          <div>
            <h1>Monitoring Attendance</h1>
            <p>
              Review recorded attendance, employee
              check-ins, and incomplete daily records.
            </p>
          </div>

          <div className="ma-header-actions">
            <label className="ma-date-control">
              <CalendarDays size={17} />
              <input
                type="date"
                aria-label="Attendance date"
                value={day}
                onChange={(event) => {
                  setDay(event.target.value);
                  setPage(1);
                  setSelectedId(null);
                  setSaveMessage("");
                }}
              />
            </label>

            <button
              type="button"
              className="ma-btn ma-btn-white"
              disabled={refreshing || !canRead}
              onClick={() => void load(true)}
            >
              <RefreshCw
                size={16}
                className={refreshing ? "ma-spin" : ""}
              />
              Refresh
            </button>

            <button
              type="button"
              className="ma-btn ma-btn-dark"
              disabled={!canRead || filtered.length === 0}
              onClick={() =>
                exportCsv(filtered, employeeMap)
              }
            >
              <Download size={17} />
              Export
            </button>
          </div>
        </header>

        {!canRead ? (
          <div className="ma-error">
            <AlertTriangle size={18} />
            You do not have permission to read attendance
            records.
          </div>
        ) : (
          <>
            {error && (
              <div className="ma-error">
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

            {saveMessage && !editOpen && (
              <div className="ma-success">
                <CheckCircle2 size={17} />
                {saveMessage}
              </div>
            )}

            <section className="ma-summary">
              <Metric
                icon={<CheckCircle2 size={28} />}
                label="Present"
                value={totals.present}
                detail="Recorded present"
                tone="green"
              />

              <Metric
                icon={<Clock3 size={28} />}
                label="Late"
                value={totals.late}
                detail="Recorded late"
                tone="orange"
              />

              <Metric
                icon={<AlertCircle size={28} />}
                label="Absent"
                value={totals.absent}
                detail="Recorded absent"
                tone="red"
              />

              <Metric
                icon={<CalendarDays size={28} />}
                label="On leave"
                value={totals.leave}
                detail="Recorded leave"
                tone="purple"
              />
            </section>

            <div className="ma-layout">
              <section className="ma-left">
                <div className="ma-filters">
                  <label className="ma-search">
                    <Search size={17} />
                    <input
                      type="search"
                      placeholder="Search employee..."
                      value={search}
                      onChange={(event) => {
                        setSearch(event.target.value);
                        setPage(1);
                      }}
                    />
                  </label>

                  <select
                    aria-label="Attendance status"
                    value={status}
                    onChange={(event) => {
                      setStatus(
                        event.target.value as FilterStatus
                      );
                      setPage(1);
                    }}
                  >
                    <option value="all">All statuses</option>
                    {(
                      Object.keys(
                        STATUS_LABELS
                      ) as AttendanceStatus[]
                    ).map((key) => (
                      <option key={key} value={key}>
                        {STATUS_LABELS[key]}
                      </option>
                    ))}
                  </select>

                  <select
                    aria-label="Review filter"
                    value={reviewFilter}
                    onChange={(event) => {
                      setReviewFilter(
                        event.target.value as ReviewFilter
                      );
                      setPage(1);
                    }}
                  >
                    <option value="all">All records</option>
                    <option value="needs_review">
                      Needs review
                    </option>
                  </select>

                  <button
                    type="button"
                    className="ma-clear"
                    onClick={() => {
                      setSearch("");
                      setStatus("all");
                      setReviewFilter("all");
                      setPage(1);
                    }}
                  >
                    Clear
                  </button>
                </div>

                <div className="ma-card">
                  <div className="ma-card-header">
                    <h2>
                      <UsersRound size={20} />
                      Employee attendance
                    </h2>
                    <span>
                      {filtered.length} records
                    </span>
                  </div>

                  <div className="ma-table-scroll">
                    <table className="ma-table">
                      <thead>
                        <tr>
                          <th>Employee</th>
                          <th>Attendance</th>
                          <th>Check in</th>
                          <th>Check out</th>
                          <th>Worked</th>
                          <th>Source</th>
                          <th>Review</th>
                        </tr>
                      </thead>

                      <tbody>
                        {visible.map((record) => {
                          const employee = employeeMap.get(
                            record.employee_id
                          );
                          const name = employeeName(employee);

                          return (
                            <tr
                              key={record.id}
                              className={
                                selected?.id === record.id
                                  ? "ma-row-selected"
                                  : ""
                              }
                            >
                              <td>
                                <button
                                  type="button"
                                  className="ma-person"
                                  onClick={() =>
                                    setSelectedId(record.id)
                                  }
                                >
                                  <span className="ma-avatar">
                                    {initials(name)}
                                  </span>
                                  <span>
                                    <strong>{name}</strong>
                                    <small>
                                      {employee?.employee_code ||
                                        record.employee_id}
                                    </small>
                                  </span>
                                </button>
                              </td>

                              <td>
                                <StatusPill
                                  status={record.status}
                                />
                              </td>

                              <td>
                                {timeString(
                                  record.check_in_at
                                )}
                              </td>

                              <td>
                                {timeString(
                                  record.check_out_at
                                )}
                              </td>

                              <td>
                                {minutesString(
                                  record.worked_minutes
                                )}
                              </td>

                              <td className="ma-source">
                                {record.source.replaceAll(
                                  "_",
                                  " "
                                )}
                              </td>

                              <td>
                                <button
                                  type="button"
                                  className="ma-review-button"
                                  onClick={() =>
                                    setSelectedId(record.id)
                                  }
                                >
                                  {needsReview(record) ? (
                                    <>
                                      <AlertTriangle
                                        size={14}
                                      />
                                      Review
                                    </>
                                  ) : (
                                    <>
                                      <CheckCircle2
                                        size={14}
                                      />
                                      Details
                                    </>
                                  )}
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>

                    {loading && (
                      <div className="ma-empty">
                        <Loader2
                          size={28}
                          className="ma-spin"
                        />
                        Loading attendance records...
                      </div>
                    )}

                    {!loading &&
                      visible.length === 0 && (
                        <div className="ma-empty">
                          <ClipboardCheck size={31} />
                          <strong>
                            {records.length === 0
                              ? "No attendance records for this date"
                              : "No records match these filters"}
                          </strong>
                          <p>
                            {records.length === 0
                              ? "Missing records are not automatically classified as absent. Attendance must be recorded by an authorized source."
                              : "Choose different filters to view more attendance records."}
                          </p>
                        </div>
                      )}
                  </div>

                  <footer className="ma-pagination">
                    <span>
                      Showing{" "}
                      {filtered.length
                        ? (currentPage - 1) *
                            PAGE_SIZE +
                          1
                        : 0}
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
                        Page {currentPage} of {totalPages}
                      </span>

                      <button
                        type="button"
                        aria-label="Next page"
                        disabled={currentPage >= totalPages}
                        onClick={() =>
                          setPage((value) =>
                            Math.min(
                              totalPages,
                              value + 1
                            )
                          )
                        }
                      >
                        <ChevronRight size={16} />
                      </button>
                    </div>
                  </footer>
                </div>
              </section>

              <aside className="ma-right">
                <div className="ma-card">
                  <div className="ma-card-header">
                    <h2>
                      <ShieldCheck size={20} />
                      Discrepancy review
                    </h2>
                    <span className="ma-review-count">
                      {totals.review} flagged
                    </span>
                  </div>

                  <div className="ma-discrepancies">
                    {issues.length ? (
                      issues.slice(0, 5).map((record) => (
                        <button
                          type="button"
                          key={record.id}
                          className={`ma-discrepancy ${
                            selected?.id === record.id
                              ? "ma-discrepancy-selected"
                              : ""
                          }`}
                          onClick={() =>
                            setSelectedId(record.id)
                          }
                        >
                          <span className="ma-warning-icon">
                            <AlertTriangle size={19} />
                          </span>
                          <span>
                            <strong>
                              {employeeName(
                                employeeMap.get(
                                  record.employee_id
                                )
                              )}
                            </strong>
                            <small>
                              {reviewDescription(record)}
                            </small>
                          </span>
                          <ChevronRight size={17} />
                        </button>
                      ))
                    ) : (
                      <div className="ma-clear-state">
                        <CheckCircle2 size={26} />
                        <strong>
                          No incomplete recorded days
                        </strong>
                        <p>
                          This only checks attendance
                          records already returned by the
                          backend.
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="ma-card ma-detail-card">
                  <div className="ma-card-header">
                    <h2>
                      <UserRound size={20} />
                      Attendance details
                    </h2>

                    {selected && (
                      <button
                        type="button"
                        className="ma-icon-btn"
                        aria-label="Clear selected record"
                        onClick={() => setSelectedId(null)}
                      >
                        <X size={18} />
                      </button>
                    )}
                  </div>

                  {selected ? (
                    <>
                      <div className="ma-detail-person">
                        <span className="ma-avatar ma-avatar-lg">
                          {initials(
                            employeeName(selectedEmployee)
                          )}
                        </span>
                        <div>
                          <strong>
                            {employeeName(selectedEmployee)}
                          </strong>
                          <small>
                            {selected.attendance_date}
                          </small>
                        </div>
                        <StatusPill
                          status={selected.status}
                        />
                      </div>

                      <dl className="ma-facts">
                        <div>
                          <dt>Check in</dt>
                          <dd>
                            {timeString(
                              selected.check_in_at
                            )}
                          </dd>
                        </div>
                        <div>
                          <dt>Check out</dt>
                          <dd>
                            {timeString(
                              selected.check_out_at
                            )}
                          </dd>
                        </div>
                        <div>
                          <dt>Worked duration</dt>
                          <dd>
                            {minutesString(
                              selected.worked_minutes
                            )}
                          </dd>
                        </div>
                        <div>
                          <dt>Break duration</dt>
                          <dd>
                            {minutesString(
                              selected.break_minutes
                            )}
                          </dd>
                        </div>
                        <div>
                          <dt>Recorded source</dt>
                          <dd>
                            {selected.source.replaceAll(
                              "_",
                              " "
                            )}
                          </dd>
                        </div>
                        <div>
                          <dt>Last updated</dt>
                          <dd>
                            {dateTimeString(
                              selected.updated_at
                            )}
                          </dd>
                        </div>
                      </dl>

                      {needsReview(selected) && (
                        <div className="ma-detail-warning">
                          <AlertTriangle size={17} />
                          {reviewDescription(selected)}
                        </div>
                      )}

                      <div className="ma-events">
                        <h3>
                          <Clock3 size={17} />
                          Recorded events
                        </h3>

                        {detailLoading ? (
                          <p className="ma-muted">
                            Loading events...
                          </p>
                        ) : events.length ? (
                          events.map((event) => (
                            <div
                              className="ma-event"
                              key={event.id}
                            >
                              <span className="ma-event-dot" />
                              <span>
                                <strong>
                                  {event.event_type
                                    .replaceAll("_", " ")}
                                </strong>
                                <small>
                                  {dateTimeString(
                                    event.occurred_at
                                  )}
                                </small>
                              </span>
                              <small>{event.source}</small>
                            </div>
                          ))
                        ) : (
                          <p className="ma-muted">
                            No events available for this
                            attendance record.
                          </p>
                        )}
                      </div>

                      {selected.notes && (
                        <div className="ma-notes">
                          <strong>Notes</strong>
                          <p>{selected.notes}</p>
                        </div>
                      )}

                      <button
                        type="button"
                        className="ma-btn ma-btn-dark ma-review-action"
                        disabled={!canEditSelected}
                        onClick={() =>
                          openEdit(selected)
                        }
                      >
                        <ClipboardCheck size={17} />
                        Review / correct record
                      </button>
                    </>
                  ) : (
                    <div className="ma-empty ma-small-empty">
                      <ClipboardCheck size={29} />
                      <strong>No record selected</strong>
                      <p>
                        Choose a record from the attendance
                        table or discrepancy list.
                      </p>
                    </div>
                  )}
                </div>

                <div className="ma-data-note">
                  <Info size={16} />
                  Attendance records and monitoring signals
                  are separate data sources. This page
                  reports attendance recorded by the
                  attendance service.
                </div>
              </aside>
            </div>
          </>
        )}

        {editOpen && selected && (
          <div
            className="ma-overlay"
            onMouseDown={(event) => {
              if (event.currentTarget === event.target) {
                setEditOpen(false);
              }
            }}
          >
            <section
              className="ma-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="ma-modal-title"
            >
              <header>
                <div>
                  <h2 id="ma-modal-title">
                    Review attendance record
                  </h2>
                  <p>
                    {employeeName(selectedEmployee)} —{" "}
                    {selected.attendance_date}
                  </p>
                </div>
                <button
                  type="button"
                  aria-label="Close dialog"
                  onClick={() => setEditOpen(false)}
                >
                  <X size={20} />
                </button>
              </header>

              <div className="ma-modal-body">
                <label>
                  Attendance status
                  <select
                    value={editStatus}
                    onChange={(event) =>
                      setEditStatus(
                        event.target.value as AttendanceStatus
                      )
                    }
                  >
                    {(
                      Object.keys(
                        STATUS_LABELS
                      ) as AttendanceStatus[]
                    ).map((key) => (
                      <option key={key} value={key}>
                        {STATUS_LABELS[key]}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Review notes
                  <textarea
                    rows={4}
                    maxLength={2000}
                    placeholder="Record the reason for any correction."
                    value={editNotes}
                    onChange={(event) =>
                      setEditNotes(event.target.value)
                    }
                  />
                </label>

                <div className="ma-modal-info">
                  <ShieldCheck size={18} />
                  Corrections are sent to the authorized
                  attendance API. The backend requires
                  owner or admin access to update records.
                  Missing timestamps are not fabricated.
                </div>

                {saveMessage && (
                  <div className="ma-error">
                    <AlertTriangle size={17} />
                    {saveMessage}
                  </div>
                )}

                <div className="ma-modal-actions">
                  <button
                    type="button"
                    className="ma-btn ma-btn-white"
                    onClick={() => setEditOpen(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="ma-btn ma-btn-dark"
                    disabled={saving}
                    onClick={() => void saveReview()}
                  >
                    {saving ? (
                      <Loader2
                        size={16}
                        className="ma-spin"
                      />
                    ) : (
                      <CheckCircle2 size={16} />
                    )}
                    Save changes
                  </button>
                </div>
              </div>
            </section>
          </div>
        )}

        <style jsx global>{`
          .ma-page {
            --ma-ink: #101c3b;
            --ma-muted: #697994;
            --ma-line: #e5e8ec;
            background: #fbfaf8;
            min-height: 100%;
            padding: 21px 21px 35px;
            color: var(--ma-ink);
            font-size: 12px;
          }

          .ma-page * {
            box-sizing: border-box;
          }

          .ma-page button,
          .ma-page input,
          .ma-page select,
          .ma-page textarea {
            font: inherit;
          }

          .ma-page button {
            cursor: pointer;
          }

          .ma-page button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
          }

          .ma-page-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            margin-bottom: 19px;
          }

          .ma-page-header h1 {
            margin: 0;
            font-size: 29px;
            font-weight: 750;
            letter-spacing: -0.8px;
            line-height: 1.15;
          }

          .ma-page-header p {
            font-size: 14px;
            margin: 5px 0 0;
            color: var(--ma-muted);
          }

          .ma-header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
          }

          .ma-date-control {
            height: 39px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 0 11px;
            border: 1px solid #e0e4ea;
            background: white;
            border-radius: 7px;
          }

          .ma-date-control input {
            border: 0;
            background: transparent;
            outline: none;
            color: var(--ma-ink);
          }

          .ma-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 9px;
            height: 39px;
            padding: 0 14px;
            font-weight: 650 !important;
            border-radius: 7px;
            white-space: nowrap;
          }

          .ma-btn-white {
            color: var(--ma-ink);
            border: 1px solid #dfe3e9;
            background: white;
          }

          .ma-btn-dark {
            color: white;
            background: #182430;
            border: 1px solid #182430;
          }

          .ma-summary {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 13px;
            margin-bottom: 16px;
          }

          .ma-metric {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 18px;
            min-height: 112px;
            background: #fffefa;
            border: 1px solid var(--ma-line);
            border-radius: 11px;
          }

          .ma-metric-icon {
            height: 58px;
            width: 58px;
            border-radius: 50%;
            flex-shrink: 0;
            display: grid;
            place-items: center;
          }

          .ma-metric-icon.ma-green {
            color: #1cab68;
            background: #e0f7e8;
          }

          .ma-metric-icon.ma-orange {
            color: #e8a000;
            background: #fff0ce;
          }

          .ma-metric-icon.ma-red {
            color: #ed494e;
            background: #ffe8e7;
          }

          .ma-metric-icon.ma-purple {
            color: #8457da;
            background: #f0e9ff;
          }

          .ma-metric-copy {
            display: flex;
            flex-direction: column;
            gap: 4px;
            min-width: 0;
          }

          .ma-metric-copy span {
            font-size: 13px;
            font-weight: 650;
          }

          .ma-metric-copy strong {
            font-size: 27px;
            letter-spacing: -0.7px;
            line-height: 1.1;
          }

          .ma-metric-copy small {
            color: var(--ma-muted);
            font-size: 11px;
          }

          .ma-layout {
            display: grid;
            grid-template-columns:
              minmax(0, 1.65fr)
              minmax(325px, 0.85fr);
            gap: 15px;
            align-items: start;
          }

          .ma-left,
          .ma-right {
            min-width: 0;
          }

          .ma-right {
            display: flex;
            flex-direction: column;
            gap: 14px;
          }

          .ma-filters {
            display: flex;
            align-items: center;
            gap: 9px;
            flex-wrap: wrap;
            margin-bottom: 14px;
          }

          .ma-search {
            height: 39px;
            min-width: 175px;
            flex: 1 1 190px;
            background: white;
            border: 1px solid #dfe4ea;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 0 12px;
            color: #74839b;
          }

          .ma-search input {
            width: 100%;
            min-width: 0;
            background: transparent;
            border: 0;
            outline: none;
            color: var(--ma-ink);
          }

          .ma-filters select {
            height: 39px;
            min-width: 120px;
            border: 1px solid #dfe4ea;
            background: white;
            border-radius: 8px;
            padding: 0 10px;
            color: var(--ma-ink);
          }

          .ma-clear {
            color: #526588;
            border: 0;
            background: transparent;
            text-decoration: underline;
            padding: 7px;
          }

          .ma-card {
            border: 1px solid var(--ma-line);
            border-radius: 11px;
            background: #fffefa;
            overflow: hidden;
          }

          .ma-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-height: 57px;
            padding: 13px 15px;
            gap: 12px;
          }

          .ma-card-header h2 {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0;
            font-size: 17px;
            font-weight: 750;
            letter-spacing: -0.3px;
          }

          .ma-card-header > span {
            color: var(--ma-muted);
          }

          .ma-table-scroll {
            overflow-x: auto;
            min-height: 330px;
          }

          .ma-table {
            width: 100%;
            min-width: 690px;
            border-collapse: collapse;
            text-align: left;
          }

          .ma-table th {
            background: #f6f7f8;
            font-size: 10px;
            font-weight: 700;
            padding: 12px 10px;
            white-space: nowrap;
          }

          .ma-table td {
            padding: 11px 10px;
            border-top: 1px solid #e9ecf0;
            font-size: 11px;
            white-space: nowrap;
          }

          .ma-table tr.ma-row-selected {
            background: #fff6e4;
          }

          .ma-person {
            display: flex;
            align-items: center;
            gap: 9px;
            border: 0;
            padding: 0;
            background: transparent;
            color: var(--ma-ink);
            text-align: left;
          }

          .ma-person > span:last-child {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }

          .ma-person small {
            color: var(--ma-muted);
            max-width: 180px;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .ma-avatar {
            width: 31px;
            height: 31px;
            border-radius: 50%;
            flex-shrink: 0;
            display: grid;
            place-items: center;
            background: #ffe8b4;
            color: #966200;
            font-weight: 750;
          }

          .ma-status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 9px;
            border-radius: 20px;
            background: #eef0f4;
            color: #657389;
            white-space: nowrap;
            font-size: 11px;
          }

          .ma-status i {
            display: inline-block;
            height: 8px;
            width: 8px;
            border-radius: 50%;
            background: currentColor;
          }

          .ma-status-present {
            color: #168653;
            background: #def7e7;
          }

          .ma-status-late {
            color: #a77700;
            background: #fff1cd;
          }

          .ma-status-absent {
            color: #bc353a;
            background: #ffe6e7;
          }

          .ma-status-on_leave {
            color: #7445bc;
            background: #f0e8ff;
          }

          .ma-status-half_day {
            color: #b47a00;
            background: #fff2d1;
          }

          .ma-status-holiday {
            color: #396bb5;
            background: #e5efff;
          }

          .ma-source {
            color: var(--ma-muted);
            text-transform: capitalize;
          }

          .ma-review-button {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            border: 1px solid #e2e5ea;
            background: white;
            border-radius: 6px;
            padding: 7px 9px;
            color: #526483;
          }

          .ma-pagination {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            padding: 14px 15px;
            color: var(--ma-muted);
          }

          .ma-pagination > div {
            display: flex;
            align-items: center;
            gap: 9px;
          }

          .ma-pagination button {
            border: 1px solid #e4e7eb;
            background: white;
            border-radius: 7px;
            width: 32px;
            height: 32px;
            display: grid;
            place-items: center;
          }

          .ma-review-count {
            color: #bd7a00 !important;
            background: #fff2d3;
            padding: 5px 9px;
            border-radius: 20px;
          }

          .ma-discrepancies {
            padding: 0 12px 12px;
          }

          .ma-discrepancy {
            display: flex;
            align-items: center;
            gap: 11px;
            width: 100%;
            text-align: left;
            background: #fff;
            border: 1px solid #e7e9ed;
            padding: 12px;
            margin-bottom: 9px;
            border-radius: 8px;
            color: var(--ma-ink);
          }

          .ma-discrepancy-selected {
            border-color: #ffcf79;
            background: #fff7e8;
          }

          .ma-warning-icon {
            background: #fff1d6;
            color: #e4a000;
            width: 35px;
            height: 35px;
            flex-shrink: 0;
            border-radius: 8px;
            display: grid;
            place-items: center;
          }

          .ma-discrepancy > span:nth-child(2) {
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 5px;
          }

          .ma-discrepancy small {
            color: var(--ma-muted);
            line-height: 1.4;
          }

          .ma-clear-state {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 9px;
            text-align: center;
            min-height: 155px;
            color: #32a56a;
            padding: 18px;
          }

          .ma-clear-state strong {
            color: var(--ma-ink);
          }

          .ma-clear-state p {
            color: var(--ma-muted);
            line-height: 1.6;
            margin: 0;
          }

          .ma-detail-person {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 3px 15px 17px;
            border-bottom: 1px solid var(--ma-line);
          }

          .ma-avatar-lg {
            width: 44px;
            height: 44px;
            font-size: 14px;
          }

          .ma-detail-person > div {
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 5px;
          }

          .ma-detail-person small {
            color: var(--ma-muted);
          }

          .ma-facts {
            margin: 0 15px;
            padding: 12px 0;
            border-bottom: 1px solid var(--ma-line);
          }

          .ma-facts > div {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 9px;
            padding: 8px 0;
          }

          .ma-facts dt {
            color: var(--ma-muted);
          }

          .ma-facts dd {
            margin: 0;
            font-weight: 650;
            text-transform: capitalize;
            overflow-wrap: anywhere;
          }

          .ma-detail-warning {
            display: flex;
            align-items: flex-start;
            gap: 9px;
            background: #fff5df;
            border: 1px solid #f0dbad;
            border-radius: 7px;
            color: #9a6b00;
            line-height: 1.55;
            margin: 13px 15px 0;
            padding: 11px;
          }

          .ma-events {
            padding: 14px 15px;
          }

          .ma-events h3 {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            margin: 0 0 12px;
          }

          .ma-event {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 9px 0;
            border-bottom: 1px solid #edf0f2;
            text-transform: capitalize;
          }

          .ma-event-dot {
            width: 9px;
            height: 9px;
            background: #2abc78;
            border-radius: 50%;
          }

          .ma-event > span:nth-child(2) {
            display: flex;
            flex: 1;
            flex-direction: column;
            gap: 5px;
          }

          .ma-event small {
            color: var(--ma-muted);
          }

          .ma-notes {
            margin: 0 15px;
            border-top: 1px solid #edf0f2;
            padding: 14px 0;
          }

          .ma-notes p {
            color: var(--ma-muted);
            line-height: 1.6;
          }

          .ma-review-action {
            margin: 0 15px 17px;
            width: calc(100% - 30px);
          }

          .ma-data-note {
            display: flex;
            align-items: flex-start;
            gap: 9px;
            color: var(--ma-muted);
            line-height: 1.6;
            padding: 3px;
          }

          .ma-data-note svg {
            flex-shrink: 0;
          }

          .ma-muted {
            color: var(--ma-muted);
            line-height: 1.6;
          }

          .ma-empty {
            min-height: 260px;
            padding: 25px;
            display: flex;
            align-items: center;
            flex-direction: column;
            justify-content: center;
            gap: 11px;
            text-align: center;
            color: #8594a9;
          }

          .ma-empty strong {
            color: var(--ma-ink);
          }

          .ma-empty p {
            color: var(--ma-muted);
            max-width: 285px;
            line-height: 1.6;
            margin: 0;
          }

          .ma-small-empty {
            min-height: 220px;
          }

          .ma-icon-btn {
            border: 0;
            background: transparent;
            color: #536682;
          }

          .ma-error,
          .ma-success {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 14px;
            border-radius: 8px;
            margin-bottom: 14px;
          }

          .ma-error {
            color: #b33030;
            border: 1px solid #f0bcbc;
            background: #fff0f0;
          }

          .ma-error span {
            flex: 1;
          }

          .ma-error button {
            border: 1px solid #eab4b4;
            border-radius: 6px;
            background: white;
            padding: 6px 10px;
          }

          .ma-success {
            color: #177c4b;
            border: 1px solid #c5e7cf;
            background: #edf9f1;
          }

          .ma-overlay {
            position: fixed;
            inset: 0;
            z-index: 250;
            display: grid;
            place-items: center;
            background: #0c172890;
            padding: 20px;
          }

          .ma-modal {
            width: min(510px, 100%);
            max-height: 90vh;
            overflow-y: auto;
            border-radius: 12px;
            border: 1px solid #e5e8ef;
            background: #fffefa;
            box-shadow: 0 18px 60px #0003;
          }

          .ma-modal header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            padding: 19px 20px;
            border-bottom: 1px solid #e7e9ed;
          }

          .ma-modal header h2 {
            font-size: 21px;
            margin: 0;
          }

          .ma-modal header p {
            margin: 6px 0 0;
            color: var(--ma-muted);
          }

          .ma-modal header button {
            background: transparent;
            border: 0;
          }

          .ma-modal-body {
            padding: 20px;
          }

          .ma-modal-body > label {
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-weight: 650;
            margin-bottom: 17px;
          }

          .ma-modal-body select,
          .ma-modal-body textarea {
            border: 1px solid #dfe4ea;
            border-radius: 7px;
            padding: 11px;
            color: var(--ma-ink);
            background: white;
            font-weight: 400;
          }

          .ma-modal-info {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 12px;
            background: #f0f7ff;
            border: 1px solid #dce9fa;
            border-radius: 7px;
            color: #395574;
            line-height: 1.6;
            margin-bottom: 15px;
          }

          .ma-modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 17px;
          }

          .ma-spin {
            animation: ma-spin 1s linear infinite;
          }

          @keyframes ma-spin {
            to {
              transform: rotate(360deg);
            }
          }

          @media (max-width: 1260px) {
            .ma-layout {
              grid-template-columns: minmax(0, 1fr);
            }

            .ma-right {
              display: grid;
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .ma-data-note {
              grid-column: 1 / -1;
            }
          }

          @media (max-width: 900px) {
            .ma-summary {
              grid-template-columns: repeat(2, 1fr);
            }

            .ma-right {
              grid-template-columns: 1fr;
            }

            .ma-data-note {
              grid-column: auto;
            }
          }

          @media (max-width: 720px) {
            .ma-page-header {
              align-items: flex-start;
              flex-direction: column;
            }
          }

          @media (max-width: 520px) {
            .ma-page {
              padding: 15px 12px;
            }

            .ma-page-header h1 {
              font-size: 24px;
            }

            .ma-summary {
              grid-template-columns: 1fr;
            }

            .ma-pagination {
              flex-wrap: wrap;
            }

            .ma-detail-person {
              flex-wrap: wrap;
            }
          }
        `}</style>
      </main>
    </WorkspaceRequired>
  );
}
