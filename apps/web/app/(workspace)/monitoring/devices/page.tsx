
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
  Apple,
  Camera,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ClipboardCopy,
  Download,
  ExternalLink,
  Info,
  Laptop,
  Monitor,
  MoreVertical,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  X,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";

type ReadinessItem = {
  device_id: string;
  employee_id: string;
  device_name: string;
  platform: string;
  os_version: string | null;
  agent_version: string;
  status: "online" | "offline" | "disabled";
  last_seen_at: string;
  heartbeat_age_seconds: number | null;
  is_online: boolean;
  consent_granted: boolean;
  activity_capability: boolean;
  screen_capability: boolean;
  monitoring_ready: boolean;
  live_ready: boolean;
  needs_setup: boolean;
  setup_reasons?: string[];
};

type ReadinessResponse = {
  summary: {
    total: number;
    online: number;
    offline: number;
    disabled: number;
    monitoring_ready: number;
    live_ready: number;
    needs_setup: number;
    online_timeout_seconds: number;
  };
  devices?: ReadinessItem[];
};

type AgentDevice = {
  id: string;
  employee_id: string;
  device_name: string;
  platform: string;
  os_version: string | null;
  agent_version: string;
  status: string;
  is_disabled: boolean;
  last_seen_at: string;
};

type AgentListResponse = {
  items?: AgentDevice[];
  total: number;
  limit: number;
  offset: number;
};

type GeneralDevice = {
  id: string;
  device_uuid: string;
  employee_id: string | null;
  hostname: string;
  os_name: string;
  os_version: string | null;
  agent_version: string | null;
  status: string;
  last_seen_at: string | null;
  is_active: boolean;
};

type GeneralDeviceResponse = {
  devices?: GeneralDevice[];
  total: number;
};

type Employee = {
  id: string;
  full_name: string;
  first_name: string;
  last_name: string;
};

type EmployeeResponse = {
  employees?: Employee[];
  total: number;
};

type Status = "online" | "offline" | "disabled" | "pending";

type Device = {
  id: string;
  employeeId: string | null;
  name: string;
  employee: string;
  os: string;
  platform: string;
  version: string;
  lastSeen: string | null;
  status: Status;
  monitoringReady: boolean | null;
  liveReady: boolean | null;
  activity: boolean | null;
  screenshots: boolean | null;
  consentGranted: boolean | null;
  setupReasons: string[];
  source: "desktop-agent" | "general";
};

type SortKey =
  | "name"
  | "employee"
  | "os"
  | "version"
  | "status"
  | "lastSeen";

const PER_PAGE = 10;
const AGENT_PAGE_LIMIT = 500;

function elapsed(value: string | null): string {
  if (!value) return "No signal";

  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) return "No signal";

  const difference = Math.max(
    0,
    Math.floor((Date.now() - timestamp) / 1000)
  );

  if (difference < 60) return `${difference} sec ago`;
  if (difference < 3600) {
    return `${Math.floor(difference / 60)} min ago`;
  }
  if (difference < 86400) {
    return `${Math.floor(difference / 3600)} hours ago`;
  }
  return `${Math.floor(difference / 86400)} days ago`;
}

const DEFAULT_ONLINE_TIMEOUT_SECONDS = 120;

function heartbeatIsFresh(
  lastSeenAt: string | null,
  heartbeatAgeSeconds: number | null = null,
  timeoutSeconds = DEFAULT_ONLINE_TIMEOUT_SECONDS
): boolean {
  if (heartbeatAgeSeconds !== null) {
    return heartbeatAgeSeconds <= timeoutSeconds;
  }

  if (!lastSeenAt) {
    return false;
  }

  const timestamp = new Date(lastSeenAt).getTime();

  if (Number.isNaN(timestamp)) {
    return false;
  }

  return Date.now() - timestamp <= timeoutSeconds * 1000;
}

function osFamily(value: string): string {
  const os = value.toLowerCase();
  if (os.includes("win")) return "Windows";
  if (os.includes("mac") || os.includes("darwin")) {
    return "macOS";
  }
  if (os.includes("linux") || os.includes("ubuntu")) {
    return "Linux";
  }
  return "Other";
}

function OperatingSystem({
  platform,
  size = 17,
}: {
  platform: string;
  size?: number;
}) {
  const family = osFamily(platform);

  if (family === "macOS") {
    return <Apple size={size} fill="currentColor" color="#647084" />;
  }

  if (family === "Windows") {
    return (
      <span
        className="d-os-windows"
        style={{ width: size, height: size }}
        aria-label="Windows"
      >
        <i />
        <i />
        <i />
        <i />
      </span>
    );
  }

  return <Laptop size={size} />;
}

function Dot({ status }: { status: Status }) {
  return <i className={`d-dot d-dot-${status}`} />;
}

function StatusText({ status }: { status: Status }) {
  return (
    <span className="d-status">
      <Dot status={status} />
      {status === "online"
        ? "Online"
        : status === "disabled"
          ? "Disabled"
          : status === "pending"
            ? "Not enrolled"
            : "Offline"}
    </span>
  );
}

function CapabilityRow({
  icon,
  title,
  value,
}: {
  icon: React.ReactNode;
  title: string;
  value: boolean | null;
}) {
  return (
    <div className="d-cap-row">
      <span>
        {icon}
        {title}
      </span>
      <b
        className={
          value === true
            ? "d-cap-yes"
            : value === false
              ? "d-cap-no"
              : "d-cap-unknown"
        }
      >
        {value === true
          ? "Ready"
          : value === false
            ? "Unavailable"
            : "Unknown"}
      </b>
    </div>
  );
}

function csvEscape(value: string): string {
  const protectedValue = /^[=+\-@\t\r]/.test(value)
    ? `'${value}`
    : value;

  return `"${protectedValue.replaceAll('"', '""')}"`;
}

