
"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  AlertTriangle,
  ArrowRight,
  CalendarDays,
  Camera,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  ExternalLink,
  FileImage,
  HardDrive,
  Info,
  Loader2,
  Monitor,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";
import {
  monitoringService,
  type MonitoringSnapshot,
} from "@/services/monitoring.service";

type Screenshot = {
  id: string;
  device_id: string;
  employee_id: string;
  requested_by_user_id: string;
  status: string;
  reason: string | null;
  requested_at: string;
  expires_at: string;
  completed_at: string | null;
  width: number | null;
  height: number | null;
  consent_required: boolean;
  visible_indicator_required: boolean;
  consent_confirmed_at: string | null;
};

type ScreenshotList = {
  items: Screenshot[];
  total: number;
};

type ScreenshotMedia = {
  request_id: string;
  download_url: string;
  expires_in_seconds: number;
};

type Employee = {
  id: string;
  name: string;
  department: string;
};

type AgentDevice = {
  id: string;
  name: string;
  employee: string;
  employee_id: string;
  status: string;
  agent_ready: boolean;
};

const asText = (value: unknown, fallback = "") =>
  typeof value === "string" ? value : fallback;

const isCompleted = (status: string) =>
  status.toLowerCase() === "completed";

const isPending = (status: string) =>
  ["requested", "pending", "accepted", "approved"].includes(
    status.toLowerCase()
  );

const dateValue = (date: Date) => {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
};

function localDayRange(day: string) {
  const start = new Date(`${day}T00:00:00`);
  const end = new Date(`${day}T23:59:59.999`);
  return {
    start_at: start.toISOString(),
    end_at: end.toISOString(),
  };
}

function formatDate(value: string | null) {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime())
    ? value
    : parsed.toLocaleString(undefined, {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
}

function formatTime(value: string | null) {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime())
    ? value
    : parsed.toLocaleTimeString(undefined, {
        hour: "2-digit",
        minute: "2-digit",
      });
}

