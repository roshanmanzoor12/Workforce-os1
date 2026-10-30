"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";

import {
  CalendarDays,
  Plus,
  RefreshCcw,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

import {
  WorkspaceRequired,
} from "@/components/workspace/workspace-required";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  employeesService,
  type Employee,
} from "@/services/employees.service";

import {
  performanceService,
} from "@/services/performance.service";

import type {
  ReviewPublic,
} from "@/types/performance";

import {
  useModalFocus,
} from "@/lib/ui/use-modal-focus";

function dateLabel(
  value: string | null | undefined,
) {
  if (!value) return "—";

  const date = new Date(value);

  return Number.isFinite(date.getTime())
    ? date.toLocaleDateString()
    : "Unknown";
}

function statusVariant(
  status: string,
): "success" | "warning" | "neutral" {
  if (
    ["approved", "completed", "submitted"].includes(
      status,
    )
  ) {
    return "success";
  }

  if (
    ["draft", "pending", "under_review"].includes(
      status,
    )
  ) {
    return "warning";
  }

  return "neutral";
}

export default function PerformancePage() {
  const { workspaceId } = useWorkspace();

  return (
    <WorkspaceRequired>
      <PerformanceContent
        key={workspaceId ?? "no-workspace"}
      />
    </WorkspaceRequired>
  );
}

