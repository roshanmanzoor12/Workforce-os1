
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
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Clock3,
  Download,
  FileBarChart2,
  FileSpreadsheet,
  FileText,
  Info,
  Laptop2,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  UsersRound,
} from "lucide-react";

import { api } from "@/lib/api/client";
import { useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { hasAnyPermission } from "@/lib/workspace/access";

type ReportScope = "self" | "team" | "workspace";

type ReportDefinition = {
  key: string;
  label: string;
  description: string;
  supported_scopes: ReportScope[];
  supported_formats: string[];
  supports_time_range: boolean;
  supports_employee_filter: boolean;
  supports_team_filter: boolean;
  supports_department_filter: boolean;
  supports_status_filter: boolean;
};

type ReportCatalog = {
  items: ReportDefinition[];
};

type ReportCapabilities = {
  can_read_self: boolean;
  can_read_team: boolean;
  can_read_workspace: boolean;
  can_export: boolean;
  effective_scopes: ReportScope[];
  available_reports: string[];
  export_formats: string[];
  async_exports_supported: boolean;
};

type ReportRequest = {
  report: string;
  scope: ReportScope;
  start_at?: string;
  end_at?: string;
  employee_id?: string;
  team_id?: string;
  department_id?: string;
  status?: string;
  limit: number;
};

type ReportResult = {
  workspace_id: string;
  report: string;
  scope: ReportScope;
  generated_at: string;
  parameters: Record<string, unknown>;
  data: Record<string, unknown>;
};

type PreviewRow = {
  label: string;
  value: unknown;
};

const PAGE_SIZE = 8;

const iconFor = (key: string) => {
  if (key === "monitoring_summary") {
    return <Activity size={22} />;
  }
  if (key === "device_health") {
    return <Laptop2 size={22} />;
  }
  if (key === "productivity") {
    return <BarChart3 size={22} />;
  }
  if (key === "attendance") {
    return <Clock3 size={22} />;
  }
  if (key === "payroll") {
    return <FileSpreadsheet size={22} />;
  }
  if (key === "audit") {
    return <ShieldCheck size={22} />;
  }
  return <FileText size={22} />;
};

function localDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function beginningOfMonth(): string {
  const now = new Date();
  return localDate(
    new Date(now.getFullYear(), now.getMonth(), 1)
  );
}

function isoStart(day: string): string {
  return new Date(`${day}T00:00:00`).toISOString();
}

function isoEndExclusive(day: string): string {
  const end = new Date(`${day}T00:00:00`);
  end.setDate(end.getDate() + 1);
  return end.toISOString();
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function displayValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "number") {
    return value.toLocaleString();
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value);
}

function titleCase(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function isRecord(
  value: unknown
): value is Record<string, unknown> {
  return (
    !!value &&
    typeof value === "object" &&
    !Array.isArray(value)
  );
}

function extractMetrics(
  data: Record<string, unknown>
): PreviewRow[] {
  const summary = isRecord(data.summary)
    ? data.summary
    : data;

  return Object.entries(summary)
    .filter(([, value]) =>
      typeof value === "number" ||
      typeof value === "boolean" ||
      typeof value === "string"
    )
    .slice(0, 8)
    .map(([label, value]) => ({
      label: titleCase(label),
      value,
    }));
}

function extractRows(
  data: Record<string, unknown>
): Record<string, unknown>[] {
  for (const key of [
    "rows",
    "items",
    "records",
    "results",
    "employees",
    "devices",
    "events",
    "attendance",
  ]) {
    const candidate = data[key];

    if (
      Array.isArray(candidate) &&
      candidate.every(isRecord)
    ) {
      return candidate;
    }
  }

  // The Reports API may return aggregates rather
  // than a tabular list. Do not fabricate rows.
  return [];
}

function safeFilename(value: string): string {
  return value.replace(/[^a-z0-9_-]/gi, "-");
}

function downloadBlob(
  blob: Blob,
  name: string
): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = url;
  anchor.download = name;

  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  window.setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 1000);
}