function statusLabel(status: string) {
  const text = status.toLowerCase().replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function screenshotPath(workspaceId: string) {
  return `/workspaces/${workspaceId}/live-monitoring/screenshots`;
}

export default function MonitoringScreenshotsPage() {
  const { workspaceId, permissions, navigationView } =
    useWorkspace();

  const canRead = hasAnyPermission(
    permissions,
    [
      "monitoring.all.read",
      "monitoring.team.read",
      "monitoring.self.read",
      "monitoring.live_view",
      "monitoring.live_screen",
    ],
    navigationView
  );

  const canRequest = hasAnyPermission(
    permissions,
    ["monitoring.live_view"],
    navigationView
  );

  const [day, setDay] = useState(() =>
    dateValue(new Date())
  );
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("all");
  const [tab, setTab] = useState<"history" | "pending">(
    "history"
  );
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(
    null
  );

  const [data, setData] = useState<ScreenshotList>({
    items: [],
    total: 0,
  });
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [devices, setDevices] = useState<AgentDevice[]>([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [requestOpen, setRequestOpen] = useState(false);
  const [requestDeviceId, setRequestDeviceId] = useState("");
  const [reason, setReason] = useState("");
  const [requesting, setRequesting] = useState(false);
  const [requestMessage, setRequestMessage] = useState("");

  const [media, setMedia] = useState<
    Record<string, string>
  >({});
  const [openingMedia, setOpeningMedia] = useState(false);

  const employeeMap = useMemo(
    () => new Map(employees.map((employee) => [
      employee.id,
      employee,
    ])),
    [employees]
  );

  const deviceMap = useMemo(
    () => new Map(devices.map((device) => [
      device.id,
      device,
    ])),
    [devices]
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
        const range = localDayRange(day);

        const [history, employeeSnapshot, deviceSnapshot] =
          await Promise.all([
            api.get<ScreenshotList>(
              screenshotPath(workspaceId),
              {
                query: {
                  start_at: range.start_at,
                  end_at: range.end_at,
                  limit: 500,
                  offset: 0,
                },
              }
            ),
            monitoringService.employees(workspaceId),
            monitoringService.devices(workspaceId),
          ]);

        const allEmployees = (
          (employeeSnapshot as MonitoringSnapshot).items || []
        ).map((value) => ({
          id: asText(value.employee_id || value.id),
          name: asText(
            value.employee || value.name,
            "Unknown employee"
          ),
          department: asText(
            value.department,
            "Unassigned"
          ),
        }));

        const allDevices = (
          (deviceSnapshot as MonitoringSnapshot).items || []
        ).map((value) => ({
          id: asText(value.device_id || value.id),
          name: asText(
            value.name || value.device,
            "Unnamed device"
          ),
          employee: asText(value.employee, "Unassigned"),
          employee_id: asText(value.employee_id),
          status: asText(value.status, "offline"),
          agent_ready: value.agent_ready === true,
        }));

        setData(history);
        setEmployees(allEmployees);
        setDevices(allDevices);
        setError("");
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load screenshot history."
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

  const departments = useMemo(
    () =>
      [...new Set(
        employees.map((employee) => employee.department)
      )].sort(),
    [employees]
  );

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();

    return data.items.filter((screenshot) => {
      const employee = employeeMap.get(
        screenshot.employee_id
      );
      const device = deviceMap.get(screenshot.device_id);

      const label = [
        employee?.name,
        employee?.department,
        device?.name,
        screenshot.status,
        screenshot.reason,
      ]
        .join(" ")
        .toLowerCase();

      return (
        (!needle || label.includes(needle)) &&
        (department === "all" ||
          employee?.department === department) &&
        (tab === "pending"
          ? isPending(screenshot.status)
          : !isPending(screenshot.status))
      );
    });
  }, [
    data.items,
    employeeMap,
    deviceMap,
    search,
    department,
    tab,
  ]);

  const sorted = useMemo(
    () =>
      [...filtered].sort(
        (a, b) =>
          new Date(b.requested_at).getTime() -
          new Date(a.requested_at).getTime()
      ),
    [filtered]
  );

  const pageSize = 6;
  const totalPages = Math.max(
    1,
    Math.ceil(sorted.length / pageSize)
  );
  const currentPage = Math.min(page, totalPages);

  const visible = sorted.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  const selected =
    data.items.find((item) => item.id === selectedId) ??
    visible[0] ??
    null;

  const selectedEmployee = selected
    ? employeeMap.get(selected.employee_id)
    : null;

  const selectedDevice = selected
    ? deviceMap.get(selected.device_id)
    : null;

  const completedCount = data.items.filter((item) =>
    isCompleted(item.status)
  ).length;

  const pendingCount = data.items.filter((item) =>
    isPending(item.status)
  ).length;

  const availableDevices = devices.filter(
    (device) => device.agent_ready
  );

  async function requestScreenshot() {
    if (!workspaceId || !requestDeviceId || !canRequest) {
      return;
    }

    setRequesting(true);
    setRequestMessage("");

    try {
      const result = await api.post<Screenshot>(
        screenshotPath(workspaceId),
        {
          device_id: requestDeviceId,
          reason: reason.trim() || null,
        }
      );

      setRequestMessage(
        `Screenshot request submitted: ${result.id}`
      );
      setRequestOpen(false);
      setReason("");
      setRequestDeviceId("");
      setTab("pending");
      setPage(1);
      await load(true);
    } catch (cause) {
      setRequestMessage(
        cause instanceof Error
          ? cause.message
          : "Screenshot request failed."
      );
    } finally {
      setRequesting(false);
    }
  }

  async function viewImage(item: Screenshot) {
    if (!workspaceId || !isCompleted(item.status)) {
      return;
    }

    setOpeningMedia(true);
    setError("");

    // Open a blank tab directly on the user click.
    // This avoids popup blockers after awaiting the API.
    const opened = window.open(
      "",
      "_blank",
      "noopener,noreferrer"
    );

    try {
      const response = await api.post<ScreenshotMedia>(
        `${screenshotPath(workspaceId)}/${item.id}/media`
      );

      setMedia((previous) => ({
        ...previous,
        [item.id]: response.download_url,
      }));

      if (opened) {
        opened.location.replace(response.download_url);
      } else {
        setError(
          "Your browser blocked the image tab. Allow popups and try again."
        );
      }
    } catch (cause) {
      opened?.close();
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to retrieve screenshot media."
      );
    } finally {
      setOpeningMedia(false);
    }
  }

  return (
    <WorkspaceRequired>
      <main className="ss-page">
        <header className="ss-header">
          <div>
            <h1>Screenshots</h1>
            <p>
              View and manage employee desktop screenshots
              captured from authorized devices.
            </p>
          </div>

          <div className="ss-storage">
            <HardDrive size={19} />
            <span>
              <strong>Storage &amp; retention</strong>
              <small>Stored per workspace policy</small>
            </span>
            <Info size={15} />
          </div>
        </header>

        {!canRead ? (
          <div className="ss-error">
            <AlertTriangle size={18} />
            You do not have permission to view screenshot
            history.
          </div>
        ) : (
          <>
            <div className="ss-tabs">
              <button
                type="button"
                className={
                  tab === "history" ? "ss-active-tab" : ""
                }
                onClick={() => {
                  setTab("history");
                  setPage(1);
                }}
              >
                <Camera size={19} />
                Capture history
                <span>{completedCount}</span>
              </button>

              <button
                type="button"
                className={
                  tab === "pending" ? "ss-active-tab" : ""
                }
                onClick={() => {
                  setTab("pending");
                  setPage(1);
                }}
              >
                <Clock3 size={19} />
                Pending requests
                <span>{pendingCount}</span>
              </button>

              <button
                type="button"
                className="ss-request-btn"
                onClick={() => {
                  setRequestMessage("");
                  setRequestOpen(true);
                }}
                disabled={!canRequest}
              >
                <Plus size={18} />
                Request screenshot
              </button>
            </div>

            <div className="ss-filters">
              <label className="ss-date">
                <CalendarDays size={18} />
                <input
                  type="date"
                  aria-label="Screenshot date"
                  value={day}
                  onChange={(event) => {
                    setDay(event.target.value);
                    setPage(1);
                  }}
                />
              </label>

              <select
                aria-label="Department"
                value={department}
                onChange={(event) => {
                  setDepartment(event.target.value);
                  setPage(1);
                }}
              >
                <option value="all">All departments</option>
                {departments.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>

              <label className="ss-search">
                <Search size={17} />
                <input
                  placeholder="Search employees..."
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                  }}
                />
              </label>

              <button
                type="button"
                className="ss-refresh"
                disabled={refreshing}
                onClick={() => void load(true)}
              >
                <RefreshCw
                  size={16}
                  className={refreshing ? "ss-spin" : ""}
                />
                Refresh
              </button>
            </div>

            {error && (
              <div className="ss-error">
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

            {requestMessage && (
              <div className="ss-message" role="status">
                <Info size={17} />
                {requestMessage}
              </div>
            )}

            <div className="ss-grid-layout">
              <section className="ss-left">
                <div className="ss-timeline">
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
                    <ChevronLeft size={19} />
                  </button>

                  <div className="ss-line">
                    {visible.map((item) => (
                      <button
                        type="button"
                        key={item.id}
                        className={
                          selected?.id === item.id
                            ? "ss-point ss-point-selected"
                            : "ss-point"
                        }
                        onClick={() => setSelectedId(item.id)}
                      >
                        <span>
                          {formatTime(item.requested_at)}
                        </span>
                        <i />
                      </button>
                    ))}
                    {visible.length === 0 && (
                      <span className="ss-empty-time">
                        No captures on this date
                      </span>
                    )}
                  </div>

                  <button
                    type="button"
                    aria-label="Next page"
                    disabled={currentPage >= totalPages}
                    onClick={() =>
                      setPage((value) =>
                        Math.min(totalPages, value + 1)
                      )
                    }
                  >
                    <ChevronRight size={19} />
                  </button>
                </div>

                {loading ? (
                  <div className="ss-empty">
                    <Loader2 size={30} className="ss-spin" />
                    <strong>Loading screenshots...</strong>
                  </div>
                ) : visible.length === 0 ? (
                  <div className="ss-empty">
                    <Camera size={32} />
                    <strong>
                      {tab === "pending"
                        ? "No pending screenshot requests"
                        : "No screenshot captures found"}
                    </strong>
                    <p>
                      Only authorized screenshot requests
                      and completed captures are displayed.
                      No example screenshot images are used.
                    </p>
                  </div>
                ) : (
                  <div className="ss-gallery">
                    {visible.map((item) => {
                      const employee = employeeMap.get(
                        item.employee_id
                      );
                      const device = deviceMap.get(
                        item.device_id
                      );

                      const imageUrl = media[item.id];

                      return (
                        <button
                          type="button"
                          key={item.id}
                          className={`ss-shot ${
                            selected?.id === item.id
                              ? "ss-shot-selected"
                              : ""
                          }`}
                          onClick={() => setSelectedId(item.id)}
                        >
                          <div className="ss-preview">
                            {imageUrl &&
                            isCompleted(item.status) ? (
                              /* eslint-disable-next-line @next/next/no-img-element */
                              <img
                                src={imageUrl}
                                alt={`Screenshot captured for ${
                                  employee?.name ||
                                  "employee"
                                }`}
                              />
                            ) : (
                              <div className="ss-placeholder">
                                <Camera size={26} />
                                <span>
                                  {isCompleted(item.status)
                                    ? "Open to view capture"
                                    : statusLabel(item.status)}
                                </span>
                              </div>
                            )}
                          </div>

                          <div className="ss-shot-meta">
                            <span className="ss-shot-employee">
                              <i
                                className={
                                  isCompleted(item.status)
                                    ? "ss-green"
                                    : "ss-yellow"
                                }
                              />
                              {employee?.name ||
                                "Employee unavailable"}
                            </span>

                            <span>
                              {formatTime(item.requested_at)}
                            </span>
                            <small>
                              {device?.name || "Unknown device"}
                            </small>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}

                <section className="ss-request-history">
                  <div className="ss-section-heading">
                    <h2>
                      <Clock3 size={20} />
                      Recent screenshot requests
                    </h2>

                    <span>
                      {sorted.length} matching records
                    </span>
                  </div>

                  <div className="ss-table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Request time</th>
                          <th>Employee</th>
                          <th>Department</th>
                          <th>Device</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>

                      <tbody>
                        {sorted.map((item) => {
                          const employee = employeeMap.get(
                            item.employee_id
                          );
                          const device = deviceMap.get(
                            item.device_id
                          );

                          return (
                            <tr key={item.id}>
                              <td>
                                {formatDate(item.requested_at)}
                              </td>
                              <td>
                                {employee?.name || "—"}
                              </td>
                              <td>
                                {employee?.department || "—"}
                              </td>
                              <td>
                                {device?.name || "—"}
                              </td>
                              <td>
                                <span
                                  className={`ss-status ss-${item.status.toLowerCase()}`}
                                >
                                  {statusLabel(item.status)}
                                </span>
                              </td>
                              <td>
                                <button
                                  type="button"
                                  className="ss-view-details"
                                  onClick={() => {
                                    setSelectedId(item.id);
                                    window.scrollTo({
                                      top: 0,
                                      behavior: "smooth",
                                    });
                                  }}
                                >
                                  View details
                                  <ChevronRight size={14} />
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </section>
              </section>

              <aside className="ss-right">
                <div className="ss-section-heading">
                  <h2>Screenshot details</h2>
                  {selected && (
                    <button
                      type="button"
                      aria-label="Clear selection"
                      onClick={() => setSelectedId(null)}
                    >
                      <X size={19} />
                    </button>
                  )}
                </div>

                {selected ? (
                  <>
                    <div className="ss-detail-preview">
                      {media[selected.id] &&
                      isCompleted(selected.status) ? (
                        /* eslint-disable-next-line @next/next/no-img-element */
                        <img
                          src={media[selected.id]}
                          alt="Selected screenshot"
                        />
                      ) : (
                        <div className="ss-placeholder">
                          <FileImage size={37} />
                          <span>
                            {isCompleted(selected.status)
                              ? "Select View image to load capture"
                              : "Capture not available"}
                          </span>
                        </div>
                      )}
                    </div>

                    <dl className="ss-detail-facts">
                      <div>
                        <dt>
                          <UserRound size={17} />
                          Employee
                        </dt>
                        <dd>
                          {selectedEmployee?.name ||
                            "Employee unavailable"}
                        </dd>
                      </div>
                      <div>
                        <dt>
                          <Clock3 size={17} />
                          Captured at
                        </dt>
                        <dd>
                          {formatDate(
                            selected.completed_at ||
                              selected.requested_at
                          )}
                        </dd>
                      </div>
                      <div>
                        <dt>
                          <Monitor size={17} />
                          Device
                        </dt>
                        <dd>
                          {selectedDevice?.name ||
                            "Unknown device"}
                        </dd>
                      </div>
                      <div>
                        <dt>
                          <UsersIcon />
                          Department
                        </dt>
                        <dd>
                          {selectedEmployee?.department ||
                            "Unassigned"}
                        </dd>
                      </div>
                      <div>
                        <dt>
                          <CheckCircle2 size={17} />
                          Status
                        </dt>
                        <dd>
                          <span
                            className={`ss-status ss-${selected.status.toLowerCase()}`}
                          >
                            {statusLabel(selected.status)}
                          </span>
                        </dd>
                      </div>
                    </dl>

                    <button
                      type="button"
                      className="ss-open-image"
                      disabled={
                        !isCompleted(selected.status) ||
                        openingMedia
                      }
                      onClick={() => void viewImage(selected)}
                    >
                      {openingMedia ? (
                        <Loader2
                          size={17}
                          className="ss-spin"
                        />
                      ) : (
                        <ExternalLink size={17} />
                      )}
                      View image
                    </button>

                    <div className="ss-extra">
                      <h3>
                        <Info size={17} />
                        Additional information
                      </h3>
                      <dl>
                        <div>
                          <dt>Request source</dt>
                          <dd>Authorized monitoring request</dd>
                        </div>
                        <div>
                          <dt>Resolution</dt>
                          <dd>
                            {selected.width &&
                            selected.height
                              ? `${selected.width} × ${selected.height}`
                              : "Not available"}
                          </dd>
                        </div>
                        <div>
                          <dt>Consent</dt>
                          <dd>
                            {selected.consent_confirmed_at
                              ? "Confirmed"
                              : selected.consent_required
                                ? "Required"
                                : "Not required"}
                          </dd>
                        </div>
                        <div>
                          <dt>Requested</dt>
                          <dd>
                            {formatDate(selected.requested_at)}
                          </dd>
                        </div>
                        <div>
                          <dt>Expires</dt>
                          <dd>
                            {formatDate(selected.expires_at)}
                          </dd>
                        </div>
                      </dl>
                    </div>
                  </>
                ) : (
                  <div className="ss-empty ss-side-empty">
                    <Camera size={29} />
                    <strong>No screenshot selected</strong>
                    <p>
                      Select a capture from the timeline
                      or request history.
                    </p>
                  </div>
                )}
              </aside>
            </div>
          </>
        )}

        {requestOpen && (
          <div
            className="ss-overlay"
            role="presentation"
            onMouseDown={(event) => {
              if (event.currentTarget === event.target) {
                setRequestOpen(false);
              }
            }}
          >
            <section
              className="ss-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="ss-request-title"
            >
              <div className="ss-modal-header">
                <div>
                  <h2 id="ss-request-title">
                    Request screenshot
                  </h2>
                  <p>
                    Ask an authorized desktop agent to
                    capture its screen.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setRequestOpen(false)}
                  aria-label="Close"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="ss-modal-body">
                <label>
                  Device
                  <select
                    value={requestDeviceId}
                    onChange={(event) =>
                      setRequestDeviceId(event.target.value)
                    }
                  >
                    <option value="">
                      Select a connected device
                    </option>
                    {availableDevices.map((device) => (
                      <option
                        value={device.id}
                        key={device.id}
                      >
                        {device.name} — {device.employee}
                      </option>
                    ))}
                  </select>
                </label>

                {availableDevices.length === 0 && (
                  <p className="ss-warning">
                    No connected monitoring devices are
                    available. The agent must be enrolled
                    and sending heartbeats before a
                    screenshot can be requested.
                  </p>
                )}

                <label>
                  Reason (optional)
                  <textarea
                    maxLength={500}
                    rows={3}
                    value={reason}
                    onChange={(event) =>
                      setReason(event.target.value)
                    }
                    placeholder="Reason for requesting this capture"
                  />
                </label>

                <div className="ss-consent-note">
                  <ShieldCheck size={19} />
                  Screenshot capture follows the
                  workspace consent policy and requires
                  visible capture indicators when enabled
                  by the backend.
                </div>

                {requestMessage && (
                  <p className="ss-warning">
                    {requestMessage}
                  </p>
                )}

                <div className="ss-modal-actions">
                  <button
                    type="button"
                    onClick={() => setRequestOpen(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="ss-submit"
                    disabled={
                      !requestDeviceId ||
                      requesting ||
                      !canRequest
                    }
                    onClick={() =>
                      void requestScreenshot()
                    }
                  >
                    {requesting ? (
                      <Loader2
                        size={16}
                        className="ss-spin"
                      />
                    ) : (
                      <Camera size={16} />
                    )}
                    Send request
                  </button>
                </div>
              </div>
            </section>
          </div>
        )}

        <style jsx global>{`
          .ss-page {
            --ss-text: #101d3c;
            --ss-muted: #6d7e98;
            --ss-border: #e5e8ed;
            min-height: 100%;
            padding: 19px 21px 30px;
            background: #fbfaf7;
            color: var(--ss-text);
            font-size: 12px;
          }
          .ss-page * {
            box-sizing: border-box;
          }
          .ss-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 20px;
          }
          .ss-header h1 {
            margin: 0;
            font-size: 29px;
            letter-spacing: -.7px;
            line-height: 1.15;
          }
          .ss-header p {
            margin: 5px 0 0;
            color: var(--ss-muted);
            font-size: 14px;
          }
          .ss-storage {
            display: flex;
            align-items: center;
            gap: 11px;
            border: 1px solid var(--ss-border);
            padding: 10px 12px;
            border-radius: 10px;
            background: #fff;
          }
          .ss-storage span {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }
          .ss-storage small {
            color: var(--ss-muted);
          }
          .ss-tabs {
            display: flex;
            align-items: center;
            border-bottom: 1px solid var(--ss-border);
            gap: 6px;
            margin-bottom: 15px;
          }
          .ss-tabs button {
            border: 0;
            background: transparent;
            color: var(--ss-text);
            cursor: pointer;
            min-height: 45px;
            padding: 0 16px;
            display: flex;
            align-items: center;
            gap: 9px;
            font: inherit;
            font-weight: 600;
          }
          .ss-tabs button.ss-active-tab {
            background: #fff8e9;
            border-bottom: 3px solid #ffad00;
            border-radius: 8px 8px 0 0;
          }
          .ss-tabs button span {
            color: var(--ss-muted);
          }
          .ss-tabs .ss-request-btn {
            margin-left: auto;
            min-height: 37px;
            margin-bottom: 5px;
            border-radius: 7px;
            background: #17212d;
            color: white;
            padding: 0 15px;
          }
          .ss-tabs button:disabled {
            opacity: .5;
            cursor: not-allowed;
          }
          .ss-filters {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            margin-bottom: 15px;
          }
          .ss-filters > select,
          .ss-date,
          .ss-search,
          .ss-refresh {
            border: 1px solid #e1e5eb;
            border-radius: 8px;
            background: white;
            height: 39px;
            color: var(--ss-text);
            font: inherit;
          }
          .ss-filters > select {
            padding: 0 12px;
            min-width: 178px;
          }
          .ss-date,
          .ss-search {
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 0 11px;
          }
          .ss-date input,
          .ss-search input {
            border: none;
            outline: none;
            background: transparent;
            color: inherit;
            font: inherit;
          }
          .ss-search {
            flex: 1;
            max-width: 300px;
          }
          .ss-search input {
            width: 100%;
          }
          .ss-refresh {
            display: flex;
            align-items: center;
            gap: 7px;
            padding: 0 13px;
            cursor: pointer;
            margin-left: auto;
          }
          .ss-grid-layout {
            display: grid;
            grid-template-columns: minmax(0, 2.1fr) minmax(320px, .9fr);
            gap: 16px;
            align-items: start;
          }
          .ss-left,
          .ss-right {
            min-width: 0;
          }
          .ss-timeline {
            display: flex;
            align-items: center;
            gap: 13px;
            padding: 12px 4px;
            min-height: 68px;
            margin-bottom: 8px;
            border: 1px solid #ececef;
            border-radius: 10px;
            background: #fffefa;
          }
          .ss-timeline > button {
            border: 1px solid #e5e8ef;
            background: white;
            border-radius: 7px;
            width: 32px;
            height: 34px;
            display: grid;
            place-items: center;
            cursor: pointer;
            flex-shrink: 0;
          }
          .ss-timeline button:disabled {
            opacity: .35;
            cursor: not-allowed;
          }
          .ss-line {
            flex: 1;
            display: flex;
            justify-content: space-around;
            align-items: center;
            position: relative;
            min-width: 0;
            padding: 8px 0;
          }
          .ss-line::after {
            content: "";
            position: absolute;
            height: 2px;
            background: #ffad0a;
            left: 0;
            right: 0;
            bottom: 9px;
          }
          .ss-line .ss-point {
            background: transparent;
            border: 0;
            padding: 0;
            min-width: 0;
            display: grid;
            justify-items: center;
            gap: 11px;
            color: #475a78;
            cursor: pointer;
            z-index: 1;
            font: inherit;
          }
          .ss-point i {
            width: 12px;
            height: 12px;
            background: white;
            border: 2px solid #ffae00;
            border-radius: 50%;
          }
          .ss-point.ss-point-selected i {
            background: #ffad0a;
            outline: 3px solid #fff;
            box-shadow: 0 0 0 2px #ffaa00;
          }
          .ss-empty-time {
            color: #8592a5;
          }
          .ss-gallery {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 11px;
            margin-bottom: 16px;
          }
          .ss-shot {
            display: flex;
            flex-direction: column;
            min-width: 0;
            text-align: left;
            padding: 10px;
            border: 1px solid #e5e8ed;
            border-radius: 10px;
            background: #fffdfa;
            cursor: pointer;
            color: var(--ss-text);
            font: inherit;
          }
          .ss-shot.ss-shot-selected {
            border-color: #ffac00;
            box-shadow: 0 0 0 1px #ffc354;
          }
          .ss-preview,
          .ss-detail-preview {
            overflow: hidden;
            background: #f2f3f5;
            border-radius: 8px;
            border: 1px solid #e8e9ec;
          }
          .ss-preview {
            height: 134px;
          }
          .ss-preview img,
          .ss-detail-preview img {
            width: 100%;
            height: 100%;
            object-fit: contain;
          }
          .ss-placeholder {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            text-align: center;
            padding: 10px;
            color: #8292a8;
          }
          .ss-shot-meta {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 6px;
            flex-wrap: wrap;
            padding-top: 10px;
            font-size: 11px;
            color: #697992;
          }
          .ss-shot-employee {
            font-weight: 650;
            color: var(--ss-text);
            display: inline-flex;
            align-items: center;
            gap: 6px;
          }
          .ss-shot-employee i {
            width: 9px;
            height: 9px;
            border-radius: 50%;
          }
          .ss-green {
            background: #23bd79;
          }
          .ss-yellow {
            background: #ffb819;
          }
          .ss-shot-meta small {
            color: #7e8ba1;
          }
          .ss-request-history,
          .ss-right {
            background: #fffefa;
            border: 1px solid #e5e7eb;
            border-radius: 11px;
            overflow: hidden;
          }
          .ss-section-heading {
            min-height: 49px;
            padding: 11px 13px;
            display: flex;
            align-items: center;
            justify-content: space-between;
          }
          .ss-section-heading h2 {
            margin: 0;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 9px;
          }
          .ss-section-heading span {
            color: #d38200;
          }
          .ss-section-heading button {
            background: transparent;
            border: none;
            cursor: pointer;
          }
          .ss-table-scroll {
            overflow-x: auto;
          }
          .ss-request-history table {
            width: 100%;
            min-width: 650px;
            border-collapse: collapse;
            text-align: left;
          }
          .ss-request-history th {
            padding: 11px 10px;
            background: #f6f7f8;
            font-size: 10px;
          }
          .ss-request-history td {
            border-top: 1px solid #edf0f2;
            padding: 9px 10px;
            font-size: 11px;
          }
          .ss-status {
            display: inline-flex;
            padding: 4px 8px;
            border-radius: 5px;
            background: #eef1f5;
            color: #536177;
            font-size: 11px;
          }
          .ss-status.ss-completed {
            background: #def8e9;
            color: #16834e;
          }
          .ss-status.ss-requested,
          .ss-status.ss-pending {
            background: #fff0cc;
            color: #a87600;
          }
          .ss-status.ss-failed,
          .ss-status.ss-denied {
            background: #ffe5e5;
            color: #c22d2d;
          }
          .ss-view-details {
            display: flex;
            align-items: center;
            gap: 5px;
            border: 1px solid #e1e5ea;
            background: white;
            border-radius: 6px;
            padding: 6px 9px;
            font: inherit;
            cursor: pointer;
          }
          .ss-detail-preview {
            margin: 5px 13px 14px;
            height: 176px;
          }
          .ss-detail-facts,
          .ss-extra dl {
            padding: 0 15px;
            margin: 0;
          }
          .ss-detail-facts > div,
          .ss-extra dl > div {
            display: grid;
            grid-template-columns: 1fr 1.15fr;
            padding: 9px 0;
            gap: 10px;
            font-size: 11px;
          }
          .ss-detail-facts dt {
            display: flex;
            align-items: center;
            gap: 9px;
            color: #526380;
          }
          .ss-detail-facts dd,
          .ss-extra dd {
            font-weight: 650;
            margin: 0;
            overflow-wrap: anywhere;
          }
          .ss-open-image {
            height: 40px;
            width: calc(100% - 26px);
            margin: 9px 13px 15px;
            border-radius: 7px;
            color: white;
            background: #17232f;
            border: none;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            font: inherit;
            font-weight: 650;
            cursor: pointer;
          }
          .ss-open-image:disabled {
            opacity: .45;
            cursor: not-allowed;
          }
          .ss-extra {
            margin: 0 13px 16px;
            border-top: 1px solid #e8ebef;
            padding-top: 11px;
          }
          .ss-extra h3 {
            display: flex;
            gap: 8px;
            align-items: center;
            font-size: 13px;
          }
          .ss-extra dl {
            padding: 0;
          }
          .ss-extra dt {
            color: #60718c;
          }
          .ss-empty {
            min-height: 240px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            gap: 11px;
            padding: 20px;
            color: #8998ad;
          }
          .ss-empty strong {
            color: var(--ss-text);
            font-size: 13px;
          }
          .ss-empty p {
            max-width: 300px;
            line-height: 1.6;
            margin: 0;
          }
          .ss-side-empty {
            min-height: 360px;
          }
          .ss-error,
          .ss-message {
            display: flex;
            align-items: center;
            gap: 10px;
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 14px;
            background: #fff0f0;
            border: 1px solid #efbcbc;
            color: #b12b2b;
          }
          .ss-error span {
            flex: 1;
          }
          .ss-error button {
            margin-left: auto;
            border: 1px solid #eec0c0;
            background: white;
            border-radius: 6px;
            padding: 5px 10px;
            cursor: pointer;
          }
          .ss-message {
            background: #eaf6ed;
            color: #28764d;
            border-color: #bde2c9;
          }
          .ss-overlay {
            position: fixed;
            inset: 0;
            z-index: 200;
            background: #101b3099;
            display: grid;
            place-items: center;
            padding: 20px;
          }
          .ss-modal {
            background: #fffefa;
            width: min(520px, 100%);
            border: 1px solid #e4e7ed;
            border-radius: 13px;
            overflow: hidden;
            box-shadow: 0 20px 70px #0004;
          }
          .ss-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            padding: 19px 20px;
            border-bottom: 1px solid #e9eaee;
          }
          .ss-modal-header h2 {
            font-size: 21px;
            margin: 0;
          }
          .ss-modal-header p {
            margin: 7px 0 0;
            color: #72819a;
          }
          .ss-modal-header button {
            border: none;
            background: transparent;
            cursor: pointer;
          }
          .ss-modal-body {
            padding: 21px;
          }
          .ss-modal-body > label {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 16px;
            font-weight: 650;
          }
          .ss-modal-body select,
          .ss-modal-body textarea {
            width: 100%;
            padding: 10px 11px;
            background: white;
            border: 1px solid #dfe4eb;
            color: #152341;
            border-radius: 7px;
            font: inherit;
            font-weight: 400;
          }
          .ss-consent-note {
            display: flex;
            gap: 10px;
            align-items: start;
            background: #f0f6fd;
            border: 1px solid #d8e7f6;
            padding: 12px;
            border-radius: 7px;
            line-height: 1.6;
            color: #425b79;
          }
          .ss-modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 9px;
            margin-top: 21px;
          }
          .ss-modal-actions button {
            border-radius: 7px;
            border: 1px solid #dfe3e9;
            background: white;
            padding: 10px 16px;
            cursor: pointer;
            font: inherit;
          }
          .ss-modal-actions button.ss-submit {
            display: flex;
            align-items: center;
            gap: 8px;
            background: #152330;
            border-color: #152330;
            color: white;
          }
          .ss-modal-actions button:disabled {
            opacity: .45;
            cursor: not-allowed;
          }
          .ss-warning {
            background: #fff8e8;
            color: #916500;
            border: 1px solid #f6dda6;
            padding: 11px;
            border-radius: 7px;
            line-height: 1.6;
          }
          .ss-spin {
            animation: ss-spin 1s linear infinite;
          }
          @keyframes ss-spin {
            to { transform: rotate(360deg); }
          }
          @media (max-width: 1200px) {
            .ss-grid-layout {
              grid-template-columns: 1fr;
            }
            .ss-right {
              max-width: none;
            }
          }
          @media (max-width: 800px) {
            .ss-header {
              align-items: flex-start;
              flex-direction: column;
            }
            .ss-gallery {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
          }
          @media (max-width: 520px) {
            .ss-page {
              padding: 15px 12px;
            }
            .ss-header h1 {
              font-size: 24px;
            }
            .ss-tabs {
              flex-wrap: wrap;
            }
            .ss-tabs .ss-request-btn {
              margin-left: 0;
              width: 100%;
            }
            .ss-gallery {
              grid-template-columns: 1fr;
            }
          }
        `}</style>
      </main>
    </WorkspaceRequired>
  );
}

function UsersIcon() {
  return <UserRound size={17} />;
}