function PerformanceContent() {
  const { workspaceId } = useWorkspace();

  const [employees, setEmployees] =
    useState<Employee[]>([]);

  const [reviews, setReviews] =
    useState<ReviewPublic[]>([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [success, setSuccess] =
    useState<string | null>(null);

  const [dialog, setDialog] =
    useState<"cycle" | "review" | null>(null);

  const [employeeFilter, setEmployeeFilter] =
    useState("");

  const [cycleName, setCycleName] = useState("");
  const [cycleStartsOn, setCycleStartsOn] = useState("");
  const [cycleEndsOn, setCycleEndsOn] = useState("");

  const [reviewCycleId, setReviewCycleId] = useState("");
  const [reviewEmployeeId, setReviewEmployeeId] =
    useState("");

  const [reviewRating, setReviewRating] = useState("5");
  const [reviewSummary, setReviewSummary] = useState("");

  const alive = useRef(false);
  const sequence = useRef(0);
  const mutationLock = useRef(false);

  useEffect(() => {
    alive.current = true;

    return () => {
      alive.current = false;
      ++sequence.current;
    };
  }, []);

  const load = useCallback(
    async (silent = false) => {
      if (!workspaceId) {
        setLoading(false);
        return;
      }

      const request = ++sequence.current;

      if (silent) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError(null);

      try {
        const [
          employeeResponse,
          reviewResponse,
        ] = await Promise.all([
          employeesService.list(
            workspaceId,
            {
              employmentStatus: "active",
              includeInactive: false,
            },
          ),
          performanceService.listReviews(
            workspaceId,
            employeeFilter || undefined,
          ),
        ]);

        if (
          !alive.current ||
          request !== sequence.current
        ) {
          return;
        }

        setEmployees(employeeResponse.employees);
        setReviews(reviewResponse.items);

        const firstEmployee =
          employeeResponse.employees[0];

        setReviewEmployeeId((current) =>
          employeeResponse.employees.some(
            (employee) => employee.id === current,
          )
            ? current
            : firstEmployee?.id ?? "",
        );
      } catch (cause) {
        if (
          alive.current &&
          request === sequence.current
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load performance data.",
          );
        }
      } finally {
        if (
          alive.current &&
          request === sequence.current
        ) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [workspaceId, employeeFilter],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const averageRating = useMemo(
    () =>
      reviews.length
        ? (
            reviews.reduce(
              (sum, review) => sum + review.rating,
              0,
            ) / reviews.length
          ).toFixed(1)
        : "—",
    [reviews],
  );

  function openDialog(
    value: "cycle" | "review",
  ) {
    setError(null);
    setSuccess(null);
    setDialog(value);
  }

  function closeDialog() {
    if (!mutationLock.current) {
      setDialog(null);
    }
  }

  async function submitCycle(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (
      mutationLock.current ||
      !workspaceId
    ) {
      return;
    }

    if (
      !cycleName.trim() ||
      !cycleStartsOn ||
      !cycleEndsOn
    ) {
      setError("Complete all review cycle fields.");
      return;
    }

    if (cycleEndsOn < cycleStartsOn) {
      setError(
        "Cycle end date cannot be before its start date.",
      );
      return;
    }

    mutationLock.current = true;
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const cycle =
        await performanceService.createCycle(
          workspaceId,
          {
            name: cycleName.trim(),
            starts_on: cycleStartsOn,
            ends_on: cycleEndsOn,
          },
        );

      if (!alive.current) return;

      setReviewCycleId(cycle.id);

      setCycleName("");
      setCycleStartsOn("");
      setCycleEndsOn("");

      setDialog(null);
      setSuccess("Review cycle created.");
    } catch (cause) {
      if (alive.current) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to create review cycle.",
        );
      }
    } finally {
      mutationLock.current = false;

      if (alive.current) {
        setSaving(false);
      }
    }
  }

  async function submitReview(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (
      mutationLock.current ||
      !workspaceId
    ) {
      return;
    }

    const rating = Number(reviewRating);

    if (
      !reviewCycleId.trim() ||
      !reviewEmployeeId ||
      !reviewSummary.trim()
    ) {
      setError(
        "Complete the cycle, employee and summary fields.",
      );
      return;
    }

    if (
      !Number.isInteger(rating) ||
      rating < 1 ||
      rating > 5
    ) {
      setError("Select a rating from 1 to 5.");
      return;
    }

    mutationLock.current = true;
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await performanceService.createReview(
        workspaceId,
        {
          cycle_id: reviewCycleId.trim(),
          employee_id: reviewEmployeeId,
          rating,
          summary: reviewSummary.trim(),
        },
      );

      if (!alive.current) return;

      setReviewSummary("");
      setReviewRating("5");

      setDialog(null);
      setSuccess("Performance review submitted.");

      await load(true);
    } catch (cause) {
      if (alive.current) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to submit performance review.",
        );
      }
    } finally {
      mutationLock.current = false;

      if (alive.current) {
        setSaving(false);
      }
    }
  }

  const busy = loading || refreshing || saving;

  return (
    <div
      style={{
        maxWidth: 1600,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Performance"
        description="Create review cycles and manage employee performance reviews."
        actions={
          <>
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => openDialog("cycle")}
            >
              <CalendarDays size={15} />
              New Review Cycle
            </Button>

            <Button
              disabled={
                busy || employees.length === 0
              }
              onClick={() => openDialog("review")}
            >
              <Plus size={15} />
              Add Review
            </Button>

            <Button
              variant="ghost"
              size="sm"
              disabled={busy}
              onClick={() => void load(true)}
              aria-label="Refresh performance data"
            >
              <RefreshCcw size={15} />
            </Button>
          </>
        }
      />

      {error ? (
        <p role="alert">{error}</p>
      ) : null}

      {success ? (
        <p role="status">{success}</p>
      ) : null}

      <div
        className="metric-grid"
        style={{ marginBottom: 16 }}
      >
        {[
          {
            label: "Loaded Reviews",
            value: reviews.length,
          },
          {
            label: "Average Loaded Rating",
            value: averageRating,
          },
          {
            label: "Loaded Active Employees",
            value: employees.length,
          },
        ].map((metric) => (
          <section
            className="panel"
            key={metric.label}
          >
            <div className="panel-body">
              <span className="text-label">
                {metric.label}
              </span>

              <strong
                style={{
                  display: "block",
                  marginTop: 8,
                  fontSize: 24,
                }}
              >
                {loading ? "—" : metric.value}
              </strong>
            </div>
          </section>
        ))}
      </div>

      <section className="panel">
        <div
          className="panel-header"
          style={{
            display: "flex",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <h2 className="text-section-title">
            Performance Reviews
          </h2>

          <select
            value={employeeFilter}
            disabled={saving}
            onChange={(event) =>
              setEmployeeFilter(event.target.value)
            }
            aria-label="Filter reviews by employee"
            style={{
              ...inputStyle,
              width: "auto",
              minWidth: 180,
            }}
          >
            <option value="">All employees</option>

            {employees.map((employee) => (
              <option
                key={employee.id}
                value={employee.id}
              >
                {employee.full_name}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <div
            className="panel-body"
            role="status"
          >
            Loading performance reviews…
          </div>
        ) : reviews.length === 0 ? (
          <div className="panel-body">
            {error
              ? "Performance data could not be loaded. Try refreshing."
              : "No performance reviews yet. Create a cycle and add a review."}
          </div>
        ) : (
          <div
            className="table-container"
            style={{ overflowX: "auto" }}
          >
            <table className="data-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Rating</th>
                  <th>Summary</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>

              <tbody>
                {reviews.map((review) => (
                  <tr key={review.id}>
                    <td>
                      {employees.find(
                        (employee) =>
                          employee.id ===
                          review.employee_id,
                      )?.full_name ??
                        review.employee_id}
                    </td>

                    <td>{review.rating}/5</td>

                    <td
                      style={{
                        maxWidth: 480,
                        whiteSpace: "normal",
                        overflowWrap: "anywhere",
                      }}
                    >
                      {review.summary}
                    </td>

                    <td>
                      <StatusBadge
                        variant={statusVariant(
                          review.status,
                        )}
                      >
                        {review.status}
                      </StatusBadge>
                    </td>

                    <td>
                      {dateLabel(review.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {dialog === "cycle" ? (
        <Modal
          title="Create Review Cycle"
          busy={saving}
          onClose={closeDialog}
        >
          <form
            onSubmit={(event) =>
              void submitCycle(event)
            }
            style={formStyle}
          >
            {error ? (
              <p role="alert">{error}</p>
            ) : null}

            <label style={labelStyle}>
              Cycle Name

              <input
                required
                value={cycleName}
                disabled={saving}
                onChange={(event) =>
                  setCycleName(event.target.value)
                }
                style={inputStyle}
              />
            </label>

            <label style={labelStyle}>
              Starts On

              <input
                required
                type="date"
                value={cycleStartsOn}
                disabled={saving}
                onChange={(event) =>
                  setCycleStartsOn(
                    event.target.value,
                  )
                }
                style={inputStyle}
              />
            </label>

            <label style={labelStyle}>
              Ends On

              <input
                required
                type="date"
                value={cycleEndsOn}
                min={cycleStartsOn || undefined}
                disabled={saving}
                onChange={(event) =>
                  setCycleEndsOn(event.target.value)
                }
                style={inputStyle}
              />
            </label>

            <div style={actionsStyle}>
              <Button
                type="button"
                variant="outline"
                disabled={saving}
                onClick={closeDialog}
              >
                Cancel
              </Button>

              <Button
                type="submit"
                disabled={saving}
              >
                {saving
                  ? "Creating…"
                  : "Create Cycle"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}

      {dialog === "review" ? (
        <Modal
          title="Add Performance Review"
          busy={saving}
          onClose={closeDialog}
        >
          <form
            onSubmit={(event) =>
              void submitReview(event)
            }
            style={formStyle}
          >
            {error ? (
              <p role="alert">{error}</p>
            ) : null}

            <label style={labelStyle}>
              Review Cycle ID

              <input
                required
                value={reviewCycleId}
                disabled={saving}
                onChange={(event) =>
                  setReviewCycleId(
                    event.target.value,
                  )
                }
                style={inputStyle}
              />
            </label>

            <label style={labelStyle}>
              Employee

              <select
                required
                value={reviewEmployeeId}
                disabled={saving}
                onChange={(event) =>
                  setReviewEmployeeId(
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
              Rating

              <select
                value={reviewRating}
                disabled={saving}
                onChange={(event) =>
                  setReviewRating(event.target.value)
                }
                style={inputStyle}
              >
                {[5, 4, 3, 2, 1].map((rating) => (
                  <option
                    key={rating}
                    value={rating}
                  >
                    {rating}/5
                  </option>
                ))}
              </select>
            </label>

            <label style={labelStyle}>
              Summary

              <textarea
                required
                maxLength={5000}
                rows={6}
                value={reviewSummary}
                disabled={saving}
                onChange={(event) =>
                  setReviewSummary(
                    event.target.value,
                  )
                }
                style={{
                  ...inputStyle,
                  resize: "vertical",
                }}
              />
            </label>

            <div style={actionsStyle}>
              <Button
                type="button"
                variant="outline"
                disabled={saving}
                onClick={closeDialog}
              >
                Cancel
              </Button>

              <Button
                type="submit"
                disabled={saving}
              >
                {saving
                  ? "Submitting…"
                  : "Submit Review"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}
    </div>
  );
}

function Modal({
  title,
  children,
  onClose,
  busy,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  busy: boolean;
}) {
  const dialogRef = useModalFocus(
    true,
    onClose,
    busy,
  );

  return (
    <div
      ref={dialogRef}
      tabIndex={-1}
      role="dialog"
      aria-modal="true"
      aria-label={title}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 100,
        padding: 18,
        display: "grid",
        placeItems: "center",
        background: "rgba(0,0,0,.35)",
      }}
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget &&
          !busy
        ) {
          onClose();
        }
      }}
    >
      <section
        className="panel"
        style={{
          width: "min(620px,100%)",
          maxHeight: "90dvh",
          overflowY: "auto",
          background: "var(--color-surface, #fff)",
        }}
      >
        <div
          className="panel-header"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2 className="text-section-title">
            {title}
          </h2>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={busy}
            onClick={onClose}
            aria-label="Close"
          >
            <X size={15} />
          </Button>
        </div>

        <div className="panel-body">
          {children}
        </div>
      </section>
    </div>
  );
}

const inputStyle = {
  width: "100%",
  minHeight: 40,
  padding: 10,
  fontSize: 16,
  border: "1px solid var(--color-border, #ddd)",
  borderRadius: 7,
  background: "var(--color-surface, #fff)",
  color: "inherit",
} as const;

const labelStyle = {
  display: "grid",
  gap: 7,
} as const;

const formStyle = {
  display: "grid",
  gap: 14,
} as const;

const actionsStyle = {
  display: "flex",
  justifyContent: "flex-end",
  gap: 8,
} as const;