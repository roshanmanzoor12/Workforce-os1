"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Plus,
  RefreshCcw,
  ShieldAlert,
  UserRound,
  X,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { useWorkspace } from "@/contexts/workspace-context";
import {
  employeesService,
  type Employee,
} from "@/services/employees.service";
import { disciplineService } from "@/services/discipline.service";
import type {
  IncidentPublic,
  IncidentStatus,
} from "@/types/discipline";

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function employeeName(
  employees: Employee[],
  employeeId: string,
): string {
  return (
    employees.find(
      (employee) => employee.id === employeeId,
    )?.full_name ?? employeeId
  );
}

function statusVariant(
  status: string,
): "success" | "warning" | "neutral" {
  switch (status) {
    case "resolved":
      return "success";

    case "open":
    case "under_review":
      return "warning";

    default:
      return "neutral";
  }
}

const statuses: IncidentStatus[] = [
  "open",
  "under_review",
  "resolved",
  "dismissed",
];

export default function DisciplinePage() {
  return (
    <WorkspaceRequired>
      <DisciplineContent />
    </WorkspaceRequired>
  );
}

function DisciplineContent() {
  const { workspaceId } = useWorkspace();

  const [employees, setEmployees] = useState<Employee[]>([]);
  const [incidents, setIncidents] = useState<IncidentPublic[]>([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [selectedIncident, setSelectedIncident] =
    useState<IncidentPublic | null>(null);

  const [employeeFilter, setEmployeeFilter] = useState("");
  const [statusFilter, setStatusFilter] =
    useState<IncidentStatus | "all">("all");

  const [employeeId, setEmployeeId] = useState("");
  const [category, setCategory] = useState("");
  const [summary, setSummary] = useState("");
  const [details, setDetails] = useState("");
  const [action, setAction] = useState("");

  const load = useCallback(
    async (silent = false) => {
      if (!workspaceId) {
        return;
      }

      if (silent) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError(null);

      try {
        const [
          employeeResponse,
          incidentResponse,
        ] = await Promise.all([
          employeesService.list(
            workspaceId,
            {
              employmentStatus: "active",
              includeInactive: false,
            },
          ),
          disciplineService.listIncidents(
            workspaceId,
            employeeFilter || undefined,
          ),
        ]);

        setEmployees(employeeResponse.employees);
        setIncidents(incidentResponse.items);

        const firstEmployee =
          employeeResponse.employees[0];

        if (
          !employeeId &&
          firstEmployee
        ) {
          setEmployeeId(
            firstEmployee.id,
          );
        }
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught.message
            : "Unable to load discipline incidents.",
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [
      employeeFilter,
      employeeId,
      workspaceId,
    ],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const visibleIncidents = useMemo(() => {
    if (statusFilter === "all") {
      return incidents;
    }

    return incidents.filter(
      (incident) =>
        incident.status === statusFilter,
    );
  }, [
    incidents,
    statusFilter,
  ]);

  const openCount = useMemo(
    () =>
      incidents.filter(
        (incident) =>
          incident.status === "open",
      ).length,
    [incidents],
  );

  const reviewCount = useMemo(
    () =>
      incidents.filter(
        (incident) =>
          incident.status === "under_review",
      ).length,
    [incidents],
  );

  const resolvedCount = useMemo(
    () =>
      incidents.filter(
        (incident) =>
          incident.status === "resolved",
      ).length,
    [incidents],
  );

  const submitIncident = async () => {
    if (
      !workspaceId ||
      !employeeId ||
      !category.trim() ||
      !summary.trim()
    ) {
      setError(
        "Employee, category and summary are required.",
      );
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await disciplineService.createIncident(
        workspaceId,
        {
          employee_id: employeeId,
          category: category.trim(),
          summary: summary.trim(),
          details: details.trim() || null,
          action: action.trim() || null,
        },
      );

      setCategory("");
      setSummary("");
      setDetails("");
      setAction("");
      setShowCreate(false);
      setSuccess("Discipline incident created.");

      await load(true);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to create discipline incident.",
      );
    } finally {
      setSaving(false);
    }
  };

  const updateIncident = async (
    incident: IncidentPublic,
    nextStatus: IncidentStatus,
    nextAction: string,
  ) => {
    if (!workspaceId) {
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const updated =
        await disciplineService.updateIncident(
          workspaceId,
          incident.id,
          {
            status: nextStatus,
            action: nextAction.trim() || null,
          },
        );

      setIncidents((current) =>
        current.map((item) =>
          item.id === updated.id
            ? updated
            : item,
        ),
      );

      setSelectedIncident(updated);
      setSuccess("Incident updated.");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to update incident.",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 1600,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Discipline"
        description="Record, review and resolve employee discipline incidents."
        actions={
          <>
            <Button
              variant="outline"
              onClick={() =>
                setShowCreate(true)
              }
            >
              <Plus size={15} />
              New Incident
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                void load(true)
              }
              disabled={refreshing}
              aria-label="Refresh discipline incidents"
            >
              <RefreshCcw size={15} />
            </Button>
          </>
        }
      />

      {error ? (
        <div
          role="alert"
          style={{
            marginBottom: 14,
            padding: "10px 12px",
            border: "1px solid #efc6c6",
            borderRadius: 7,
            background: "#fff0f0",
            color: "#b52b2b",
            fontSize: 11,
          }}
        >
          {error}
        </div>
      ) : null}

      {success ? (
        <div
          role="status"
          style={{
            marginBottom: 14,
            padding: "10px 12px",
            border: "1px solid #cce5c4",
            borderRadius: 7,
            background: "#f0faed",
            color: "#34732a",
            fontSize: 11,
            display: "flex",
            alignItems: "center",
            gap: 7,
          }}
        >
          <CheckCircle2 size={15} />
          {success}
        </div>
      ) : null}

      <div
        className="metric-grid"
        style={{ marginBottom: 16 }}
      >
        <section className="panel">
          <div className="panel-body">
            <span className="text-label">
              Open
            </span>

            <strong
              style={{
                display: "block",
                marginTop: 8,
                fontSize: 24,
              }}
            >
              {openCount}
            </strong>
          </div>
        </section>

        <section className="panel">
          <div className="panel-body">
            <span className="text-label">
              Under Review
            </span>

            <strong
              style={{
                display: "block",
                marginTop: 8,
                fontSize: 24,
              }}
            >
              {reviewCount}
            </strong>
          </div>
        </section>

        <section className="panel">
          <div className="panel-body">
            <span className="text-label">
              Resolved
            </span>

            <strong
              style={{
                display: "block",
                marginTop: 8,
                fontSize: 24,
              }}
            >
              {resolvedCount}
            </strong>
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="text-section-title">
              Discipline Incidents
            </h2>

            <p
              className="text-label"
              style={{ marginTop: 4 }}
            >
              Workspace incidents and their current resolution state.
            </p>
          </div>

          <div
            style={{
              display: "flex",
              gap: 8,
              flexWrap: "wrap",
            }}
          >
            <select
              value={employeeFilter}
              onChange={(event) =>
                setEmployeeFilter(
                  event.target.value,
                )
              }
              style={selectStyle}
              aria-label="Filter incidents by employee"
            >
              <option value="">
                All employees
              </option>

              {employees.map((employee) => (
                <option
                  key={employee.id}
                  value={employee.id}
                >
                  {employee.full_name}
                </option>
              ))}
            </select>

            <select
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(
                  event.target.value as
                    | IncidentStatus
                    | "all",
                )
              }
              style={selectStyle}
              aria-label="Filter incidents by status"
            >
              <option value="all">
                All statuses
              </option>

              {statuses.map((status) => (
                <option
                  key={status}
                  value={status}
                >
                  {status.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div style={stateStyle}>
            Loading discipline incidents…
          </div>
        ) : visibleIncidents.length === 0 ? (
          <div style={stateStyle}>
            <ShieldAlert size={24} />

            <strong>
              No discipline incidents found.
            </strong>

            <span>
              Create an incident when a documented disciplinary record is required.
            </span>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Category</th>
                  <th>Summary</th>
                  <th>Status</th>
                  <th>Action</th>
                  <th>Created</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {visibleIncidents.map(
                  (incident) => (
                    <tr key={incident.id}>
                      <td>
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                          }}
                        >
                          <UserRound size={15} />

                          {employeeName(
                            employees,
                            incident.employee_id,
                          )}
                        </div>
                      </td>

                      <td>
                        {incident.category}
                      </td>

                      <td
                        style={{
                          maxWidth: 380,
                          whiteSpace: "normal",
                          lineHeight: 1.5,
                        }}
                      >
                        {incident.summary}
                      </td>

                      <td>
                        <StatusBadge
                          variant={statusVariant(
                            incident.status,
                          )}
                        >
                          {incident.status.replace(
                            "_",
                            " ",
                          )}
                        </StatusBadge>
                      </td>

                      <td>
                        {incident.action || "—"}
                      </td>

                      <td>
                        {formatDate(
                          incident.created_at,
                        )}
                      </td>

                      <td>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            setSelectedIncident(
                              incident,
                            )
                          }
                        >
                          Review
                        </Button>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {showCreate ? (
        <Modal
          title="Create Discipline Incident"
          onClose={() =>
            setShowCreate(false)
          }
        >
          <div style={formGridStyle}>
            <label style={labelStyle}>
              Employee

              <select
                value={employeeId}
                onChange={(event) =>
                  setEmployeeId(
                    event.target.value,
                  )
                }
                style={inputStyle}
              >
                <option value="">
                  Select employee
                </option>

                {employees.map((employee) => (
                  <option
                    key={employee.id}
                    value={employee.id}
                  >
                    {employee.full_name}
                  </option>
                ))}
              </select>
            </label>

            <label style={labelStyle}>
              Category

              <input
                value={category}
                onChange={(event) =>
                  setCategory(
                    event.target.value,
                  )
                }
                maxLength={80}
                placeholder="Attendance, conduct, policy…"
                style={inputStyle}
              />
            </label>

            <label style={labelStyle}>
              Summary

              <input
                value={summary}
                onChange={(event) =>
                  setSummary(
                    event.target.value,
                  )
                }
                maxLength={500}
                placeholder="Short incident summary"
                style={inputStyle}
              />
            </label>

            <label style={labelStyle}>
              Details

              <textarea
                value={details}
                onChange={(event) =>
                  setDetails(
                    event.target.value,
                  )
                }
                maxLength={10000}
                rows={6}
                placeholder="Document the incident details…"
                style={{
                  ...inputStyle,
                  height: "auto",
                  padding: 10,
                  resize: "vertical",
                }}
              />
            </label>

            <label style={labelStyle}>
              Action

              <input
                value={action}
                onChange={(event) =>
                  setAction(
                    event.target.value,
                  )
                }
                maxLength={120}
                placeholder="Warning issued, meeting scheduled…"
                style={inputStyle}
              />
            </label>
          </div>

          <div style={modalActionsStyle}>
            <Button
              variant="outline"
              onClick={() =>
                setShowCreate(false)
              }
            >
              Cancel
            </Button>

            <Button
              onClick={() =>
                void submitIncident()
              }
              disabled={saving}
            >
              {saving
                ? "Creating…"
                : "Create Incident"}
            </Button>
          </div>
        </Modal>
      ) : null}

      {selectedIncident ? (
        <IncidentReviewModal
          incident={selectedIncident}
          employeeName={employeeName(
            employees,
            selectedIncident.employee_id,
          )}
          saving={saving}
          onClose={() =>
            setSelectedIncident(null)
          }
          onSave={updateIncident}
        />
      ) : null}
    </div>
  );
}

function IncidentReviewModal({
  incident,
  employeeName,
  saving,
  onClose,
  onSave,
}: {
  incident: IncidentPublic;
  employeeName: string;
  saving: boolean;
  onClose: () => void;
  onSave: (
    incident: IncidentPublic,
    status: IncidentStatus,
    action: string,
  ) => Promise<void>;
}) {
  const [status, setStatus] =
    useState<IncidentStatus>(
      incident.status as IncidentStatus,
    );

  const [action, setAction] =
    useState(incident.action ?? "");

  return (
    <Modal
      title="Review Discipline Incident"
      onClose={onClose}
    >
      <div
        style={{
          display: "grid",
          gap: 14,
        }}
      >
        <div
          style={{
            padding: 12,
            border: "1px solid var(--color-border)",
            borderRadius: 8,
            background: "#fffefa",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontWeight: 600,
            }}
          >
            <UserRound size={15} />
            {employeeName}
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginTop: 10,
            }}
          >
            <AlertTriangle size={15} />
            <strong>
              {incident.category}
            </strong>
          </div>

          <p
            style={{
              marginTop: 10,
              fontSize: 11,
              lineHeight: 1.6,
            }}
          >
            {incident.summary}
          </p>

          {incident.details ? (
            <p
              className="text-label"
              style={{
                marginTop: 8,
                lineHeight: 1.6,
              }}
            >
              {incident.details}
            </p>
          ) : null}
        </div>

        <label style={labelStyle}>
          Status

          <select
            value={status}
            onChange={(event) =>
              setStatus(
                event.target.value as IncidentStatus,
              )
            }
            style={inputStyle}
          >
            {statuses.map((item) => (
              <option
                key={item}
                value={item}
              >
                {item.replace("_", " ")}
              </option>
            ))}
          </select>
        </label>

        <label style={labelStyle}>
          Action

          <input
            value={action}
            onChange={(event) =>
              setAction(event.target.value)
            }
            maxLength={120}
            style={inputStyle}
          />
        </label>
      </div>

      <div style={modalActionsStyle}>
        <Button
          variant="outline"
          onClick={onClose}
        >
          Cancel
        </Button>

        <Button
          onClick={() =>
            void onSave(
              incident,
              status,
              action,
            )
          }
          disabled={saving}
        >
          {saving
            ? "Saving…"
            : "Save Changes"}
        </Button>
      </div>
    </Modal>
  );
}

function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 100,
        background: "rgba(0,0,0,.35)",
        display: "grid",
        placeItems: "center",
        padding: 18,
      }}
      onMouseDown={(event) => {
        if (
          event.currentTarget === event.target
        ) {
          onClose();
        }
      }}
    >
      <div
        className="panel"
        style={{
          width: "min(680px, 100%)",
          maxHeight: "90vh",
          overflow: "auto",
          background: "#fffefa",
        }}
      >
        <div
          className="panel-header"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <h2 className="text-section-title">
            {title}
          </h2>

          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={15} />
          </Button>
        </div>

        <div className="panel-body">
          {children}
        </div>
      </div>
    </div>
  );
}

const inputStyle = {
  width: "100%",
  minHeight: 36,
  padding: "0 10px",
  border: "1px solid var(--color-border)",
  borderRadius: 7,
  outline: "none",
  background: "#fffefa",
  color: "#303235",
  fontSize: 11,
} as const;

const selectStyle = {
  ...inputStyle,
  width: "auto",
  minWidth: 170,
} as const;

const labelStyle = {
  display: "grid",
  gap: 6,
  color: "var(--color-text-muted)",
  fontSize: 10,
} as const;

const formGridStyle = {
  display: "grid",
  gap: 14,
} as const;

const modalActionsStyle = {
  display: "flex",
  justifyContent: "flex-end",
  gap: 8,
  marginTop: 18,
} as const;

const stateStyle = {
  minHeight: 260,
  display: "grid",
  placeItems: "center",
  alignContent: "center",
  gap: 8,
  padding: 32,
  color: "var(--color-text-muted)",
  fontSize: 11,
  textAlign: "center",
} as const;