export default function MonitoringReportsPage() {
  const {
    workspaceId,
    permissions,
    navigationView,
  } = useWorkspace();

  const hasReportPermission = hasAnyPermission(
    permissions,
    [
      "reports.all.read",
      "reports.team.read",
      "reports.self.read",
      "reports.export",
    ],
    navigationView
  );

  const [catalog, setCatalog] = useState<
    ReportDefinition[]
  >([]);
  const [capabilities, setCapabilities] =
    useState<ReportCapabilities | null>(null);

  const [selectedKey, setSelectedKey] =
    useState("monitoring_summary");
  const [scope, setScope] =
    useState<ReportScope>("workspace");

  const [startDate, setStartDate] =
    useState(beginningOfMonth);
  const [endDate, setEndDate] =
    useState(() => localDate(new Date()));

  const [employeeId, setEmployeeId] = useState("");
  const [teamId, setTeamId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [status, setStatus] = useState("");
  const [recordLimit, setRecordLimit] = useState(500);

  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");
  const [reportError, setReportError] = useState("");
  const [result, setResult] =
    useState<ReportResult | null>(null);
  const [success, setSuccess] = useState("");

  const base = workspaceId
    ? `/workspaces/${workspaceId}/reports`
    : "";

  const loadConfiguration = useCallback(async () => {
    if (!workspaceId || !hasReportPermission) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const [catalogResponse, capabilityResponse] =
        await Promise.all([
          api.get<ReportCatalog>(
            `/workspaces/${workspaceId}/reports/catalog`
          ),
          api.get<ReportCapabilities>(
            `/workspaces/${workspaceId}/reports/capabilities`
          ),
        ]);

      setCatalog(catalogResponse.items || []);
      setCapabilities(capabilityResponse);

      const preferred =
        catalogResponse.items.find(
          (item) => item.key === "monitoring_summary"
        ) || catalogResponse.items[0];

      if (preferred) {
        setSelectedKey(preferred.key);

        const firstScope =
          preferred.supported_scopes.includes("workspace")
            ? "workspace"
            : preferred.supported_scopes.includes("team")
              ? "team"
              : preferred.supported_scopes[0] || "self";

        setScope(firstScope);
      }
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to load report catalog."
      );
    } finally {
      setLoading(false);
    }
  }, [workspaceId, hasReportPermission]);

  useEffect(() => {
    void loadConfiguration();
  }, [loadConfiguration]);

  const selected = useMemo(
    () =>
      catalog.find(
        (item) => item.key === selectedKey
      ) || null,
    [catalog, selectedKey]
  );

  const selectedScopes = selected?.supported_scopes || [];

  const validScope = selectedScopes.includes(scope)
    ? scope
    : selectedScopes[0] || "self";

  const canExport =
    capabilities?.can_export === true &&
    selected?.supported_formats.includes("csv") === true;

  const dateValid =
    !selected?.supports_time_range ||
    (Boolean(startDate) &&
      Boolean(endDate) &&
      startDate <= endDate);

  const filteredCatalog = useMemo(() => {
    const needle = search.trim().toLowerCase();

    return catalog.filter((item) =>
      `${item.label} ${item.description} ${item.key}`
        .toLowerCase()
        .includes(needle)
    );
  }, [catalog, search]);

  const reportMetrics = useMemo(
    () =>
      result ? extractMetrics(result.data) : [],
    [result]
  );

  const resultRows = useMemo(
    () =>
      result ? extractRows(result.data) : [],
    [result]
  );

  const tableColumns = useMemo(() => {
    const columns = new Set<string>();

    for (const item of resultRows.slice(0, 30)) {
      for (const key of Object.keys(item)) {
        columns.add(key);
        if (columns.size >= 12) break;
      }
    }

    return [...columns].slice(0, 12);
  }, [resultRows]);

  const totalPages = Math.max(
    1,
    Math.ceil(resultRows.length / PAGE_SIZE)
  );

  const currentPage = Math.min(page, totalPages);
  const visibleRows = resultRows.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const createRequest = (): ReportRequest | null => {
    if (!selected || !dateValid) return null;

    const request: ReportRequest = {
      report: selected.key,
      scope: validScope,
      limit: recordLimit,
    };

    if (selected.supports_time_range) {
      request.start_at = isoStart(startDate);
      request.end_at = isoEndExclusive(endDate);
    }

    if (
      selected.supports_employee_filter &&
      employeeId.trim()
    ) {
      request.employee_id = employeeId.trim();
    }

    if (
      selected.supports_team_filter &&
      teamId.trim()
    ) {
      request.team_id = teamId.trim();
    }

    if (
      selected.supports_department_filter &&
      departmentId.trim()
    ) {
      request.department_id = departmentId.trim();
    }

    if (
      selected.supports_status_filter &&
      status.trim()
    ) {
      request.status = status.trim();
    }

    return request;
  };

  const runReport = async () => {
    if (!workspaceId || running) return;

    const request = createRequest();
    if (!request) return;

    setRunning(true);
    setReportError("");
    setSuccess("");
    setResult(null);
    setPage(1);

    try {
      const response = await api.post<ReportResult>(
        `${base}/run`,
        request
      );

      setResult(response);
      setSuccess(
        "Report generated from the workspace backend."
      );
    } catch (cause) {
      setReportError(
        cause instanceof Error
          ? cause.message
          : "Unable to generate report."
      );
    } finally {
      setRunning(false);
    }
  };

  const exportReport = async () => {
    if (!workspaceId || !canExport || exporting) {
      return;
    }

    const request = createRequest();
    if (!request) return;

    setExporting(true);
    setReportError("");

    try {
      const file = await api.post<Blob>(
        `${base}/export`,
        request,
        { responseType: "blob" }
      );

      downloadBlob(
        file,
        `workforce-${safeFilename(
          request.report
        )}-${endDate}.csv`
      );
    } catch (cause) {
      setReportError(
        cause instanceof Error
          ? cause.message
          : "Unable to export CSV."
      );
    } finally {
      setExporting(false);
    }
  };

  const selectReport = (report: ReportDefinition) => {
    setSelectedKey(report.key);
    setScope(
      report.supported_scopes.includes("workspace")
        ? "workspace"
        : report.supported_scopes[0] || "self"
    );
    setResult(null);
    setReportError("");
    setSuccess("");
    setPage(1);
    setEmployeeId("");
    setTeamId("");
    setDepartmentId("");
    setStatus("");
  };

  const clearFilters = () => {
    setStartDate(beginningOfMonth());
    setEndDate(localDate(new Date()));
    setEmployeeId("");
    setTeamId("");
    setDepartmentId("");
    setStatus("");
    setRecordLimit(500);
    setResult(null);
    setReportError("");
    setSuccess("");
  };

  return (
    <WorkspaceRequired>
      <main className="mr-page">
        <header className="mr-header">
          <div>
            <h1>Monitoring Reports</h1>
            <p>
              Generate and export authorized workforce,
              monitoring, and device-health reports.
            </p>
          </div>

          <div className="mr-header-actions">
            <button
              type="button"
              className="mr-btn mr-outline"
              disabled={loading}
              onClick={() =>
                void loadConfiguration()
              }
            >
              <RefreshCw
                size={16}
                className={
                  loading ? "mr-spin" : ""
                }
              />
              Refresh catalog
            </button>

            <button
              type="button"
              className="mr-btn mr-dark"
              disabled={
                !canExport ||
                !dateValid ||
                exporting
              }
              onClick={() =>
                void exportReport()
              }
            >
              {exporting ? (
                <Loader2
                  size={17}
                  className="mr-spin"
                />
              ) : (
                <Download size={17} />
              )}
              Export CSV
            </button>
          </div>
        </header>

        {!hasReportPermission ? (
          <div className="mr-error">
            <AlertTriangle size={19} />
            You do not have permission to access
            workspace reports.
          </div>
        ) : (
          <>
            {error && (
              <div className="mr-error">
                <AlertTriangle size={18} />
                <span>{error}</span>
                <button
                  type="button"
                  onClick={() =>
                    void loadConfiguration()
                  }
                >
                  Retry
                </button>
              </div>
            )}

            <section className="mr-summary">
              <Metric
                icon={<FileBarChart2 size={28} />}
                value={catalog.length}
                label="Available reports"
                detail="Authorized report types"
              />

              <Metric
                icon={<UsersRound size={28} />}
                value={
                  capabilities?.effective_scopes.length ??
                  0
                }
                label="Access scopes"
                detail="Scopes allowed by backend"
              />

              <Metric
                icon={<FileSpreadsheet size={28} />}
                value={
                  capabilities?.can_export ? 1 : 0
                }
                label="CSV export"
                detail={
                  capabilities?.can_export
                    ? "Enabled for authorized reports"
                    : "Not permitted"
                }
              />

              <Metric
                icon={<ClipboardList size={28} />}
                value={result ? 1 : 0}
                label="Current preview"
                detail={
                  result
                    ? "Report generated"
                    : "No report generated yet"
                }
              />
            </section>

            <div className="mr-layout">
              <aside className="mr-card mr-catalog">
                <div className="mr-card-header">
                  <h2>
                    <FileText size={20} />
                    Report catalog
                  </h2>
                </div>

                <div className="mr-catalog-search">
                  <Search size={17} />
                  <input
                    aria-label="Search report types"
                    placeholder="Search reports..."
                    value={search}
                    onChange={(event) =>
                      setSearch(event.target.value)
                    }
                  />
                </div>

                <div className="mr-report-list">
                  {filteredCatalog.map((report) => (
                    <button
                      key={report.key}
                      type="button"
                      className={`mr-report-option ${
                        selectedKey === report.key
                          ? "mr-report-selected"
                          : ""
                      }`}
                      onClick={() =>
                        selectReport(report)
                      }
                    >
                      <span className="mr-report-icon">
                        {iconFor(report.key)}
                      </span>

                      <span className="mr-report-copy">
                        <strong>{report.label}</strong>
                        <small>
                          {report.description}
                        </small>
                      </span>

                      <ChevronRight size={17} />
                    </button>
                  ))}

                  {!loading &&
                    filteredCatalog.length === 0 && (
                      <div className="mr-empty-small">
                        No reports available.
                      </div>
                    )}

                  {loading && (
                    <div className="mr-empty-small">
                      <Loader2
                        size={20}
                        className="mr-spin"
                      />
                      Loading catalog...
                    </div>
                  )}
                </div>
              </aside>

              <section className="mr-main">
                <div className="mr-card mr-generator">
                  <div className="mr-card-header">
                    <h2>
                      <BarChart3 size={20} />
                      Report configuration
                    </h2>
                    {selected && (
                      <span className="mr-report-type">
                        {selected.label}
                      </span>
                    )}
                  </div>

                  {selected ? (
                    <>
                      <div className="mr-selected-report">
                        <span className="mr-large-icon">
                          {iconFor(selected.key)}
                        </span>
                        <div>
                          <h3>{selected.label}</h3>
                          <p>
                            {selected.description}
                          </p>
                        </div>
                      </div>

                      <div className="mr-controls">
                        <label>
                          <span>Report scope</span>
                          <div className="mr-control-wrap">
                            <select
                              value={validScope}
                              onChange={(event) => {
                                setScope(
                                  event.target.value as ReportScope
                                );
                                setResult(null);
                              }}
                            >
                              {selectedScopes.map(
                                (item) => (
                                  <option
                                    key={item}
                                    value={item}
                                  >
                                    {titleCase(item)}
                                  </option>
                                )
                              )}
                            </select>
                            <ChevronDown size={16} />
                          </div>
                        </label>

                        {selected.supports_time_range && (
                          <>
                            <label>
                              <span>Start date</span>
                              <div className="mr-date-wrap">
                                <CalendarDays size={16} />
                                <input
                                  type="date"
                                  value={startDate}
                                  onChange={(event) => {
                                    setStartDate(
                                      event.target.value
                                    );
                                    setResult(null);
                                  }}
                                />
                              </div>
                            </label>

                            <label>
                              <span>End date</span>
                              <div className="mr-date-wrap">
                                <CalendarDays size={16} />
                                <input
                                  type="date"
                                  value={endDate}
                                  onChange={(event) => {
                                    setEndDate(
                                      event.target.value
                                    );
                                    setResult(null);
                                  }}
                                />
                              </div>
                            </label>
                          </>
                        )}

                        {selected.supports_employee_filter && (
                          <label>
                            <span>Employee ID (optional)</span>
                            <input
                              value={employeeId}
                              placeholder="Employee UUID"
                              onChange={(event) => {
                                setEmployeeId(
                                  event.target.value
                                );
                                setResult(null);
                              }}
                            />
                          </label>
                        )}

                        {selected.supports_team_filter && (
                          <label>
                            <span>Team ID (optional)</span>
                            <input
                              value={teamId}
                              placeholder="Team UUID"
                              onChange={(event) => {
                                setTeamId(
                                  event.target.value
                                );
                                setResult(null);
                              }}
                            />
                          </label>
                        )}

                        {selected.supports_department_filter && (
                          <label>
                            <span>Department ID (optional)</span>
                            <input
                              value={departmentId}
                              placeholder="Department UUID"
                              onChange={(event) => {
                                setDepartmentId(
                                  event.target.value
                                );
                                setResult(null);
                              }}
                            />
                          </label>
                        )}

                        {selected.supports_status_filter && (
                          <label>
                            <span>Status filter (optional)</span>
                            <input
                              value={status}
                              placeholder="Backend status"
                              onChange={(event) => {
                                setStatus(
                                  event.target.value
                                );
                                setResult(null);
                              }}
                            />
                          </label>
                        )}

                        <label>
                          <span>Maximum records</span>
                          <div className="mr-control-wrap">
                            <select
                              value={recordLimit}
                              onChange={(event) => {
                                setRecordLimit(
                                  Number(
                                    event.target.value
                                  )
                                );
                                setResult(null);
                              }}
                            >
                              <option value={100}>
                                100 records
                              </option>
                              <option value={500}>
                                500 records
                              </option>
                              <option value={1000}>
                                1,000 records
                              </option>
                              <option value={5000}>
                                5,000 records
                              </option>
                            </select>
                            <ChevronDown size={16} />
                          </div>
                        </label>
                      </div>

                      {!dateValid && (
                        <p className="mr-validation">
                          End date must not be earlier
                          than start date.
                        </p>
                      )}

                      <div className="mr-generator-footer">
                        <button
                          type="button"
                          className="mr-btn mr-outline"
                          onClick={clearFilters}
                        >
                          Clear filters
                        </button>

                        <button
                          type="button"
                          className="mr-btn mr-dark"
                          disabled={
                            !dateValid ||
                            running ||
                            !selectedScopes.length
                          }
                          onClick={() =>
                            void runReport()
                          }
                        >
                          {running ? (
                            <Loader2
                              size={17}
                              className="mr-spin"
                            />
                          ) : (
                            <BarChart3 size={17} />
                          )}
                          Generate report
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="mr-empty">
                      <FileText size={32} />
                      <strong>Select a report</strong>
                      <p>
                        Choose an authorized report from
                        the catalog to configure it.
                      </p>
                    </div>
                  )}
                </div>

                {reportError && (
                  <div className="mr-error">
                    <AlertTriangle size={17} />
                    {reportError}
                  </div>
                )}

                {success && (
                  <div className="mr-success">
                    <CheckCircle2 size={17} />
                    {success}
                  </div>
                )}

                <section className="mr-card mr-preview">
                  <div className="mr-card-header">
                    <h2>
                      <FileBarChart2 size={20} />
                      Report preview
                    </h2>

                    {result && (
                      <span className="mr-generated">
                        Generated{" "}
                        {formatDate(
                          result.generated_at
                        )}
                      </span>
                    )}
                  </div>

                  {!result ? (
                    <div className="mr-empty mr-preview-empty">
                      {running ? (
                        <Loader2
                          size={33}
                          className="mr-spin"
                        />
                      ) : (
                        <FileSpreadsheet size={35} />
                      )}
                      <strong>
                        {running
                          ? "Generating report..."
                          : "No report generated"}
                      </strong>
                      <p>
                        Configure a report above and select
                        Generate report to load real
                        workspace data.
                      </p>
                    </div>
                  ) : (
                    <>
                      <div className="mr-preview-info">
                        <div>
                          <span>Report type</span>
                          <strong>
                            {titleCase(result.report)}
                          </strong>
                        </div>
                        <div>
                          <span>Access scope</span>
                          <strong>
                            {titleCase(result.scope)}
                          </strong>
                        </div>
                        <div>
                          <span>Generated</span>
                          <strong>
                            {formatDate(
                              result.generated_at
                            )}
                          </strong>
                        </div>
                      </div>

                      {reportMetrics.length > 0 && (
                        <div className="mr-preview-metrics">
                          {reportMetrics.map(
                            (item, index) => (
                              <div key={`${item.label}-${index}`}>
                                <small>{item.label}</small>
                                <strong>
                                  {displayValue(
                                    item.value
                                  )}
                                </strong>
                              </div>
                            )
                          )}
                        </div>
                      )}

                      {resultRows.length > 0 ? (
                        <>
                          <div className="mr-table-header">
                            <h3>
                              <ClipboardList size={18} />
                              Report records
                            </h3>
                            <span>
                              {resultRows.length} rows
                            </span>
                          </div>

                          <div className="mr-table-scroll">
                            <table>
                              <thead>
                                <tr>
                                  {tableColumns.map(
                                    (column) => (
                                      <th key={column}>
                                        {titleCase(
                                          column
                                        )}
                                      </th>
                                    )
                                  )}
                                </tr>
                              </thead>
                              <tbody>
                                {visibleRows.map(
                                  (row, index) => (
                                    <tr
                                      key={
                                        (currentPage - 1) *
                                          PAGE_SIZE +
                                        index
                                      }
                                    >
                                      {tableColumns.map(
                                        (column) => (
                                          <td
                                            key={column}
                                          >
                                            {displayValue(
                                              row[column]
                                            )}
                                          </td>
                                        )
                                      )}
                                    </tr>
                                  )
                                )}
                              </tbody>
                            </table>
                          </div>

                          <footer className="mr-pagination">
                            <span>
                              {(
                                currentPage - 1
                              ) * PAGE_SIZE + 1}
                              –
                              {Math.min(
                                currentPage * PAGE_SIZE,
                                resultRows.length
                              )}{" "}
                              of {resultRows.length}
                            </span>

                            <div>
                              <button
                                type="button"
                                disabled={
                                  currentPage <= 1
                                }
                                onClick={() =>
                                  setPage((value) =>
                                    Math.max(
                                      1,
                                      value - 1
                                    )
                                  )
                                }
                              >
                                <ChevronLeft
                                  size={16}
                                />
                              </button>

                              <span>
                                {currentPage} /{" "}
                                {totalPages}
                              </span>

                              <button
                                type="button"
                                disabled={
                                  currentPage >=
                                  totalPages
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
                                <ChevronRight
                                  size={16}
                                />
                              </button>
                            </div>
                          </footer>
                        </>
                      ) : (
                        <div className="mr-aggregate">
                          <Info size={19} />
                          <div>
                            <strong>
                              Aggregate report
                            </strong>
                            <p>
                              The backend returned report
                              data without a recognized
                              row collection. The complete
                              response is shown below.
                            </p>
                          </div>
                        </div>
                      )}

                      <details className="mr-json">
                        <summary>
                          View complete report response
                        </summary>
                        <pre>
                          {JSON.stringify(
                            result.data,
                            null,
                            2
                          )}
                        </pre>
                      </details>
                    </>
                  )}
                </section>
              </section>
            </div>

            <footer className="mr-bottom-note">
              <Info size={16} />
              Report types, accessible scopes, and export
              permissions are determined by the backend.
              CSV exports are generated by the server,
              not reconstructed from the preview.
            </footer>
          </>
        )}

        <style jsx global>{`
          .mr-page {
            --mr-ink: #101c3b;
            --mr-muted: #70809a;
            --mr-line: #e6e8ec;
            background: #fbfaf8;
            color: var(--mr-ink);
            min-height: 100%;
            padding: 22px 21px 35px;
            font-size: 12px;
          }

          .mr-page * {
            box-sizing: border-box;
          }

          .mr-page button,
          .mr-page input,
          .mr-page select {
            font: inherit;
          }

          .mr-page button {
            cursor: pointer;
          }

          .mr-page button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
          }

          .mr-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 18px;
            margin-bottom: 20px;
          }

          .mr-header h1 {
            margin: 0;
            font-size: 29px;
            line-height: 1.2;
            font-weight: 750;
            letter-spacing: -0.8px;
          }

          .mr-header p {
            color: var(--mr-muted);
            font-size: 14px;
            margin: 5px 0 0;
          }

          .mr-header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
          }

          .mr-btn {
            min-height: 38px;
            padding: 0 15px;
            border-radius: 7px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 9px;
            font-weight: 650 !important;
            white-space: nowrap;
          }

          .mr-outline {
            background: white;
            border: 1px solid #dfe3e9;
            color: var(--mr-ink);
          }

          .mr-dark {
            background: #192530;
            border: 1px solid #192530;
            color: white;
          }

          .mr-summary {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 13px;
            margin-bottom: 17px;
          }

          .mr-metric {
            display: flex;
            align-items: center;
            gap: 14px;
            min-height: 100px;
            background: linear-gradient(
              105deg,
              #fff9ef,
              #fffefa
            );
            border: 1px solid #f0e5d2;
            border-radius: 11px;
            padding: 17px;
          }

          .mr-metric-icon {
            height: 53px;
            width: 53px;
            display: grid;
            place-items: center;
            background: #fff0d1;
            border-radius: 50%;
            flex-shrink: 0;
          }

          .mr-metric > div {
            display: flex;
            flex-direction: column;
            gap: 5px;
            min-width: 0;
          }

          .mr-metric strong {
            font-size: 26px;
            line-height: 1;
            letter-spacing: -0.5px;
          }

          .mr-metric div span {
            font-weight: 700;
            font-size: 13px;
          }

          .mr-metric small {
            color: var(--mr-muted);
            font-size: 11px;
            line-height: 1.35;
          }

          .mr-layout {
            display: grid;
            grid-template-columns:
              minmax(270px, 0.8fr)
              minmax(0, 2.1fr);
            gap: 15px;
            align-items: start;
          }

          .mr-card {
            min-width: 0;
            overflow: hidden;
            border: 1px solid var(--mr-line);
            border-radius: 11px;
            background: #fffefa;
          }

          .mr-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            min-height: 57px;
            padding: 13px 16px;
            border-bottom: 1px solid #edf0f2;
          }

          .mr-card-header h2 {
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 17px;
            letter-spacing: -0.25px;
            font-weight: 750;
          }

          .mr-catalog-search {
            height: 39px;
            display: flex;
            align-items: center;
            gap: 9px;
            border: 1px solid #e0e4ea;
            background: white;
            border-radius: 7px;
            padding: 0 11px;
            margin: 14px;
            color: #77869d;
          }

          .mr-catalog-search input {
            width: 100%;
            min-width: 0;
            background: transparent;
            outline: 0;
            border: 0;
            color: var(--mr-ink);
          }

          .mr-report-list {
            padding: 0 10px 12px;
          }

          .mr-report-option {
            display: flex;
            align-items: center;
            width: 100%;
            gap: 12px;
            text-align: left;
            padding: 12px 10px;
            border: 1px solid transparent;
            background: transparent;
            border-radius: 8px;
            color: var(--mr-ink);
          }

          .mr-report-option:hover {
            background: #fff9ef;
          }

          .mr-report-option.mr-report-selected {
            border-color: #ffda93;
            background: #fff4e0;
          }

          .mr-report-icon {
            height: 39px;
            width: 39px;
            flex-shrink: 0;
            border-radius: 8px;
            display: grid;
            place-items: center;
            background: #fff0d1;
          }

          .mr-report-copy {
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 5px;
          }

          .mr-report-copy strong {
            font-size: 12px;
          }

          .mr-report-copy small {
            color: var(--mr-muted);
            font-size: 11px;
            line-height: 1.45;
          }

          .mr-main {
            display: flex;
            flex-direction: column;
            gap: 15px;
            min-width: 0;
          }

          .mr-report-type {
            color: #a56f00;
            background: #fff0cf;
            border-radius: 20px;
            padding: 6px 11px;
            white-space: nowrap;
          }

          .mr-selected-report {
            display: flex;
            align-items: center;
            gap: 13px;
            padding: 18px 18px 8px;
          }

          .mr-large-icon {
            width: 53px;
            height: 53px;
            flex-shrink: 0;
            display: grid;
            place-items: center;
            border-radius: 10px;
            background: #fff1d8;
          }

          .mr-selected-report h3 {
            margin: 0;
            font-size: 16px;
          }

          .mr-selected-report p {
            margin: 6px 0 0;
            line-height: 1.55;
            color: var(--mr-muted);
          }

          .mr-controls {
            padding: 14px 18px 18px;
            display: grid;
            grid-template-columns:
              repeat(2, minmax(0, 1fr));
            gap: 15px;
          }

          .mr-controls > label {
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-width: 0;
          }

          .mr-controls > label > span {
            font-weight: 700;
            font-size: 12px;
          }

          .mr-controls input,
          .mr-control-wrap,
          .mr-date-wrap {
            height: 40px;
            border-radius: 7px;
            border: 1px solid #e1e5eb;
            background: white;
            color: var(--mr-ink);
          }

          .mr-controls > label > input {
            width: 100%;
            padding: 0 11px;
            outline: 0;
          }

          .mr-control-wrap,
          .mr-date-wrap {
            display: flex;
            align-items: center;
            padding: 0 11px;
            gap: 8px;
          }

          .mr-control-wrap select {
            flex: 1;
            width: 100%;
            appearance: none;
            border: 0;
            outline: 0;
            background: transparent;
            color: var(--mr-ink);
          }

          .mr-date-wrap input {
            min-width: 0;
            flex: 1;
            width: 100%;
            border: 0;
            outline: 0;
            background: transparent;
            color: var(--mr-ink);
          }

          .mr-generator-footer {
            padding: 14px 18px;
            border-top: 1px solid #edf0f2;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 10px;
          }

          .mr-validation {
            margin: 0 18px 13px;
            color: #b33b3d;
          }

          .mr-generated {
            color: var(--mr-muted);
            font-size: 11px;
          }

          .mr-preview-info {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            padding: 17px;
            border-bottom: 1px solid #edf0f2;
          }

          .mr-preview-info > div {
            display: flex;
            flex-direction: column;
            gap: 6px;
            min-width: 0;
          }

          .mr-preview-info span {
            color: var(--mr-muted);
          }

          .mr-preview-info strong {
            overflow-wrap: anywhere;
          }

          .mr-preview-metrics {
            display: grid;
            grid-template-columns:
              repeat(4, minmax(0, 1fr));
            gap: 11px;
            padding: 15px 17px;
          }

          .mr-preview-metrics > div {
            padding: 15px;
            border: 1px solid #ece7dc;
            border-radius: 9px;
            background: #fffaf0;
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-width: 0;
          }

          .mr-preview-metrics small {
            color: var(--mr-muted);
            line-height: 1.4;
          }

          .mr-preview-metrics strong {
            font-size: 19px;
            overflow-wrap: anywhere;
          }

          .mr-table-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 17px;
          }

          .mr-table-header h3 {
            display: flex;
            align-items: center;
            gap: 9px;
            margin: 0;
            font-size: 14px;
          }

          .mr-table-header span {
            color: var(--mr-muted);
          }

          .mr-table-scroll {
            width: 100%;
            overflow-x: auto;
          }

          .mr-table-scroll table {
            min-width: 600px;
            width: 100%;
            border-collapse: collapse;
            text-align: left;
          }

          .mr-table-scroll th {
            background: #f7f7f7;
            font-size: 10px;
            padding: 12px;
            white-space: nowrap;
          }

          .mr-table-scroll td {
            padding: 12px;
            font-size: 11px;
            border-top: 1px solid #ebedf0;
            max-width: 270px;
            overflow-wrap: anywhere;
          }

          .mr-pagination {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 12px 17px;
            color: var(--mr-muted);
          }

          .mr-pagination > div {
            display: flex;
            align-items: center;
            gap: 9px;
          }

          .mr-pagination button {
            width: 32px;
            height: 32px;
            display: grid;
            place-items: center;
            border-radius: 7px;
            border: 1px solid #e5e8ed;
            background: white;
          }

          .mr-aggregate {
            display: flex;
            align-items: flex-start;
            gap: 11px;
            padding: 17px;
            color: #58708e;
          }

          .mr-aggregate strong {
            color: var(--mr-ink);
          }

          .mr-aggregate p {
            line-height: 1.6;
            margin: 6px 0 0;
          }

          .mr-json {
            padding: 14px 17px;
            border-top: 1px solid #ebedf0;
          }

          .mr-json summary {
            cursor: pointer;
            font-weight: 650;
          }

          .mr-json pre {
            max-height: 360px;
            overflow: auto;
            background: #f4f6f9;
            border: 1px solid #e3e8ef;
            border-radius: 8px;
            padding: 15px;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
            font-size: 11px;
            line-height: 1.6;
            margin-top: 12px;
          }

          .mr-empty {
            min-height: 240px;
            padding: 30px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            gap: 12px;
            color: #8593a8;
          }

          .mr-empty strong {
            color: var(--mr-ink);
          }

          .mr-empty p {
            max-width: 310px;
            margin: 0;
            line-height: 1.6;
          }

          .mr-preview-empty {
            min-height: 300px;
          }

          .mr-empty-small {
            padding: 24px 15px;
            text-align: center;
            color: var(--mr-muted);
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 9px;
          }

          .mr-error,
          .mr-success {
            border-radius: 8px;
            padding: 12px 15px;
            display: flex;
            align-items: center;
            gap: 10px;
          }

          .mr-error {
            border: 1px solid #edb9bb;
            background: #fff0f0;
            color: #b52f34;
            margin-bottom: 14px;
          }

          .mr-error span {
            flex: 1;
          }

          .mr-error button {
            border: 1px solid currentColor;
            background: white;
            border-radius: 6px;
            padding: 6px 10px;
          }

          .mr-success {
            border: 1px solid #bfe4cf;
            background: #edf8f1;
            color: #177f4c;
          }

          .mr-bottom-note {
            display: flex;
            align-items: flex-start;
            gap: 9px;
            line-height: 1.6;
            margin-top: 15px;
            color: var(--mr-muted);
          }

          .mr-bottom-note svg {
            flex-shrink: 0;
            margin-top: 2px;
          }

          .mr-spin {
            animation: mr-spin 1s linear infinite;
          }

          @keyframes mr-spin {
            to {
              transform: rotate(360deg);
            }
          }

          @media (max-width: 1230px) {
            .mr-layout {
              grid-template-columns: 1fr;
            }

            .mr-report-list {
              display: grid;
              grid-template-columns:
                repeat(2, minmax(0, 1fr));
              gap: 7px;
            }
          }

          @media (max-width: 950px) {
            .mr-summary {
              grid-template-columns:
                repeat(2, minmax(0, 1fr));
            }
          }

          @media (max-width: 720px) {
            .mr-header {
              align-items: flex-start;
              flex-direction: column;
            }

            .mr-report-list {
              grid-template-columns: 1fr;
            }

            .mr-controls {
              grid-template-columns: 1fr;
            }

            .mr-preview-metrics {
              grid-template-columns:
                repeat(2, minmax(0, 1fr));
            }
          }

          @media (max-width: 520px) {
            .mr-page {
              padding: 15px 12px;
            }

            .mr-header h1 {
              font-size: 24px;
            }

            .mr-header-actions {
              flex-wrap: wrap;
            }

            .mr-summary {
              grid-template-columns: 1fr;
            }

            .mr-preview-info {
              grid-template-columns: 1fr;
            }

            .mr-preview-metrics {
              grid-template-columns: 1fr;
            }

            .mr-card-header {
              flex-wrap: wrap;
            }

            .mr-pagination {
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
  value,
  label,
  detail,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
  detail: string;
}) {
  return (
    <div className="mr-metric">
      <span className="mr-metric-icon">
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