function exportDevices(devices: Device[]) {
  const headings = [
    "Device",
    "Employee",
    "OS",
    "Agent version",
    "Connection",
    "Last heartbeat",
    "Monitoring ready",
    "Live ready",
    "Source",
  ];

  const rows = devices.map((item) => [
    item.name,
    item.employee,
    item.os,
    item.version,
    item.status,
    item.lastSeen || "",
    item.monitoringReady === null
      ? "Unknown"
      : item.monitoringReady
        ? "Yes"
        : "No",
    item.liveReady === null
      ? "Unknown"
      : item.liveReady
        ? "Yes"
        : "No",
    item.source,
  ]);

  const csv = [headings, ...rows]
    .map((row) => row.map(csvEscape).join(","))
    .join("\r\n");

  const blob = new Blob(["\uFEFF", csv], {
    type: "text/csv;charset=utf-8",
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "workforce-monitoring-devices.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function MonitoringDevicesPage() {
  const { workspaceId, permissions, navigationView } =
    useWorkspace();

  const canRead = hasAnyPermission(
    permissions,
    [
      "monitoring.all.read",
      "monitoring.team.read",
      "monitoring.self.read",
      "devices.all.read",
      "devices.team.read",
      "devices.self.read",
    ],
    navigationView
  );

  const canManage = hasAnyPermission(
    permissions,
    ["devices.manage"],
    navigationView
  );

  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);

  const [search, setSearch] = useState("");
  const [platform, setPlatform] = useState("all");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(PER_PAGE);

  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortAsc, setSortAsc] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(
    null
  );
  const [checked, setChecked] = useState<string[]>([]);
  const [menuOpen, setMenuOpen] = useState(false);

  const [setupOpen, setSetupOpen] = useState(false);
  const [setupMessage, setSetupMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const fetchData = useCallback(
    async (quiet = false) => {
      if (!workspaceId || !canRead) {
        setDevices([]);
        setLoading(false);
        return;
      }

      if (quiet) setRefreshing(true);
      else setLoading(true);

      const base = `/workspaces/${workspaceId}`;

      try {
        const results = await Promise.allSettled([
          api.get<ReadinessResponse>(
            `${base}/devices/readiness`
          ),
          api.get<AgentListResponse>(
            `${base}/desktop-agent/devices`,
            {
              query: {
                limit: AGENT_PAGE_LIMIT,
                offset: 0,
              },
            }
          ),
          api.get<GeneralDeviceResponse>(
            `${base}/devices`,
            {
              query: { include_inactive: true },
            }
          ),
          api.get<EmployeeResponse>(
            `${base}/employees`,
            {
              query: { include_inactive: true },
            }
          ),
        ]);

        const [
          readinessResult,
          agentsResult,
          generalResult,
          employeesResult,
        ] = results;

        const errors: string[] = [];

        const readiness =
          readinessResult.status === "fulfilled"
            ? readinessResult.value
            : null;

        const agents =
          agentsResult.status === "fulfilled"
            ? agentsResult.value
            : null;

        const general =
          generalResult.status === "fulfilled"
            ? generalResult.value
            : null;

        const employees =
          employeesResult.status === "fulfilled"
            ? employeesResult.value
            : null;

        if (readinessResult.status === "rejected") {
          errors.push("Device readiness API unavailable");
        }
        if (agentsResult.status === "rejected") {
          errors.push("Desktop-agent list unavailable");
        }
        if (generalResult.status === "rejected") {
          errors.push("General-device list unavailable");
        }
        if (employeesResult.status === "rejected") {
          errors.push("Employee directory unavailable");
        }

        if (!readiness && !agents && !general) {
          throw new Error(
            "Unable to retrieve devices from any device API."
          );
        }

        const employeeNames = new Map(
          (employees?.employees || []).map((employee) => [
            employee.id,
            employee.full_name?.trim() ||
              `${employee.first_name} ${employee.last_name}`.trim(),
          ])
        );

        const rows = new Map<string, Device>();

        const agentRows = agents?.items || [];
        const readinessRows = readiness?.devices || [];

        // Prefer the backend's authoritative readiness
        // projection: it calculates heartbeat freshness.
        for (const item of readinessRows) {
          rows.set(item.device_id, {
            id: item.device_id,
            employeeId: item.employee_id,
            name: item.device_name,
            employee:
              employeeNames.get(item.employee_id) ||
              "Unknown employee",
            os:
              `${item.platform} ${item.os_version || ""}`.trim(),
            platform: osFamily(item.platform),
            version: item.agent_version,
            lastSeen: item.last_seen_at,
            status:
              item.status === "disabled"
                ? "disabled"
                : heartbeatIsFresh(
                    item.last_seen_at,
                    item.heartbeat_age_seconds,
                    readiness?.summary.online_timeout_seconds ??
                      DEFAULT_ONLINE_TIMEOUT_SECONDS
                  )
                  ? "online"
                  : "offline",
            monitoringReady: item.monitoring_ready,
            liveReady: item.live_ready,
            activity: item.activity_capability,
            screenshots: item.screen_capability,
            consentGranted: item.consent_granted,
            setupReasons: item.setup_reasons || [],
            source: "desktop-agent",
          });
        }

        // Merge registration metadata when a readiness
        // record is present. If readiness is temporarily unavailable,
        // derive the status from the latest authenticated heartbeat.
        for (const agent of agentRows) {
          const existing = rows.get(agent.id);

          if (existing) {
            rows.set(agent.id, {
              ...existing,
              name: existing.name || agent.device_name,
              version:
                existing.version || agent.agent_version,
            });
            continue;
          }

          rows.set(agent.id, {
            id: agent.id,
            employeeId: agent.employee_id,
            name: agent.device_name,
            employee:
              employeeNames.get(agent.employee_id) ||
              "Unknown employee",
            os:
              `${agent.platform} ${
                agent.os_version || ""
              }`.trim(),
            platform: osFamily(agent.platform),
            version: agent.agent_version,
            lastSeen: agent.last_seen_at,
            status: agent.is_disabled
              ? "disabled"
              : heartbeatIsFresh(agent.last_seen_at)
                ? "online"
                : "offline",
            monitoringReady: null,
            liveReady: null,
            activity: null,
            screenshots: null,
            consentGranted: null,
            setupReasons: [
              "Readiness details not returned by server",
            ],
            source: "desktop-agent",
          });
        }

        // General devices can exist without an enrolled
        // desktop monitoring agent. Show them, but mark
        // them "Not enrolled", never falsely "Online".
        const usedGeneralIds = new Set<string>();

        for (const device of general?.devices || []) {
          const matched = [...rows.values()].find(
            (row) =>
              row.source === "desktop-agent" &&
              row.employeeId === device.employee_id &&
              row.name.trim().toLowerCase() ===
                device.hostname.trim().toLowerCase()
          );

          if (matched) {
            usedGeneralIds.add(device.id);
            continue;
          }

          if (usedGeneralIds.has(device.id)) continue;

          rows.set(`general:${device.id}`, {
            id: `general:${device.id}`,
            employeeId: device.employee_id,
            name: device.hostname,
            employee: device.employee_id
              ? employeeNames.get(device.employee_id) ||
                "Unknown employee"
              : "Unassigned",
            os:
              `${device.os_name} ${
                device.os_version || ""
              }`.trim(),
            platform: osFamily(device.os_name),
            version:
              device.agent_version || "Not installed",
            lastSeen: device.last_seen_at,
            status:
              device.status === "disabled" ||
              device.status === "revoked"
                ? "disabled"
                : "pending",
            monitoringReady: false,
            liveReady: false,
            activity: false,
            screenshots: false,
            consentGranted: null,
            setupReasons: [
              "Desktop monitoring agent not enrolled",
            ],
            source: "general",
          });
        }

        if (
          agents &&
          agents.total > AGENT_PAGE_LIMIT
        ) {
          errors.push(
            "More than 500 desktop agents exist. Additional backend pagination is needed."
          );
        }

        setDevices([...rows.values()]);
        setWarnings(errors);
        setError("");
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Failed to load devices."
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [workspaceId, canRead]
  );

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!workspaceId || !canRead) return;

    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void fetchData(true);
      }
    }, 10000);

    return () => window.clearInterval(timer);
  }, [workspaceId, canRead, fetchData]);

  useEffect(() => {
    const first = devices[0];

    if (!first) {
      setSelectedId(null);
      return;
    }

    if (
      selectedId &&
      devices.some((device) => device.id === selectedId)
    ) {
      return;
    }

    setSelectedId(first.id);
  }, [devices, selectedId]);

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();

    const result = devices.filter((device) => {
      const matchesSearch =
        !needle ||
        [
          device.name,
          device.employee,
          device.os,
          device.version,
        ]
          .join(" ")
          .toLowerCase()
          .includes(needle);

      const matchesPlatform =
        platform === "all" || device.platform === platform;

      const matchesStatus =
        status === "all" || device.status === status;

      return (
        matchesSearch &&
        matchesPlatform &&
        matchesStatus
      );
    });

    result.sort((a, b) => {
      const aValue = String(a[sortKey] || "");
      const bValue = String(b[sortKey] || "");
      const compared = aValue.localeCompare(
        bValue,
        undefined,
        { numeric: true }
      );
      return sortAsc ? compared : -compared;
    });

    return result;
  }, [devices, search, platform, status, sortKey, sortAsc]);

  const totals = useMemo(() => {
    const registered = devices.filter(
      (device) => device.source === "desktop-agent"
    );

    return {
      total: devices.length,
      connected: registered.filter(
        (device) => device.status === "online"
      ).length,
      unavailable: devices.filter(
        (device) =>
          device.status === "offline" ||
          device.status === "disabled" ||
          device.status === "pending"
      ).length,
      updateRequired: null as number | null,
    };
  }, [devices]);

  const percent = (value: number) =>
    totals.total
      ? `${((value / totals.total) * 100).toFixed(1)}%`
      : "0.0%";

  const maxPages = Math.max(
    1,
    Math.ceil(filtered.length / rowsPerPage)
  );

  const safePage = Math.min(page, maxPages);

  const visible = filtered.slice(
    (safePage - 1) * rowsPerPage,
    safePage * rowsPerPage
  );

  const selected =
    devices.find((device) => device.id === selectedId) ||
    null;

  const platforms = [
    ...new Set(devices.map((device) => device.platform)),
  ].sort();

  function changeSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc((value) => !value);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  }

  async function copyWorkspaceId() {
    if (!workspaceId) return;

    try {
      await navigator.clipboard.writeText(workspaceId);
      setSetupMessage("Workspace ID copied.");
    } catch {
      setSetupMessage("Unable to copy workspace ID.");
    }
  }

  async function disableDevice() {
    if (
      !workspaceId ||
      !selected ||
      selected.source !== "desktop-agent" ||
      !canManage
    ) {
      return;
    }

    const confirmed = window.confirm(
      `Disable ${selected.name}?\n\nThis will prevent the desktop monitoring agent from reporting until it is re-enabled through the authorized device workflow.`
    );

    if (!confirmed) return;

    setBusy(true);

    try {
      await api.post(
        `/workspaces/${workspaceId}/desktop-agent/devices/${selected.id}/disable`
      );

      setMenuOpen(false);
      await fetchData(true);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to disable device."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspaceRequired>
      <main className="d-page">
        <header className="d-page-header">
          <div>
            <h1>Monitoring Devices</h1>
            <p>
              View and manage devices across your
              organization.
            </p>
          </div>

          <div className="d-header-buttons">
            <button
              type="button"
              className="d-btn d-btn-white"
              disabled={!canManage}
              onClick={() => {
                setSetupMessage("");
                setSetupOpen(true);
              }}
            >
              <Download size={17} />
              Register device
            </button>

            <button
              type="button"
              className="d-btn d-btn-dark"
              disabled={!canManage}
              onClick={() => {
                setSetupMessage("");
                setSetupOpen(true);
              }}
            >
              <Settings size={18} />
              Agent setup
            </button>
          </div>
        </header>

        {!canRead ? (
          <div className="d-notice d-notice-error">
            You do not have permission to view monitoring
            devices.
          </div>
        ) : (
          <>
            {error && (
              <div className="d-notice d-notice-error">
                <AlertTriangle size={17} />
                <span>{error}</span>
                <button
                  type="button"
                  onClick={() => void fetchData()}
                >
                  Retry
                </button>
              </div>
            )}

            {warnings.length > 0 && (
              <div className="d-notice d-notice-warning">
                <Info size={17} />
                <span>{warnings.join(". ")}</span>
              </div>
            )}

            <section className="d-metrics">
              <Metric
                label="Devices"
                value={totals.total}
                detail="Total devices"
              />
              <Metric
                label="Connected"
                value={totals.connected}
                detail={`${percent(
                  totals.connected
                )} online`}
                color="green"
              />
              <Metric
                label="Update required"
                value={totals.updateRequired}
                detail="Version compliance not configured"
                color="yellow"
              />
              <Metric
                label="Unavailable"
                value={totals.unavailable}
                detail={`${percent(
                  totals.unavailable
                )} unavailable`}
                color="red"
              />
            </section>

            <div className="d-layout">
              <section className="d-left">
                <div className="d-filters">
                  <label className="d-search">
                    <Search size={17} />
                    <input
                      value={search}
                      placeholder="Search devices, employee or device name..."
                      onChange={(event) => {
                        setSearch(event.target.value);
                        setPage(1);
                      }}
                    />
                  </label>

                  <label className="d-select">
                    <select
                      aria-label="Platform filter"
                      value={platform}
                      onChange={(event) => {
                        setPlatform(event.target.value);
                        setPage(1);
                      }}
                    >
                      <option value="all">
                        All platforms
                      </option>
                      {platforms.map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                    <ChevronDown size={15} />
                  </label>

                  <label className="d-select">
                    <select
                      aria-label="Connection status filter"
                      value={status}
                      onChange={(event) => {
                        setStatus(event.target.value);
                        setPage(1);
                      }}
                    >
                      <option value="all">
                        All connection status
                      </option>
                      <option value="online">
                        Online
                      </option>
                      <option value="offline">
                        Offline
                      </option>
                      <option value="disabled">
                        Disabled
                      </option>
                      <option value="pending">
                        Not enrolled
                      </option>
                    </select>
                    <ChevronDown size={15} />
                  </label>

                  <button
                    type="button"
                    className="d-clear"
                    onClick={() => {
                      setSearch("");
                      setPlatform("all");
                      setStatus("all");
                      setPage(1);
                    }}
                  >
                    Clear filters
                  </button>
                </div>

                <div className="d-card d-inventory">
                  <div className="d-card-title">
                    <h2>
                      <Monitor size={20} />
                      Device inventory
                    </h2>

                    <div className="d-heading-actions">
                      <span>
                        Showing {filtered.length} devices
                      </span>

                      <button
                        type="button"
                        title="Refresh"
                        disabled={refreshing}
                        onClick={() => void fetchData(true)}
                      >
                        <RefreshCw
                          size={16}
                          className={
                            refreshing ? "d-spin" : ""
                          }
                        />
                      </button>

                      <button
                        type="button"
                        title="Export filtered devices"
                        onClick={() => exportDevices(filtered)}
                      >
                        <Download size={16} />
                      </button>
                    </div>
                  </div>

                  <div className="d-table-wrap">
                    <table className="d-table">
                      <thead>
                        <tr>
                          <th className="d-check-cell">
                            <input
                              type="checkbox"
                              aria-label="Select visible devices"
                              checked={
                                visible.length > 0 &&
                                visible.every((item) =>
                                  checked.includes(item.id)
                                )
                              }
                              onChange={(event) => {
                                const ids = visible.map(
                                  (item) => item.id
                                );

                                if (event.target.checked) {
                                  setChecked((previous) => [
                                    ...new Set([
                                      ...previous,
                                      ...ids,
                                    ]),
                                  ]);
                                } else {
                                  setChecked((previous) =>
                                    previous.filter(
                                      (id) =>
                                        !ids.includes(id)
                                    )
                                  );
                                }
                              }}
                            />
                          </th>

                          {(
                            [
                              ["name", "Device"],
                              ["employee", "Assigned employee"],
                              ["os", "OS"],
                              ["version", "Agent version"],
                              ["status", "Connection"],
                              ["lastSeen", "Last heartbeat"],
                            ] as [SortKey, string][]
                          ).map(([key, label]) => (
                            <th key={key}>
                              <button
                                type="button"
                                onClick={() =>
                                  changeSort(key)
                                }
                              >
                                {label}
                                <span className="d-sort">
                                  {sortKey === key
                                    ? sortAsc
                                      ? "↑"
                                      : "↓"
                                    : "↕"}
                                </span>
                              </button>
                            </th>
                          ))}
                          <th>Capabilities</th>
                        </tr>
                      </thead>

                      <tbody>
                        {visible.map((device) => (
                          <tr
                            key={device.id}
                            className={
                              selected?.id === device.id
                                ? "d-selected-row"
                                : ""
                            }
                          >
                            <td className="d-check-cell">
                              <input
                                type="checkbox"
                                aria-label={`Select ${device.name}`}
                                checked={checked.includes(
                                  device.id
                                )}
                                onChange={(event) => {
                                  setChecked((previous) =>
                                    event.target.checked
                                      ? [
                                          ...previous,
                                          device.id,
                                        ]
                                      : previous.filter(
                                          (id) =>
                                            id !== device.id
                                        )
                                  );
                                }}
                              />
                            </td>
                            <td>
                              <button
                                type="button"
                                className="d-device-name"
                                onClick={() =>
                                  setSelectedId(device.id)
                                }
                              >
                                {device.name}
                              </button>
                            </td>
                            <td>{device.employee}</td>
                            <td>
                              <span className="d-os">
                                <OperatingSystem
                                  platform={device.platform}
                                />
                                {device.os}
                              </span>
                            </td>
                            <td>{device.version}</td>
                            <td>
                              <StatusText
                                status={device.status}
                              />
                            </td>
                            <td className="d-muted">
                              {elapsed(device.lastSeen)}
                            </td>
                            <td>
                              <div className="d-icons">
                                <Activity
                                  size={17}
                                  color={
                                    device.activity === false
                                      ? "#a5adba"
                                      : "#172440"
                                  }
                                />
                                <Camera
                                  size={17}
                                  color={
                                    device.screenshots ===
                                    false
                                      ? "#a5adba"
                                      : "#172440"
                                  }
                                />
                                <Monitor
                                  size={17}
                                  color={
                                    device.liveReady === false
                                      ? "#a5adba"
                                      : "#172440"
                                  }
                                />
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    {loading && (
                      <div className="d-empty">
                        <RefreshCw
                          size={28}
                          className="d-spin"
                        />
                        Loading device inventory...
                      </div>
                    )}

                    {!loading && !visible.length && (
                      <div className="d-empty">
                        <Laptop size={33} />
                        <strong>
                          {devices.length
                            ? "No devices match your filters"
                            : "No devices registered"}
                        </strong>
                        <span>
                          {devices.length
                            ? "Adjust your filters to see more devices."
                            : "Register an authorized desktop agent to begin monitoring."}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="d-table-footer">
                    <div className="d-rows">
                      Rows per page
                      <select
                        aria-label="Rows per page"
                        value={rowsPerPage}
                        onChange={(event) => {
                          setRowsPerPage(
                            Number(event.target.value)
                          );
                          setPage(1);
                        }}
                      >
                        <option value={10}>10</option>
                        <option value={20}>20</option>
                        <option value={50}>50</option>
                      </select>
                    </div>

                    <div className="d-pagination">
                      <span>
                        {filtered.length === 0
                          ? 0
                          : (safePage - 1) *
                              rowsPerPage +
                            1}
                        –
                        {Math.min(
                          safePage * rowsPerPage,
                          filtered.length
                        )}{" "}
                        of {filtered.length}
                      </span>

                      <button
                        type="button"
                        disabled={safePage === 1}
                        onClick={() =>
                          setPage(safePage - 1)
                        }
                      >
                        <ChevronLeft size={16} />
                      </button>

                      {Array.from(
                        { length: Math.min(maxPages, 5) },
                        (_, index) => index + 1
                      ).map((number) => (
                        <button
                          key={number}
                          type="button"
                          className={
                            safePage === number
                              ? "d-current"
                              : ""
                          }
                          onClick={() => setPage(number)}
                        >
                          {number}
                        </button>
                      ))}

                      <button
                        type="button"
                        disabled={safePage >= maxPages}
                        onClick={() =>
                          setPage(safePage + 1)
                        }
                      >
                        <ChevronRight size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              </section>

              <aside className="d-right">
                <section className="d-card d-selected">
                  <div className="d-card-title">
                    <h2>
                      <Monitor size={21} />
                      Selected device
                    </h2>

                    <div className="d-action-menu">
                      <button
                        type="button"
                        aria-label="Device actions"
                        disabled={!selected}
                        onClick={() =>
                          setMenuOpen((value) => !value)
                        }
                      >
                        <MoreVertical size={19} />
                      </button>

                      {menuOpen && selected && (
                        <div className="d-menu">
                          <button
                            type="button"
                            onClick={() => {
                              exportDevices([selected]);
                              setMenuOpen(false);
                            }}
                          >
                            <Download size={15} />
                            Export device
                          </button>

                          {canManage &&
                            selected.source ===
                              "desktop-agent" &&
                            selected.status !==
                              "disabled" && (
                              <button
                                type="button"
                                disabled={busy}
                                onClick={() =>
                                  void disableDevice()
                                }
                              >
                                <X size={15} />
                                Disable agent
                              </button>
                            )}
                        </div>
                      )}
                    </div>
                  </div>

                  {selected ? (
                    <>
                      <div className="d-device-summary">
                        <div className="d-big-os">
                          <OperatingSystem
                            platform={selected.platform}
                            size={31}
                          />
                        </div>
                        <div className="d-device-label">
                          <h3>{selected.name}</h3>
                          <span>{selected.os}</span>
                        </div>
                        <StatusText status={selected.status} />
                      </div>

                      <dl className="d-facts">
                        <div>
                          <dt>Assigned employee</dt>
                          <dd>{selected.employee}</dd>
                        </div>
                        <div>
                          <dt>Agent version</dt>
                          <dd>{selected.version}</dd>
                        </div>
                        <div>
                          <dt>Last heartbeat</dt>
                          <dd>
                            {elapsed(selected.lastSeen)}
                          </dd>
                        </div>
                        <div>
                          <dt>Connection</dt>
                          <dd>
                            <StatusText
                              status={selected.status}
                            />
                          </dd>
                        </div>
                      </dl>

                      <div className="d-capabilities">
                        <h3>Capabilities</h3>

                        <CapabilityRow
                          icon={<Activity size={19} />}
                          title="Activity"
                          value={selected.activity}
                        />
                        <CapabilityRow
                          icon={<Camera size={19} />}
                          title="Screenshots"
                          value={selected.screenshots}
                        />
                        <CapabilityRow
                          icon={<Monitor size={19} />}
                          title="Live screen"
                          value={selected.liveReady}
                        />

                        {selected.setupReasons.length > 0 && (
                          <div className="d-setup-reasons">
                            <Info size={15} />
                            {selected.setupReasons.join("; ")}
                          </div>
                        )}
                      </div>

                      <div className="d-detail-actions">
                        <Link
                          href="/monitoring/activity"
                          className="d-btn d-btn-white"
                        >
                          <ExternalLink size={16} />
                          View activity
                        </Link>
                        <button
                          type="button"
                          className="d-btn d-btn-dark"
                          disabled={!canManage}
                          onClick={() => setSetupOpen(true)}
                        >
                          <Settings size={17} />
                          Agent setup
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="d-empty d-side-empty">
                      <Monitor size={30} />
                      Select a device to view details.
                    </div>
                  )}
                </section>

                <section className="d-card d-device-setup">
                  <div className="d-card-title">
                    <h2>
                      <Settings size={20} />
                      Device setup
                    </h2>
                  </div>

                  <button
                    type="button"
                    className="d-setup-action"
                    disabled={!canManage}
                    onClick={() => setSetupOpen(true)}
                  >
                    <Download size={22} />
                    <span>
                      <strong>Download agent</strong>
                      <small>
                        Install on authorized Windows,
                        macOS or Linux devices
                      </small>
                    </span>
                    <ChevronRight size={19} />
                  </button>

                  <button
                    type="button"
                    className="d-setup-action"
                    disabled={!canManage}
                    onClick={() => setSetupOpen(true)}
                  >
                    <ClipboardCopy size={22} />
                    <span>
                      <strong>Copy enrollment details</strong>
                      <small>
                        Use your workspace's authorized
                        desktop-agent registration
                      </small>
                    </span>
                    <ChevronRight size={19} />
                  </button>
                </section>
              </aside>
            </div>
          </>
        )}

        {setupOpen && (
          <div
            className="d-modal-overlay"
            onMouseDown={(event) => {
              if (event.currentTarget === event.target) {
                setSetupOpen(false);
              }
            }}
          >
            <section
              role="dialog"
              aria-modal="true"
              aria-labelledby="d-setup-title"
              className="d-modal"
            >
              <header>
                <div>
                  <h2 id="d-setup-title">
                    Desktop agent setup
                  </h2>
                  <p>
                    Register an authorized employee device.
                  </p>
                </div>
                <button
                  type="button"
                  aria-label="Close"
                  onClick={() => setSetupOpen(false)}
                >
                  <X size={20} />
                </button>
              </header>

              <div className="d-modal-body">
                <div className="d-modal-note">
                  <ShieldCheck size={21} />
                  Desktop monitoring requires an installed
                  agent, a signed-in device user, and
                  acknowledged monitoring consent.
                </div>

                <h3>Workspace ID</h3>
                <div className="d-copy-line">
                  <code>{workspaceId || "—"}</code>
                  <button
                    type="button"
                    onClick={() =>
                      void copyWorkspaceId()
                    }
                  >
                    <ClipboardCopy size={16} />
                    Copy
                  </button>
                </div>

                <p>
                  Your backend provides:
                  <code>
                    {" "}
                    POST /workspaces/
                    {"{workspace_id}"}
                    /desktop-agent/register
                  </code>
                  . Registration requires the installation
                  ID, platform, agent version, device name,
                  and acknowledged consent.
                </p>

                <p>
                  The public API does not expose an
                  installer download URL or enrollment
                  invitation link. Use your trusted agent
                  installer and its authenticated
                  registration workflow rather than
                  exposing registration credentials through
                  this dashboard.
                </p>

                {setupMessage && (
                  <div className="d-success">
                    <Check size={16} />
                    {setupMessage}
                  </div>
                )}

                <button
                  type="button"
                  className="d-btn d-btn-dark d-full"
                  onClick={() => {
                    setSetupOpen(false);
                    void fetchData(true);
                  }}
                >
                  <RefreshCw size={16} />
                  Refresh registered devices
                </button>
              </div>
            </section>
          </div>
        )}

        <style jsx global>{`
          .d-page {
            --d-ink: #101c3b;
            --d-muted: #6c7b95;
            --d-line: #e8e8e8;
            --d-green: #26bf78;
            --d-yellow: #ffb81e;
            --d-red: #ff4247;
            color: var(--d-ink);
            background: #fbfaf8;
            padding: 22px 20px 35px;
            min-height: 100%;
            font-size: 12px;
          }
          .d-page * { box-sizing: border-box; }
          .d-page button { cursor: pointer; }
          .d-page button:disabled {
            opacity: .45;
            cursor: not-allowed;
          }
          .d-page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            margin-bottom: 19px;
          }
          .d-page-header h1 {
            margin: 0;
            font-size: 29px;
            font-weight: 750;
            line-height: 1.2;
            letter-spacing: -.8px;
          }
          .d-page-header p {
            color: var(--d-muted);
            margin: 4px 0 0;
            font-size: 14px;
          }
          .d-header-buttons {
            display: flex;
            gap: 11px;
            align-items: center;
          }
          .d-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            min-height: 38px;
            border-radius: 7px;
            padding: 0 14px;
            white-space: nowrap;
            font: inherit;
            font-weight: 650;
            text-decoration: none;
          }
          .d-btn-white {
            background: #fff;
            border: 1px solid #e0e3e9;
            color: var(--d-ink);
          }
          .d-btn-dark {
            background: linear-gradient(#25313e, #111b26);
            border: 1px solid #14202e;
            color: white;
          }
          .d-metrics {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            border: 1px solid #f0e4d2;
            border-radius: 12px;
            background: linear-gradient(
              100deg,
              #fffbf2,
              #fffdfb 52%,
              #fffbf1
            );
            margin-bottom: 18px;
            padding: 14px 10px;
            min-height: 94px;
          }
          .d-metric {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 14px;
            border-right: 1px solid #ece3d8;
            min-width: 0;
            padding: 0 11px;
          }
          .d-metric:last-child { border-right: 0; }
          .d-metric-icon {
            flex-shrink: 0;
            width: 54px;
            height: 54px;
            background: #fff1d6;
            border-radius: 50%;
            display: grid;
            place-items: center;
          }
          .d-metric-copy {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }
          .d-metric-copy strong {
            font-size: 25px;
            line-height: 1;
            letter-spacing: -.6px;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .d-metric-copy label {
            font-size: 13px;
            font-weight: 700;
          }
          .d-metric-copy small {
            color: var(--d-muted);
            font-size: 12px;
          }
          .d-metric-color {
            width: 10px;
            height: 10px;
            border-radius: 50%;
          }
          .d-metric-color.green { background: var(--d-green); }
          .d-metric-color.yellow { background: var(--d-yellow); }
          .d-metric-color.red { background: var(--d-red); }
          .d-layout {
            display: grid;
            grid-template-columns: minmax(0, 2.11fr) minmax(320px, 1fr);
            align-items: start;
            gap: 16px;
          }
          .d-left, .d-right { min-width: 0; }
          .d-filters {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 11px;
            margin-bottom: 16px;
          }
          .d-search {
            height: 41px;
            border: 1px solid #e2e6eb;
            border-radius: 8px;
            background: #fff;
            display: flex;
            align-items: center;
            gap: 9px;
            color: #7184a4;
            padding: 0 13px;
            flex: 1 1 230px;
            min-width: 190px;
          }
          .d-search input {
            background: transparent;
            border: none;
            outline: none;
            color: var(--d-ink);
            min-width: 0;
            width: 100%;
            font: inherit;
          }
          .d-select {
            position: relative;
            height: 41px;
            min-width: 135px;
            border: 1px solid #e2e6eb;
            border-radius: 8px;
            background: white;
          }
          .d-select select {
            appearance: none;
            background: transparent;
            border: 0;
            outline: 0;
            width: 100%;
            height: 100%;
            padding: 0 31px 0 13px;
            font: inherit;
            color: var(--d-ink);
            cursor: pointer;
          }
          .d-select svg {
            pointer-events: none;
            position: absolute;
            right: 10px;
            top: 13px;
          }
          .d-clear {
            color: #516386;
            background: transparent;
            border: 0;
            text-decoration: underline;
            font: inherit;
            padding: 7px;
          }
          .d-card {
            background: #fffefa;
            border: 1px solid var(--d-line);
            border-radius: 11px;
            overflow: hidden;
          }
          .d-card-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            min-height: 54px;
            padding: 12px 15px;
          }
          .d-card-title h2 {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 17px;
            font-weight: 750;
            letter-spacing: -.3px;
            margin: 0;
          }
          .d-heading-actions {
            display: flex;
            align-items: center;
            gap: 9px;
            color: var(--d-muted);
          }
          .d-heading-actions button,
          .d-action-menu > button {
            background: transparent;
            border: 0;
            color: #324462;
            padding: 4px;
          }
          .d-table-wrap {
            overflow-x: auto;
            min-height: 370px;
          }
          .d-table {
            width: 100%;
            min-width: 825px;
            border-collapse: collapse;
            text-align: left;
          }
          .d-table thead th {
            background: #f6f6f6;
            color: #15213e;
            padding: 11px 7px;
            font-weight: 700;
            font-size: 10px;
            white-space: nowrap;
          }
          .d-table thead th button {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: transparent;
            border: 0;
            font: inherit;
            color: inherit;
            padding: 0;
          }
          .d-sort {
            font-size: 12px;
            color: #7583a0;
          }
          .d-table td {
            border-top: 1px solid #e9ebee;
            padding: 10px 7px;
            height: 42px;
            white-space: nowrap;
            font-size: 11px;
          }
          .d-table .d-check-cell {
            width: 35px;
            padding-left: 13px;
          }
          .d-table input[type="checkbox"] {
            accent-color: #ffb400;
            cursor: pointer;
            width: 15px;
            height: 15px;
          }
          .d-table tbody tr:hover { background: #fff9ef; }
          .d-table tbody tr.d-selected-row {
            background: #fff6e5;
            outline: 1px solid #ffd389;
            outline-offset: -1px;
          }
          .d-device-name {
            background: transparent;
            border: 0;
            font: inherit;
            font-weight: 700;
            color: var(--d-ink);
          }
          .d-os {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #526580;
          }
          .d-os-windows {
            display: inline-grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 1px;
            transform: perspective(40px) rotateY(-8deg);
          }
          .d-os-windows i { background: #08a5ed; }
          .d-status {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            white-space: nowrap;
          }
          .d-dot {
            width: 10px;
            height: 10px;
            flex: 0 0 10px;
            border-radius: 50%;
            background: #99a5b4;
            display: inline-block;
          }
          .d-dot-online { background: #25bd75; }
          .d-dot-offline { background: #f24748; }
          .d-dot-pending { background: #fbb724; }
          .d-dot-disabled { background: #97a1af; }
          .d-muted { color: var(--d-muted); }
          .d-icons {
            display: flex;
            align-items: center;
            gap: 12px;
          }
          .d-table-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            padding: 13px 15px;
            flex-wrap: wrap;
            min-height: 68px;
            color: #687895;
          }
          .d-rows, .d-pagination {
            display: flex;
            align-items: center;
            gap: 7px;
          }
          .d-rows select {
            margin-left: 9px;
            height: 35px;
            border: 1px solid #e5e7eb;
            border-radius: 7px;
            padding: 0 12px;
            background: #fff;
            color: #15223d;
          }
          .d-pagination > span { margin-right: 8px; }
          .d-pagination button {
            border: 1px solid #e8eaf0;
            background: #fff;
            border-radius: 7px;
            min-width: 30px;
            height: 32px;
            color: var(--d-ink);
            display: grid;
            place-items: center;
          }
          .d-pagination button.d-current {
            background: #ffecbf;
            border-color: #ffdf91;
            font-weight: 800;
          }
          .d-right {
            display: flex;
            flex-direction: column;
            gap: 15px;
          }
          .d-action-menu { position: relative; }
          .d-menu {
            position: absolute;
            top: 30px;
            right: 0;
            z-index: 20;
            background: white;
            border: 1px solid #dfe3e9;
            border-radius: 8px;
            padding: 5px;
            width: 180px;
            box-shadow: 0 12px 30px #101a2920;
          }
          .d-menu button {
            border: 0;
            border-radius: 5px;
            padding: 10px;
            background: transparent;
            width: 100%;
            display: flex;
            align-items: center;
            gap: 8px;
            text-align: left;
            font: inherit;
            color: var(--d-ink);
          }
          .d-menu button:hover { background: #fff4dc; }
          .d-device-summary {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 0 16px 17px;
          }
          .d-big-os {
            width: 54px;
            height: 54px;
            border: 1px solid #e6e7ea;
            display: grid;
            place-items: center;
            border-radius: 9px;
            background: white;
            flex-shrink: 0;
          }
          .d-device-label {
            flex: 1;
            min-width: 0;
          }
          .d-device-label h3 {
            margin: 0 0 5px;
            font-size: 16px;
            overflow-wrap: anywhere;
          }
          .d-device-label span { color: var(--d-muted); }
          .d-device-summary > .d-status {
            background: #e0f8e7;
            color: #17864f;
            padding: 6px 12px;
            border-radius: 20px;
          }
          .d-facts {
            margin: 0 16px;
            padding: 12px 0 16px;
            border-bottom: 1px solid #e6e8ec;
          }
          .d-facts > div {
            display: grid;
            grid-template-columns: 1.05fr 1fr;
            gap: 8px;
            padding: 8px 0;
          }
          .d-facts dt { color: var(--d-muted); }
          .d-facts dd {
            margin: 0;
            font-weight: 650;
          }
          .d-capabilities {
            margin: 0 16px;
            padding: 14px 0;
          }
          .d-capabilities h3 {
            margin: 0 0 9px;
            font-size: 13px;
          }
          .d-cap-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 0;
            gap: 10px;
          }
          .d-cap-row > span {
            display: inline-flex;
            align-items: center;
            gap: 13px;
          }
          .d-cap-row b {
            font-weight: 500;
            padding: 5px 13px;
            border-radius: 30px;
            font-size: 11px;
          }
          .d-cap-yes {
            background: #def7e6;
            color: #13804c;
          }
          .d-cap-no {
            background: #ffeded;
            color: #b23434;
          }
          .d-cap-unknown {
            background: #eef0f4;
            color: #6c7585;
          }
          .d-setup-reasons {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            padding: 10px;
            background: #fff5e0;
            color: #966900;
            line-height: 1.5;
            border-radius: 7px;
            margin-top: 10px;
          }
          .d-detail-actions {
            padding: 2px 15px 16px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 9px;
          }
          .d-detail-actions .d-btn {
            padding: 0 7px;
          }
          .d-device-setup .d-card-title {
            padding-bottom: 10px;
          }
          .d-setup-action {
            background: white;
            display: flex;
            width: calc(100% - 26px);
            margin: 0 13px 11px;
            padding: 13px;
            border: 1px solid #e4e7ed;
            border-radius: 9px;
            align-items: center;
            text-align: left;
            gap: 13px;
            color: var(--d-ink);
          }
          .d-setup-action > span {
            display: flex;
            flex-direction: column;
            gap: 5px;
            flex: 1;
          }
          .d-setup-action strong { font-size: 12px; }
          .d-setup-action small {
            font-size: 11px;
            color: var(--d-muted);
            line-height: 1.4;
          }
          .d-empty {
            min-height: 285px;
            padding: 25px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            color: #8190a8;
            text-align: center;
          }
          .d-empty strong { color: var(--d-ink); }
          .d-side-empty { min-height: 220px; }
          .d-notice {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 11px 14px;
            border-radius: 8px;
            margin-bottom: 15px;
          }
          .d-notice span { flex: 1; }
          .d-notice button {
            border: 1px solid currentColor;
            padding: 5px 10px;
            border-radius: 5px;
            background: white;
          }
          .d-notice-error {
            background: #fff0f0;
            border: 1px solid #f5baba;
            color: #b52c2c;
          }
          .d-notice-warning {
            background: #fff8e9;
            border: 1px solid #f3dba2;
            color: #986d0b;
          }
          .d-modal-overlay {
            position: fixed;
            inset: 0;
            z-index: 250;
            display: grid;
            place-items: center;
            background: #0b172895;
            padding: 18px;
          }
          .d-modal {
            width: min(540px, 100%);
            max-height: 90vh;
            overflow-y: auto;
            border-radius: 13px;
            border: 1px solid #e4e7ef;
            background: #fffefa;
            box-shadow: 0 15px 60px #08101b44;
          }
          .d-modal header {
            padding: 19px 20px;
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 10px;
            border-bottom: 1px solid #e8eaf0;
          }
          .d-modal header h2 {
            font-size: 20px;
            margin: 0;
          }
          .d-modal header p {
            color: #6b7c95;
            margin: 6px 0 0;
          }
          .d-modal header button {
            border: 0;
            background: transparent;
          }
          .d-modal-body { padding: 20px; }
          .d-modal-body h3 { font-size: 14px; }
          .d-modal-body p {
            color: #596b88;
            line-height: 1.7;
            overflow-wrap: anywhere;
          }
          .d-modal-body code { overflow-wrap: anywhere; }
          .d-modal-note {
            display: flex;
            gap: 11px;
            padding: 13px;
            border-radius: 8px;
            border: 1px solid #dceaf8;
            background: #f0f7ff;
            line-height: 1.6;
          }
          .d-copy-line {
            display: flex;
            align-items: center;
            gap: 8px;
            border: 1px solid #e1e5eb;
            border-radius: 7px;
            padding: 10px;
            background: #fff;
          }
          .d-copy-line code { flex: 1; }
          .d-copy-line button {
            display: flex;
            align-items: center;
            gap: 6px;
            background: #fff6e4;
            border: 1px solid #f2dbaa;
            border-radius: 5px;
            padding: 8px;
          }
          .d-success {
            display: flex;
            gap: 8px;
            color: #19834e;
            padding: 9px 0;
          }
          .d-full {
            width: 100%;
            margin-top: 17px;
          }
          .d-spin { animation: d-spin 1s linear infinite; }
          @keyframes d-spin {
            to { transform: rotate(360deg); }
          }
          @media (max-width: 1240px) {
            .d-layout {
              grid-template-columns: 1fr;
            }
            .d-right {
              display: grid;
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
          }
          @media (max-width: 850px) {
            .d-metrics {
              grid-template-columns: repeat(2, minmax(0, 1fr));
              row-gap: 15px;
            }
            .d-metric:nth-child(2) { border-right: 0; }
            .d-page-header {
              align-items: flex-start;
              flex-direction: column;
            }
            .d-right { grid-template-columns: 1fr; }
          }
          @media (max-width: 550px) {
            .d-page { padding: 15px 12px 25px; }
            .d-page-header h1 { font-size: 24px; }
            .d-metric-icon { width: 40px; height: 40px; }
            .d-metric { padding: 0 6px; gap: 9px; }
            .d-metric-copy strong { font-size: 21px; }
            .d-detail-actions { grid-template-columns: 1fr; }
          }
        `}</style>
      </main>
    </WorkspaceRequired>
  );
}

function Metric({
  label,
  value,
  detail,
  color,
}: {
  label: string;
  value: number | null;
  detail: string;
  color?: "green" | "yellow" | "red";
}) {
  return (
    <div className="d-metric">
      <div className="d-metric-icon">
        <Laptop size={29} />
      </div>
      <div className="d-metric-copy">
        <strong>
          {color && (
            <i className={`d-metric-color ${color}`} />
          )}
          {value ?? "—"}
        </strong>
        <label>{label}</label>
        <small>{detail}</small>
      </div>
    </div>
  );
}
