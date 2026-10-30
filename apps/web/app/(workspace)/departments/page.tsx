"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  Building2,
  Plus,
  RefreshCcw,
  Trash2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { WorkspaceRequired } from "@/components/workspace/workspace-required";
import { useWorkspace } from "@/contexts/workspace-context";
import { ApiError } from "@/lib/api/client";

import {
  departmentsService,
  type Department,
} from "@/services/departments.service";

export default function DepartmentsPage() {
  return (
    <WorkspaceRequired>
      <DepartmentsContent />
    </WorkspaceRequired>
  );
}

function DepartmentsContent() {
  const {
    workspaceId,
    workspace,
    canManage,
  } = useWorkspace();

  const [
    departments,
    setDepartments,
  ] = useState<Department[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [showCreate, setShowCreate] =
    useState(false);

  const [name, setName] =
    useState("");

  const [code, setCode] =
    useState("");

  const [description, setDescription] =
    useState("");

  const loadDepartments =
    useCallback(async () => {
      if (!workspaceId) {
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const response =
          await departmentsService.list(
            workspaceId,
          );

        setDepartments(
          response.departments,
        );
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load departments.",
        );
      } finally {
        setLoading(false);
      }
    }, [workspaceId]);

  useEffect(() => {
    void loadDepartments();
  }, [loadDepartments]);

  async function createDepartment(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (
      !workspaceId ||
      !name.trim()
    ) {
      return;
    }

    try {
      setSaving(true);
      setError(null);

      await departmentsService.create(
        workspaceId,
        {
          name: name.trim(),

          code:
            code.trim() ||
            null,

          description:
            description.trim() ||
            null,
        },
      );

      setName("");
      setCode("");
      setDescription("");
      setShowCreate(false);

      await loadDepartments();
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "Unable to create department.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function deactivateDepartment(
    departmentId: string,
  ) {
    if (
      !workspaceId ||
      !canManage
    ) {
      return;
    }

    const confirmed =
      window.confirm(
        "Deactivate this department?",
      );

    if (!confirmed) {
      return;
    }

    try {
      await departmentsService.deactivate(
        workspaceId,
        departmentId,
      );

      await loadDepartments();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to deactivate department.",
      );
    }
  }

  return (
    <div
      style={{
        maxWidth: 1500,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Departments"
        description={`Organization structure for ${workspace?.name ?? "workspace"}.`}
        actions={
          <div
            style={{
              display: "flex",
              gap: 8,
            }}
          >
            <Button
              variant="outline"
              onClick={() =>
                void loadDepartments()
              }
            >
              <RefreshCcw size={14} />
              Refresh
            </Button>

            {canManage ? (
              <Button
                onClick={() =>
                  setShowCreate(
                    (current) =>
                      !current,
                  )
                }
              >
                <Plus size={15} />
                Add Department
              </Button>
            ) : null}
          </div>
        }
      />

      {error ? (
        <div
          className="auth-error"
          style={{
            marginBottom: 14,
          }}
        >
          {error}
        </div>
      ) : null}

      {showCreate &&
      canManage ? (
        <section
          className="panel"
          style={{
            marginBottom: 14,
          }}
        >
          <div className="panel-header">
            <h2 className="text-section-title">
              New Department
            </h2>
          </div>

          <form
            className="panel-body"
            onSubmit={
              createDepartment
            }
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "1fr 180px",
                gap: 12,
              }}
            >
              <label className="field">
                <span className="field-label">
                  Department name
                </span>

                <input
                  className="input"
                  value={name}
                  required
                  minLength={2}
                  maxLength={150}
                  onChange={(
                    event,
                  ) =>
                    setName(
                      event.target
                        .value,
                    )
                  }
                />
              </label>

              <label className="field">
                <span className="field-label">
                  Code
                </span>

                <input
                  className="input"
                  value={code}
                  maxLength={50}
                  placeholder="ENG"
                  onChange={(
                    event,
                  ) =>
                    setCode(
                      event.target
                        .value,
                    )
                  }
                />
              </label>
            </div>

            <label
              className="field"
              style={{
                marginTop: 12,
              }}
            >
              <span className="field-label">
                Description
              </span>

              <textarea
                className="input"
                value={description}
                maxLength={500}
                rows={3}
                onChange={(
                  event,
                ) =>
                  setDescription(
                    event.target
                      .value,
                  )
                }
              />
            </label>

            <div
              style={{
                display: "flex",
                gap: 8,
                marginTop: 14,
              }}
            >
              <Button
                type="submit"
                disabled={saving}
              >
                {saving
                  ? "Creating..."
                  : "Create Department"}
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  setShowCreate(false)
                }
              >
                Cancel
              </Button>
            </div>
          </form>
        </section>
      ) : null}

      <section
        className="panel"
        style={{
          overflow: "hidden",
        }}
      >
        <div className="panel-header">
          <div>
            <h2 className="text-section-title">
              Department Directory
            </h2>

            <span className="text-label">
              {departments.length} departments
            </span>
          </div>
        </div>

        {loading ? (
          <div
            className="panel-body"
            style={{
              display: "grid",
              gap: 8,
            }}
          >
            {Array.from({
              length: 6,
            }).map((_, index) => (
              <div
                key={index}
                className="skeleton"
                style={{
                  height: 42,
                }}
              />
            ))}
          </div>
        ) : departments.length ===
          0 ? (
          <div
            className="panel-body"
            style={{
              padding: 40,
              textAlign: "center",
            }}
          >
            <Building2
              size={32}
            />

            <h3
              style={{
                marginTop: 10,
              }}
            >
              No departments yet
            </h3>

            <p className="text-label">
              Create the first
              department for this
              workspace.
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Department</th>
                  <th>Code</th>
                  <th>Description</th>
                  <th>Status</th>

                  {canManage ? (
                    <th>Actions</th>
                  ) : null}
                </tr>
              </thead>

              <tbody>
                {departments.map(
                  (department) => (
                    <tr
                      key={
                        department.id
                      }
                    >
                      <td>
                        <strong>
                          {
                            department.name
                          }
                        </strong>
                      </td>

                      <td>
                        {department.code ??
                          "—"}
                      </td>

                      <td>
                        {department.description ??
                          "—"}
                      </td>

                      <td>
                        <StatusBadge
                          variant={
                            department.is_active
                              ? "success"
                              : "neutral"
                          }
                        >
                          {department.is_active
                            ? "Active"
                            : "Inactive"}
                        </StatusBadge>
                      </td>

                      {canManage ? (
                        <td>
                          {department.is_active ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                void deactivateDepartment(
                                  department.id,
                                )
                              }
                            >
                              <Trash2
                                size={
                                  14
                                }
                              />
                            </Button>
                          ) : (
                            "—"
                          )}
                        </td>
                      ) : null}
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}