"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import type {
  FormEvent,
  ReactNode,
} from "react";

import {
  Archive,
  CalendarDays,
  CheckCircle2,
  Eye,
  FileText,
  Flag,
  MoreHorizontal,
  Pencil,
  Plus,
  RefreshCcw,
  Search,
  Sparkles,
  Target,
  Trash2,
  X,
} from "lucide-react";

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
  goalsService,
} from "@/services/goals.service";

import type {
  GoalPriority,
  GoalPublic,
  GoalStatus,
} from "@/types/goals";

type GoalUpdate =
  Parameters<typeof goalsService.updateMine>[2];

type Tab =
  | "milestones"
  | "tasks"
  | "notes";

type Editor =
  | {
      kind: "create";
    }
  | {
      kind: "edit";
      goal: GoalPublic;
    };

type Draft = {
  title: string;
  description: string;
  priority: GoalPriority;
  status: GoalStatus;
  startDate: string;
  dueDate: string;
};

function pretty(value: string): string {
  return value
    .replace(/[_-]+/g, " ")
    .replace(
      /\b\w/g,
      (letter) => letter.toUpperCase(),
    );
}

function dateLabel(
  value: string | null | undefined,
): string {
  if (!value) {
    return "No date";
  }

  const date =
    /^\d{4}-\d{2}-\d{2}$/.test(value)
      ? new Date(`${value}T00:00:00`)
      : new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "No date";
  }

  return date.toLocaleDateString(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  );
}

function percent(value: number): number {
  return Number.isFinite(value)
    ? Math.max(
        0,
        Math.min(
          100,
          Math.round(value),
        ),
      )
    : 0;
}

function message(
  cause: unknown,
  fallback: string,
): string {
  return cause instanceof Error
    ? cause.message
    : fallback;
}

export default function GoalsPage() {
  const {
    workspaceId,
    user,
    mode,
    loading,
    workspaceLoading,
  } = useWorkspace();

  if (
    loading ||
    (mode !== "personal" && workspaceLoading)
  ) {
    return (
      <div role="status" style={{ padding: 24 }}>
        Loading goals...
      </div>
    );
  }

  const content = (
    <GoalsContent
      key={`${mode}:${workspaceId ?? "none"}:${user?.id ?? "none"}`}
    />
  );

  if (mode === "personal") {
    return content;
  }

  return (
    <WorkspaceRequired>
      {content}
    </WorkspaceRequired>
  );
}

function GoalsContent() {
  const {
    workspaceId,
    workspace,
    user,
    mode,
  } = useWorkspace();

  const personal = mode === "personal";
  const goalWorkspaceId = personal ? null : workspaceId;

  const [employee, setEmployee] =
    useState<Employee | null>(null);

  const [goals, setGoals] =
    useState<GoalPublic[]>([]);

  const [selectedId, setSelectedId] =
    useState<string | null>(null);

  const [filter, setFilter] =
    useState<GoalStatus | "all">("all");

  const [search, setSearch] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [busy, setBusy] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [notice, setNotice] =
    useState<string | null>(null);

  const [editor, setEditor] =
    useState<Editor | null>(null);

  const request = useRef(0);
  const mutation = useRef(false);

  const load = useCallback(
    async () => {
      const ticket = ++request.current;

      if (
        !user?.id ||
        (!personal && !goalWorkspaceId)
      ) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        if (personal) {
          setEmployee(null);
        } else {
          const response = await employeesService.list(
            goalWorkspaceId!,
            {
              includeInactive: true,
            },
          );

          if (ticket !== request.current) return;

          const owner =
            response.employees.find(
              (item) => item.user_id === user.id,
            ) ?? null;

          setEmployee(owner);

          if (!owner) {
            setGoals([]);
            setSelectedId(null);
            return;
          }
        }

        const result = await goalsService.listMine(
          goalWorkspaceId,
        );

        if (ticket !== request.current) return;

        setGoals(result.items);

        setSelectedId((current) =>
          result.items.some(
            (goal) => goal.id === current,
          )
            ? current
            : result.items[0]?.id ?? null,
        );
      } catch (cause) {
        if (ticket === request.current) {
          setError(
            message(
              cause,
              "Unable to load goals.",
            ),
          );
        }
      } finally {
        if (ticket === request.current) {
          setLoading(false);
        }
      }
    },
    [
      goalWorkspaceId,
      personal,
      user?.id,
    ],
  );

  useEffect(
    () => {
      void load();

      return () => {
        request.current += 1;
      };
    },
    [load],
  );

  const visibleGoals = useMemo(
    () => {
      const query =
        search.trim().toLowerCase();

      return goals.filter(
        (goal) =>
          (
            filter === "all" ||
            goal.status === filter
          ) &&
          (
            !query ||
            `${goal.title} ${goal.description ?? ""}`
              .toLowerCase()
              .includes(query)
          ),
      );
    },
    [
      goals,
      filter,
      search,
    ],
  );

  const selectedGoal =
    visibleGoals.find(
      (goal) =>
        goal.id === selectedId,
    ) ??
    visibleGoals[0] ??
    null;

  const activeCount =
    goals.filter(
      (goal) =>
        goal.status === "active",
    ).length;

  const completedCount =
    goals.filter(
      (goal) =>
        goal.status === "completed",
    ).length;

  const averageProgress =
    goals.length
      ? Math.round(
          goals.reduce(
            (total, goal) =>
              total +
              percent(
                goal.progress_percent,
              ),
            0,
          ) / goals.length,
        )
      : 0;

  async function updateGoal(
    id: string,
    payload: GoalUpdate,
  ): Promise<boolean> {
    if (
      !user?.id ||
      (!personal && !goalWorkspaceId) ||
      mutation.current ||
      loading
    ) {
      return false;
    }

    mutation.current = true;

    setBusy(true);
    setError(null);
    setNotice(null);

    try {
      const updated =
        await goalsService.updateMine(
          goalWorkspaceId,
          id,
          payload,
        );

      setGoals(
        (current) =>
          current.map(
            (goal) =>
              goal.id === updated.id
                ? updated
                : goal,
          ),
      );

      setNotice(
        "Goal updated successfully.",
      );

      return true;
    } catch (cause) {
      setError(
        message(
          cause,
          "Unable to update goal.",
        ),
      );

      return false;
    } finally {
      mutation.current = false;
      setBusy(false);
    }
  }

  async function saveEditor(
    draft: Draft,
  ): Promise<void> {
    if (
      !editor ||
      !user?.id ||
      (!personal && (!goalWorkspaceId || !employee)) ||
      mutation.current ||
      loading
    ) {
      return;
    }

    const payload = {
      title:
        draft.title.trim(),

      description:
        draft.description.trim() ||
        null,

      priority:
        draft.priority,

      start_date:
        draft.startDate || null,

      due_date:
        draft.dueDate || null,
    };

    if (
      editor.kind === "edit"
    ) {
      const saved =
        await updateGoal(
          editor.goal.id,
          {
            ...payload,
            status: draft.status,
          },
        );

      if (saved) {
        setEditor(null);
      }

      return;
    }

    mutation.current = true;

    setBusy(true);
    setError(null);
    setNotice(null);

    try {
      const created =
        await goalsService.createMine(
          goalWorkspaceId,
          {
            ...payload,
            ...(personal
              ? {}
              : {
                  owner_employee_id: employee!.id,
                }),
          },
        );

      setGoals(
        (current) => [
          created,
          ...current,
        ],
      );

      setSelectedId(created.id);
      setFilter("all");
      setSearch("");
      setEditor(null);

      setNotice(
        "Goal created successfully.",
      );
    } catch (cause) {
      setError(
        message(
          cause,
          "Unable to create goal.",
        ),
      );
    } finally {
      mutation.current = false;
      setBusy(false);
    }
  }

  async function removeGoal(
    goal: GoalPublic,
  ): Promise<void> {
    if (
      !workspaceId ||
      mutation.current ||
      loading
    ) {
      return;
    }

    const confirmed =
      window.confirm(
        `Delete goal "${goal.title}"? This cannot be undone.`,
      );

    if (!confirmed) {
      return;
    }

    mutation.current = true;

    setBusy(true);
    setError(null);
    setNotice(null);

    try {
      await goalsService.deleteMine(
        goalWorkspaceId,
        goal.id,
      );

      setGoals(
        (current) =>
          current.filter(
            (item) =>
              item.id !== goal.id,
          ),
      );

      setSelectedId(null);
      setNotice("Goal deleted.");
    } catch (cause) {
      setError(
        message(
          cause,
          "Unable to delete goal.",
        ),
      );
    } finally {
      mutation.current = false;
      setBusy(false);
    }
  }

  const blocked =
    loading || busy;

  return (
    <main
      className="wg"
      aria-busy={loading}
    >
      <div className="wg-crumb">
        {personal
          ? "Personal"
          : workspace?.name ?? "Workspace"}

        <span>/</span>

        Goals
      </div>

      <header className="wg-header">
        <div>
          <h1>My Goals</h1>

          <p>
            Turn your ambitions into
            milestones and steady
            progress.
          </p>
        </div>

        <div className="wg-actions">
          <button
            type="button"
            className="wg-icon"
            aria-label="Refresh goals"
            disabled={blocked}
            onClick={() => {
              void load();
            }}
          >
            <RefreshCcw size={16} />
          </button>

          <button
            type="button"
            className="wg-button wg-dark"
            disabled={
              blocked || (!personal && !employee)
            }
            onClick={() =>
              setEditor({
                kind: "create",
              })
            }
          >
            <Plus size={17} />

            New goal
          </button>
        </div>
      </header>

      {error && !editor ? (
        <div
          className="wg-alert wg-error"
          role="alert"
        >
          {error}
        </div>
      ) : null}

      {notice ? (
        <div
          className="wg-alert wg-success"
          role="status"
        >
          <CheckCircle2 size={16} />

          {notice}
        </div>
      ) : null}

      <section
        className="wg-summary"
        aria-label="Goal overview"
      >
        <Metric
          icon={<Target />}
          value={activeCount}
          label="Active goals"
        />

        <Metric
          icon={<CheckCircle2 />}
          value={completedCount}
          label="Completed goals"
        />

        <Metric
          icon={<Flag />}
          value="—"
          label="Milestones completed"
          hint="Milestone tracking is not connected yet."
        />

        <Gauge
          value={
            selectedGoal
              ? percent(
                  selectedGoal.progress_percent,
                )
              : averageProgress
          }
          label={
            selectedGoal
              ? `${selectedGoal.title} progress`
              : "Average goal progress"
          }
        />
      </section>

      <div className="wg-toolbar">
        <label className="wg-search">
          <Search size={17} />

          <input
            aria-label="Search goals"
            placeholder="Search goals"
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value,
              )
            }
          />
        </label>

        <div
          className="wg-filters"
          role="group"
          aria-label="Filter goals"
        >
          {(
            [
              "all",
              "active",
              "completed",
            ] as const
          ).map(
            (value) => (
              <button
                key={value}
                type="button"
                className={
                  `wg-pill ${
                    filter === value
                      ? "is-active"
                      : ""
                  }`
                }
                aria-pressed={
                  filter === value
                }
                onClick={() =>
                  setFilter(value)
                }
              >
                {value === "all"
                  ? "All goals"
                  : pretty(value)}
              </button>
            ),
          )}

          <select
            aria-label="Additional goal statuses"
            className="wg-extra-filter"
            value={
              filter === "cancelled" ||
              filter === "archived"
                ? filter
                : ""
            }
            onChange={(event) =>
              setFilter(
                event.target.value as
                  | GoalStatus
                  | "all",
              )
            }
          >
            <option
              value=""
              disabled
            >
              More statuses
            </option>

            <option value="all">
              All goals
            </option>

            <option value="cancelled">
              Cancelled
            </option>

            <option value="archived">
              Archived
            </option>
          </select>
        </div>
      </div>

      {!personal && !loading && !employee ? (
        <section className="wg-card wg-unlinked">
          <Target size={30} />

          <h2>
            Employee account not linked
          </h2>

          <p>
            Your current Goals API
            requires an employee linked
            to this workspace account.
          </p>

          <button
            type="button"
            className="wg-button"
            disabled={busy}
            onClick={() => {
              void load();
            }}
          >
            Check again
          </button>
        </section>
      ) : (
        <div className="wg-columns">
          <section
            className="wg-card wg-list"
            aria-label="My goals"
          >
            <div className="wg-card-heading">
              <h2>My goals</h2>

              <button
                type="button"
                className="wg-icon"
                aria-label="Create goal"
                disabled={
                  blocked || (!personal && !employee)
                }
                onClick={() =>
                  setEditor({
                    kind: "create",
                  })
                }
              >
                <Plus size={16} />
              </button>
            </div>

            {loading ? (
              <p
                className="wg-empty"
                role="status"
              >
                Loading your goals…
              </p>
            ) : visibleGoals.length ? (
              <div className="wg-goal-items">
                {visibleGoals.map(
                  (goal) => (
                    <button
                      key={goal.id}
                      type="button"
                      className={
                        `wg-goal ${
                          selectedGoal?.id ===
                          goal.id
                            ? "is-selected"
                            : ""
                        }`
                      }
                      aria-pressed={
                        selectedGoal?.id ===
                        goal.id
                      }
                      onClick={() =>
                        setSelectedId(
                          goal.id,
                        )
                      }
                    >
                      <Target
                        className="wg-goal-icon"
                        size={25}
                      />

                      <div className="wg-goal-content">
                        <div className="wg-goal-title">
                          <strong>
                            {goal.title}
                          </strong>

                          <Status
                            status={
                              goal.status
                            }
                          />
                        </div>

                        <div className="wg-progress-line">
                          <Progress
                            value={
                              goal.progress_percent
                            }
                            complete={
                              goal.status ===
                              "completed"
                            }
                          />

                          <span>
                            {percent(
                              goal.progress_percent,
                            )}
                            %
                          </span>
                        </div>

                        <div className="wg-date">
                          <CalendarDays
                            size={16}
                          />

                          Target:{" "}
                          {dateLabel(
                            goal.due_date,
                          )}
                        </div>
                      </div>
                    </button>
                  ),
                )}
              </div>
            ) : (
              <p className="wg-empty">
                {goals.length
                  ? "No goals match your filters."
                  : "Create your first goal to get started."}
              </p>
            )}
          </section>

          <div className="wg-center">
            {selectedGoal ? (
              <GoalDetail
                key={selectedGoal.id}
                goal={selectedGoal}
                busy={blocked}
                onEdit={() =>
                  setEditor({
                    kind: "edit",
                    goal: selectedGoal,
                  })
                }
                onUpdate={(
                  payload,
                ) =>
                  updateGoal(
                    selectedGoal.id,
                    payload,
                  )
                }
                onDelete={() => {
                  void removeGoal(
                    selectedGoal,
                  );
                }}
              />
            ) : (
              <section className="wg-card wg-no-selection">
                <Target size={32} />

                <h2>
                  {loading
                    ? "Loading goals"
                    : "Your next milestone starts here"}
                </h2>

                <p>
                  {loading
                    ? "Fetching your latest progress…"
                    : "Select a goal or create a new one to view its details."}
                </p>
              </section>
            )}

            <section className="wg-card wg-next">
              <div className="wg-card-heading">
                <h2>Next tasks</h2>

                <button
                  type="button"
                  className="wg-button"
                  disabled
                  title="Goal task endpoints are not available yet."
                >
                  <Plus size={15} />

                  Add task
                </button>
              </div>

              <p className="wg-empty wg-small-empty">
                Goal tasks are not
                connected yet.
              </p>
            </section>
          </div>

          <aside
            className="wg-right"
            aria-label="Goal support and details"
          >
            <section className="wg-card wg-assistance">
              <div className="wg-card-heading">
                <h2>AI assistance</h2>
              </div>

              <div className="wg-ai-copy">
                <Sparkles size={25} />

                <p>
                  AI goal planning will
                  appear here when the
                  AI assistance backend
                  is connected.
                </p>
              </div>

              <div className="wg-ai-actions">
                <button
                  type="button"
                  className="wg-pill"
                  disabled
                >
                  Suggest milestones
                </button>

                <button
                  type="button"
                  className="wg-pill"
                  disabled
                >
                  Plan next steps
                </button>
              </div>

              <button
                type="button"
                className="wg-button wg-dark wg-full"
                disabled
              >
                Apply suggestion
              </button>
            </section>

            <section className="wg-card wg-notes">
              <div className="wg-card-heading">
                <h2>Goal notes</h2>
              </div>

              <div className="wg-note-empty">
                <FileText size={24} />

                <div>
                  <strong>
                    No connected notes
                  </strong>

                  <p>
                    Goal notes need
                    backend support
                    before they can
                    be saved.
                  </p>
                </div>
              </div>

              <button
                type="button"
                className="wg-button wg-full"
                disabled
              >
                <Plus size={15} />

                Add note
              </button>
            </section>

            <section className="wg-card wg-details">
              <div className="wg-card-heading">
                <h2>Goal details</h2>
              </div>

              <dl>
                <div>
                  <dt>
                    <CalendarDays
                      size={17}
                    />

                    Created
                  </dt>

                  <dd>
                    {dateLabel(
                      selectedGoal?.created_at,
                    )}
                  </dd>
                </div>

                <div>
                  <dt>
                    <Eye size={17} />

                    Scope
                  </dt>

                  <dd>Workspace</dd>
                </div>

                <div>
                  <dt>
                    <Target size={17} />

                    Target date
                  </dt>

                  <dd>
                    {dateLabel(
                      selectedGoal?.due_date,
                    )}
                  </dd>
                </div>

                <div>
                  <dt>
                    <Flag size={17} />

                    Priority
                  </dt>

                  <dd>
                    {selectedGoal
                      ? pretty(
                          selectedGoal.priority,
                        )
                      : "—"}
                  </dd>
                </div>
              </dl>
            </section>
          </aside>
        </div>
      )}

      {editor ? (
        <GoalEditor
          editor={editor}
          busy={busy}
          error={error}
          onClose={() => {
            if (
              !mutation.current
            ) {
              setEditor(null);
              setError(null);
            }
          }}
          onSave={saveEditor}
        />
      ) : null}

      <style>{styles}</style>
    </main>
  );
}

function Metric({
  icon,
  value,
  label,
  hint,
}: {
  icon: ReactNode;
  value: number | string;
  label: string;
  hint?: string;
}) {
  return (
    <div
      className="wg-metric"
      title={hint}
    >
      {icon}

      <div>
        <strong>{value}</strong>

        <span>{label}</span>
      </div>
    </div>
  );
}

function Gauge({
  value,
  label,
}: {
  value: number;
  label: string;
}) {
  const progress =
    percent(value);

  const angle =
    (
      160 +
      progress * 2.2
    ) *
    Math.PI /
    180;

  return (
    <div
      className="wg-gauge"
      role="img"
      aria-label={
        `${label}: ${progress}%`
      }
    >
      <svg
        viewBox="0 0 260 175"
        aria-hidden="true"
      >
        <path
          className="wg-gauge-track"
          d="M 36.03 149.20 A 100 100 0 1 1 223.97 149.20"
          pathLength="100"
        />

        <path
          className="wg-gauge-fill"
          d="M 36.03 149.20 A 100 100 0 1 1 223.97 149.20"
          pathLength="100"
          strokeDasharray={
            `${progress} 100`
          }
        />

        {[
          0,
          20,
          40,
          60,
          80,
          100,
        ].map(
          (tick) => {
            const radians =
              (
                160 +
                tick * 2.2
              ) *
              Math.PI /
              180;

            return (
              <text
                key={tick}
                x={
                  130 +
                  121 *
                    Math.cos(
                      radians,
                    )
                }
                y={
                  119 +
                  121 *
                    Math.sin(
                      radians,
                    )
                }
                textAnchor="middle"
              >
                {tick}
              </text>
            );
          },
        )}

        <circle
          cx={
            130 +
            100 *
              Math.cos(angle)
          }
          cy={
            115 +
            100 *
              Math.sin(angle)
          }
          r="8.5"
        />

        <text
          className="wg-gauge-number"
          x="130"
          y="116"
          textAnchor="middle"
        >
          {progress}%
        </text>
      </svg>

      <span>{label}</span>
    </div>
  );
}

function Progress({
  value,
  complete = false,
}: {
  value: number;
  complete?: boolean;
}) {
  return (
    <div
      className={
        `wg-progress ${
          complete
            ? "is-complete"
            : ""
        }`
      }
      role="progressbar"
      aria-label="Goal progress"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={
        percent(value)
      }
    >
      <span
        style={{
          width:
            `${percent(value)}%`,
        }}
      />
    </div>
  );
}

function Status({
  status,
}: {
  status: GoalStatus;
}) {
  return (
    <span
      className={
        `wg-status ${
          status === "completed"
            ? "is-completed"
            : status === "active"
              ? "is-progress"
              : "is-muted"
        }`
      }
    >
      {status === "active"
        ? "In progress"
        : pretty(status)}
    </span>
  );
}

function GoalDetail({
  goal,
  busy,
  onEdit,
  onUpdate,
  onDelete,
}: {
  goal: GoalPublic;
  busy: boolean;
  onEdit: () => void;
  onUpdate: (
    payload: GoalUpdate,
  ) => Promise<boolean>;
  onDelete: () => void;
}) {
  const [tab, setTab] =
    useState<Tab>(
      "milestones",
    );

  const [progress, setProgress] =
    useState(
      percent(
        goal.progress_percent,
      ),
    );

  const [
    showProgress,
    setShowProgress,
  ] = useState(false);

  useEffect(
    () => {
      setProgress(
        percent(
          goal.progress_percent,
        ),
      );
    },
    [goal.progress_percent],
  );

  return (
    <section className="wg-card wg-main-detail">
      <div className="wg-detail-heading">
        <h2>{goal.title}</h2>

        <div className="wg-actions">
          <button
            type="button"
            className="wg-button"
            disabled={busy}
            onClick={onEdit}
          >
            <Pencil size={15} />

            Edit goal
          </button>

          <details className="wg-menu">
            <summary
              className="wg-icon"
              aria-label="Goal actions"
            >
              <MoreHorizontal
                size={18}
              />
            </summary>

            <div className="wg-menu-popover">
              <button
                type="button"
                disabled={
                  busy ||
                  goal.status ===
                    "completed"
                }
                onClick={() => {
                  void onUpdate({
                    status:
                      "completed",
                    progress_percent:
                      100,
                  });
                }}
              >
                <CheckCircle2
                  size={15}
                />

                Mark complete
              </button>

              <button
                type="button"
                disabled={
                  busy ||
                  goal.status ===
                    "archived"
                }
                onClick={() => {
                  void onUpdate({
                    status:
                      "archived",
                  });
                }}
              >
                <Archive size={15} />

                Archive goal
              </button>

              <button
                type="button"
                disabled={
                  busy ||
                  goal.status ===
                    "active"
                }
                onClick={() => {
                  void onUpdate({
                    status: "active",
                  });
                }}
              >
                <Target size={15} />

                Set active
              </button>

              <button
                type="button"
                className="wg-danger"
                disabled={busy}
                onClick={onDelete}
              >
                <Trash2 size={15} />

                Delete goal
              </button>
            </div>
          </details>
        </div>
      </div>

      <p className="wg-description">
        {goal.description ||
          "Add a description to define the result you want to achieve."}
      </p>

      <div className="wg-detail-overview">
        <div className="wg-target">
          <CalendarDays
            size={22}
          />

          <div>
            <span>
              Target date
            </span>

            <strong>
              {dateLabel(
                goal.due_date,
              )}
            </strong>
          </div>
        </div>

        <div className="wg-detail-progress">
          <span>Progress</span>

          <div className="wg-progress-line">
            <Progress
              value={
                goal.progress_percent
              }
              complete={
                goal.status ===
                "completed"
              }
            />

            <span>
              {percent(
                goal.progress_percent,
              )}
              %
            </span>
          </div>
        </div>

        <button
          type="button"
          className="wg-button wg-dark"
          disabled={busy}
          aria-expanded={
            showProgress
          }
          onClick={() =>
            setShowProgress(
              (current) =>
                !current,
            )
          }
        >
          Update progress
        </button>
      </div>

      {showProgress ? (
        <form
          className="wg-progress-editor"
          onSubmit={async (
            event,
          ) => {
            event.preventDefault();

            const saved =
              await onUpdate({
                progress_percent:
                  progress,
              });

            if (saved) {
              setShowProgress(
                false,
              );
            }
          }}
        >
          <label
            htmlFor="wg-progress-input"
          >
            Progress:{" "}
            <strong>
              {progress}%
            </strong>
          </label>

          <input
            id="wg-progress-input"
            type="range"
            min={0}
            max={100}
            step={1}
            value={progress}
            disabled={busy}
            onChange={(
              event,
            ) =>
              setProgress(
                Number(
                  event.target.value,
                ),
              )
            }
          />

          <button
            type="submit"
            className="wg-button wg-dark"
            disabled={
              busy ||
              progress ===
                percent(
                  goal.progress_percent,
                )
            }
          >
            Save progress
          </button>
        </form>
      ) : null}

      <div
        className="wg-tabs"
        role="tablist"
        aria-label="Goal sections"
      >
        {(
          [
            "milestones",
            "tasks",
            "notes",
          ] as const
        ).map(
          (value) => (
            <button
              key={value}
              id={
                `wg-tab-${value}`
              }
              type="button"
              role="tab"
              aria-selected={
                tab === value
              }
              aria-controls={
                `wg-panel-${value}`
              }
              onClick={() =>
                setTab(value)
              }
            >
              {pretty(value)}
            </button>
          ),
        )}
      </div>

      <div
        className="wg-tab-panel"
        id={`wg-panel-${tab}`}
        role="tabpanel"
        aria-labelledby={
          `wg-tab-${tab}`
        }
      >
        <div className="wg-feature-empty">
          {tab === "milestones" ? (
            <Flag size={25} />
          ) : tab === "tasks" ? (
            <CheckCircle2
              size={25}
            />
          ) : (
            <FileText size={25} />
          )}

          <strong>
            {pretty(tab)} are not
            connected yet
          </strong>

          <p>
            Your current Goals API
            does not include {tab}.
            Saved items will appear
            here after backend
            support is added.
          </p>
        </div>

        <button
          type="button"
          className="wg-button"
          disabled
        >
          <Plus size={15} />

          Add{" "}
          {tab === "milestones"
            ? "milestone"
            : tab === "tasks"
              ? "task"
              : "note"}
        </button>
      </div>
    </section>
  );
}

function GoalEditor({
  editor,
  busy,
  error,
  onClose,
  onSave,
}: {
  editor: Editor;
  busy: boolean;
  error: string | null;
  onClose: () => void;
  onSave: (
    draft: Draft,
  ) => Promise<void>;
}) {
  const goal =
    editor.kind === "edit"
      ? editor.goal
      : null;

  const [draft, setDraft] =
    useState<Draft>(
      () => ({
        title:
          goal?.title ?? "",

        description:
          goal?.description ?? "",

        priority:
          goal?.priority ??
          "medium",

        status:
          goal?.status ??
          "active",

        startDate:
          goal?.start_date ?? "",

        dueDate:
          goal?.due_date ?? "",
      }),
    );

  const [
    validation,
    setValidation,
  ] = useState<string | null>(
    null,
  );

  const dialog =
    useRef<HTMLDialogElement>(
      null,
    );

  useEffect(
    () => {
      const element =
        dialog.current;

      element?.showModal();

      const previous =
        document.body.style
          .overflow;

      document.body.style
        .overflow = "hidden";

      return () => {
        element?.close();

        document.body.style
          .overflow = previous;
      };
    },
    [],
  );

  function field<
    K extends keyof Draft,
  >(
    key: K,
    value: Draft[K],
  ) {
    setDraft(
      (current) => ({
        ...current,
        [key]: value,
      }),
    );

    setValidation(null);
  }

  async function submit(
    event: FormEvent<
      HTMLFormElement
    >,
  ) {
    event.preventDefault();

    if (busy) {
      return;
    }

    if (
      !draft.title.trim()
    ) {
      setValidation(
        "Enter a goal title.",
      );

      return;
    }

    if (
      draft.startDate &&
      draft.dueDate &&
      draft.startDate >
        draft.dueDate
    ) {
      setValidation(
        "Target date must be on or after the start date.",
      );

      return;
    }

    await onSave(draft);
  }

  return (
    <dialog
      ref={dialog}
      className="wg-dialog"
      aria-labelledby="wg-editor-title"
      onCancel={(event) => {
        event.preventDefault();

        if (!busy) {
          onClose();
        }
      }}
    >
      <form onSubmit={submit}>
        <div className="wg-editor-heading">
          <h2
            id="wg-editor-title"
          >
            {goal
              ? "Edit goal"
              : "New goal"}
          </h2>

          <button
            type="button"
            className="wg-icon"
            aria-label="Close goal editor"
            disabled={busy}
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </div>

        {validation || error ? (
          <div
            className="wg-alert wg-error"
            role="alert"
          >
            {validation || error}
          </div>
        ) : null}

        <fieldset
          disabled={busy}
        >
          <label>
            Goal title

            <input
              autoFocus
              required
              maxLength={200}
              value={draft.title}
              onChange={(
                event,
              ) =>
                field(
                  "title",
                  event.target.value,
                )
              }
            />
          </label>

          <label>
            Description

            <textarea
              rows={4}
              maxLength={10000}
              value={
                draft.description
              }
              onChange={(
                event,
              ) =>
                field(
                  "description",
                  event.target.value,
                )
              }
            />
          </label>

          <div className="wg-editor-grid">
            <label>
              Priority

              <select
                value={
                  draft.priority
                }
                onChange={(
                  event,
                ) =>
                  field(
                    "priority",
                    event.target
                      .value as
                      GoalPriority,
                  )
                }
              >
                <option value="low">
                  Low
                </option>

                <option value="medium">
                  Medium
                </option>

                <option value="high">
                  High
                </option>
              </select>
            </label>

            {goal ? (
              <label>
                Status

                <select
                  value={
                    draft.status
                  }
                  onChange={(
                    event,
                  ) =>
                    field(
                      "status",
                      event.target
                        .value as
                        GoalStatus,
                    )
                  }
                >
                  <option value="active">
                    Active
                  </option>

                  <option value="completed">
                    Completed
                  </option>

                  <option value="cancelled">
                    Cancelled
                  </option>

                  <option value="archived">
                    Archived
                  </option>
                </select>
              </label>
            ) : null}

            <label>
              Start date

              <input
                type="date"
                value={
                  draft.startDate
                }
                onChange={(
                  event,
                ) =>
                  field(
                    "startDate",
                    event.target.value,
                  )
                }
              />
            </label>

            <label>
              Target date

              <input
                type="date"
                min={
                  draft.startDate ||
                  undefined
                }
                value={
                  draft.dueDate
                }
                onChange={(
                  event,
                ) =>
                  field(
                    "dueDate",
                    event.target.value,
                  )
                }
              />
            </label>
          </div>
        </fieldset>

        <div className="wg-editor-footer">
          <button
            type="button"
            className="wg-button"
            disabled={busy}
            onClick={onClose}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="wg-button wg-dark"
            disabled={
              busy ||
              !draft.title.trim()
            }
          >
            {busy
              ? "Saving…"
              : goal
                ? "Save changes"
                : "Create goal"}
          </button>
        </div>
      </form>
    </dialog>
  );
}

const styles = `
.wg {
  --wg-ink: #11151b;
  --wg-muted: #596476;
  --wg-border: #ebe8e0;
  --wg-yellow: #ffcd32;

  width: 100%;
  min-width: 0;
  padding: 20px 16px 14px;

  color: var(--wg-ink);
  background:
    linear-gradient(
      115deg,
      #f8f6ef,
      #fbf9f3 65%,
      #faf4df
    );

  border-radius: 16px;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.4;
  isolation: isolate;
  color-scheme: light;
}

.wg *,
.wg *::before,
.wg *::after {
  box-sizing: border-box;
}

.wg h1,
.wg h2,
.wg p,
.wg dl,
.wg dd {
  margin: 0;
}

.wg button,
.wg input,
.wg select,
.wg textarea {
  font: inherit;
}

.wg button {
  cursor: pointer;
}

.wg button:disabled,
.wg fieldset:disabled {
  cursor: not-allowed;
}

.wg button:disabled {
  opacity: .48;
}

.wg button,
.wg input,
.wg select,
.wg textarea,
.wg summary {
  -webkit-tap-highlight-color:
    transparent;
}

.wg :focus-visible {
  outline: 2px solid #9a7000;
  outline-offset: 3px;
}

.wg ::selection {
  background: #ffe68c;
  color: #11151b;
}

.wg input,
.wg textarea {
  caret-color: #926500;
}

.wg-crumb {
  display: flex;
  gap: 12px;
  color: #69717b;
  font-size: 12px;
  margin: 0 6px 20px;
}

.wg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin: 0 6px 18px;
}

.wg-header h1 {
  font-size: 34px;
  line-height: 1.12;
  font-weight: 500;
  letter-spacing: -.025em;
}

.wg-header p {
  margin-top: 5px;
  color: #6c7179;
  font-size: 15px;
}

.wg-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.wg-button,
.wg-icon,
.wg-pill,
.wg-extra-filter {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;

  min-height: 32px;
  border: 1px solid #dedbd4;
  border-radius: 11px;

  background: #fcfbf8;
  color: #172132;
  padding: 6px 13px;
  text-decoration: none;
}

.wg-button:hover:not(:disabled),
.wg-icon:hover:not(:disabled),
.wg-pill:hover:not(:disabled) {
  background: #f3f0e7;
}

.wg-icon {
  width: 32px;
  padding: 0;
  flex-shrink: 0;
}

.wg-dark {
  background:
    linear-gradient(
      #303030,
      #232323
    );

  color: #fff;
  border-color: #262626;
}

.wg-dark:hover:not(:disabled) {
  background: #3a3a3a;
}

.wg-header .wg-dark {
  min-height: 42px;
  padding-inline: 17px;
}

.wg-full {
  width: 100%;
}

.wg-summary {
  display: grid;

  grid-template-columns:
    1fr
    1fr
    1.08fr
    1.45fr;

  align-items: center;
  min-height: 118px;
  border: 1px solid #eee6ce;
  border-radius: 13px;

  background:
    linear-gradient(
      105deg,
      #f9f6ed,
      #faf5e3
    );

  margin-bottom: 11px;
}

.wg-metric {
  display: flex;
  align-items: center;
  gap: 22px;
  min-height: 62px;
  padding: 0 30px;
  border-right:
    1px solid #e9e4d7;
}

.wg-metric > svg {
  width: 27px;
  height: 27px;
  stroke-width: 1.6;
  color: #515c68;
  flex-shrink: 0;
}

.wg-metric strong {
  display: block;
  font-size: 29px;
  line-height: 1.15;
  font-weight: 500;
  font-variant-numeric:
    tabular-nums;
}

.wg-metric span {
  display: block;
  color: #606a77;
  font-size: 14px;
  margin-top: 2px;
  white-space: nowrap;
}

.wg-gauge {
  position: relative;
  width: 260px;
  max-width: 100%;
  height: 118px;
  justify-self: center;
}

.wg-gauge svg {
  position: absolute;
  width: 100%;
  height: 175px;
  bottom: -9px;
  left: 0;
  overflow: visible;
}

.wg-gauge path {
  fill: none;
  stroke-width: 11px;
  stroke-linecap: round;
}

.wg-gauge-track {
  stroke: #fff;
}

.wg-gauge-fill {
  stroke: var(--wg-yellow);
}

.wg-gauge circle {
  fill: #fffdf5;
  stroke: #ffc000;
  stroke-width: 4px;
}

.wg-gauge text {
  fill: #777d80;
  font-size: 11px;
  font-family: inherit;
}

.wg-gauge .wg-gauge-number {
  fill: #11151b;
  font-size: 29px;
  font-weight: 500;
}

.wg-gauge > span {
  position: absolute;
  left: 15%;
  right: 15%;
  bottom: 20px;
  text-align: center;
  color: #717777;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wg-toolbar {
  display: flex;
  align-items: center;
  gap: 13px;
  margin-bottom: 9px;
  flex-wrap: wrap;
}

.wg-search {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 326px;
  max-width: 100%;
  height: 35px;

  border: 1px solid #e3dfd7;
  border-radius: 11px;
  padding: 0 13px;
  background: #ffffffa8;
  color: #667080;
}

.wg-search input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--wg-ink);
}

.wg-search:focus-within {
  outline: 2px solid #9a7000;
  outline-offset: 2px;
}

.wg-search input::placeholder {
  color: #697384;
  opacity: 1;
}

.wg-filters {
  display: flex;
  align-items: center;
  gap: 9px;
  flex-wrap: wrap;
}

.wg-pill {
  border-radius: 999px;
  padding: 5px 19px;
  min-height: 32px;
  white-space: nowrap;
}

.wg-pill.is-active {
  background: #282828;
  color: #fff;
  border-color: #282828;
}

.wg-pill.is-active:hover {
  background: #3a3a3a;
}

.wg-extra-filter {
  max-width: 145px;
  font-size: 12px;
}

.wg-columns {
  display: grid;

  grid-template-columns:
    minmax(245px, 1.02fr)
    minmax(410px, 1.66fr)
    minmax(260px, 1fr);

  gap: 10px;
  align-items: start;
}

.wg-card {
  min-width: 0;
  background: #ffffffb8;
  border:
    1px solid var(--wg-border);
  border-radius: 12px;
}

.wg-card-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 43px;
}

.wg-card h2 {
  font-size: 16px;
  font-weight: 550;
  letter-spacing: -.02em;
}

.wg-list {
  align-self: stretch;
  min-height: 563px;
  padding: 6px 6px 16px;
}

.wg-list > .wg-card-heading {
  padding: 0 10px 3px;
}

.wg-goal-items {
  max-height: 660px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color:
    #c8c2b6 transparent;
}

.wg-goal {
  display: flex;
  gap: 17px;
  width: 100%;

  border:
    1px solid transparent;

  background: transparent;
  color: var(--wg-ink);
  text-align: left;
  padding: 17px 15px 18px;
  border-radius: 9px;
  position: relative;
}

.wg-goal:not(:last-child)::after {
  content: "";
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 0;
  height: 1px;
  background: #eeece6;
}

.wg-goal:hover {
  background: #faf7ed;
}

.wg-goal.is-selected {
  background: #fff9df;
  border-color: #fff0b2;
}

.wg-goal.is-selected::after {
  display: none;
}

.wg-goal-icon {
  margin-top: 4px;
  color: #505d71;
  stroke-width: 1.65;
  flex-shrink: 0;
}

.wg-goal-content {
  flex: 1;
  min-width: 0;
}

.wg-goal-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.wg-goal-title strong {
  font-size: 15px;
  font-weight: 550;
  overflow-wrap: anywhere;
}

.wg-status {
  flex-shrink: 0;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  line-height: 1.55;
  white-space: nowrap;
}

.wg-status.is-progress {
  color: #795300;
  background: #fff0b6;
}

.wg-status.is-completed {
  color: #087a3c;
  background: #def7e5;
}

.wg-status.is-muted {
  color: #526071;
  background: #edf0f4;
}

.wg-progress-line {
  display: flex;
  align-items: center;
  gap: 10px;
  font-variant-numeric:
    tabular-nums;
}

.wg-progress-line > span {
  min-width: 37px;
  font-size: 13px;
}

.wg-progress {
  flex: 1;
  min-width: 40px;
  height: 9px;
  background: #e6e6e6;
  border-radius: 999px;
  overflow: hidden;
}

.wg-progress > span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #ffce35;
}

.wg-progress.is-complete > span {
  background: #50c66d;
}

.wg-date {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--wg-muted);
  font-size: 12px;
  margin-top: 11px;
}

.wg-center,
.wg-right {
  display: grid;
  gap: 9px;
  min-width: 0;
}

.wg-main-detail {
  padding: 14px 15px 12px;
}

.wg-detail-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.wg-detail-heading h2 {
  font-size: 21px;
  font-weight: 500;
  overflow-wrap: anywhere;
}

.wg-description {
  color: var(--wg-muted);
  max-width: 64ch;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 5px !important;
  min-height: 36px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.wg-detail-overview {
  display: flex;
  align-items: center;
  gap: 13px;
  margin: 13px 0 16px;
}

.wg-target {
  display: flex;
  align-items: center;
  gap: 12px;
  border-right:
    1px solid #edeae3;
  padding-right: 15px;
  flex-shrink: 0;
}

.wg-target > svg {
  color: #526071;
  stroke-width: 1.65;
}

.wg-target span,
.wg-detail-progress > span {
  display: block;
  font-size: 11px;
  color: var(--wg-muted);
  margin-bottom: 3px;
}

.wg-target strong {
  font-size: 13px;
  font-weight: 450;
  white-space: nowrap;
}

.wg-detail-progress {
  flex: 1;
  min-width: 90px;
}

.wg-detail-progress .wg-progress {
  height: 8px;
}

.wg-detail-overview > button {
  flex-shrink: 0;
  font-size: 12px;
  padding-inline: 12px;
}

.wg-tabs {
  display: flex;
  gap: 17px;
  border-bottom:
    1px solid #eeece5;
}

.wg-tabs button {
  border: 0;
  background: none;
  color: #576277;
  padding: 8px 10px 10px;
  position: relative;
}

.wg-tabs button[aria-selected="true"] {
  color: #10151b;
  font-weight: 550;
}

.wg-tabs button[aria-selected="true"]::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 3px;
  border-radius: 2px;
  background: #ffc700;
}

.wg-tab-panel {
  padding-top: 9px;
}

.wg-feature-empty {
  min-height: 181px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 8px;
  border: 1px solid #eeece7;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 8px;
  color: #5b6471;
}

.wg-feature-empty strong {
  font-weight: 500;
  color: #303a47;
}

.wg-feature-empty p {
  max-width: 37ch;
  font-size: 12px;
  line-height: 1.55;
}

.wg-next {
  padding: 0 15px 10px;
}

.wg-next .wg-card-heading {
  min-height: 43px;
  border-bottom:
    1px solid #eeece6;
}

.wg-empty {
  padding: 35px 18px;
  text-align: center;
  color: var(--wg-muted);
  font-size: 13px;
  line-height: 1.6;
}

.wg-small-empty {
  padding: 21px 8px;
  font-size: 12px;
}

.wg-assistance,
.wg-notes,
.wg-details {
  padding: 0 13px 13px;
}

.wg-ai-copy {
  display: flex;
  gap: 12px;
  padding: 14px 12px;
  background: #fdf4dc;
  border: 1px solid #fbefc9;
  border-radius: 9px;
  min-height: 81px;
}

.wg-ai-copy svg {
  color: #e5a600;
  flex-shrink: 0;
}

.wg-ai-copy p {
  font-size: 12px;
  line-height: 1.5;
}

.wg-ai-actions {
  display: grid;
  grid-template-columns:
    1fr 1fr;
  gap: 9px;
  margin: 8px 0;
}

.wg-ai-actions .wg-pill {
  padding: 5px 6px;
  font-size: 11px;
}

.wg-note-empty {
  display: flex;
  align-items: flex-start;
  gap: 17px;
  padding: 7px 8px 13px;
  min-height: 107px;
}

.wg-note-empty > svg {
  color: #4f5c70;
  flex-shrink: 0;
  margin-top: 5px;
}

.wg-note-empty strong {
  font-size: 12px;
  font-weight: 550;
}

.wg-note-empty p {
  color: var(--wg-muted);
  font-size: 12px;
  line-height: 1.5;
  margin-top: 5px;
}

.wg-details dl {
  display: grid;
  gap: 10px;
  padding: 3px 6px 0;
}

.wg-details dl > div {
  display: grid;
  grid-template-columns:
    1fr 1fr;
  gap: 9px;
  font-size: 12px;
}

.wg-details dt {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--wg-muted);
}

.wg-details dd {
  overflow-wrap: anywhere;
}

.wg-menu {
  position: relative;
}

.wg-menu summary {
  list-style: none;
  cursor: pointer;
}

.wg-menu summary::-webkit-details-marker {
  display: none;
}

.wg-menu-popover {
  position: absolute;
  right: 0;
  top: 38px;
  z-index: 5;
  width: 175px;
  padding: 5px;
  border: 1px solid #e5e0d5;
  border-radius: 10px;
  background: #fffefa;
  box-shadow:
    0 9px 25px #29251c1a;
}

.wg-menu-popover button {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 9px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  text-align: left;
  font-size: 12px;
}

.wg-menu-popover button:hover:not(:disabled) {
  background: #f7f1e4;
}

.wg-menu-popover .wg-danger {
  color: #b42f2f;
}

.wg-progress-editor {
  display: grid;
  grid-template-columns:
    1fr auto;
  align-items: center;
  gap: 10px;
  padding: 12px;
  margin-bottom: 12px;
  border-radius: 9px;
  background: #fff8e2;
}

.wg-progress-editor label {
  grid-column: 1 / -1;
}

.wg-progress-editor input {
  width: 100%;
  accent-color: #bb8700;
}

.wg-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 13px;
  border-radius: 9px;
  margin-bottom: 12px;
  font-size: 13px;
  overflow-wrap: anywhere;
}

.wg-error {
  color: #9d2222;
  background: #fff0ee;
  border: 1px solid #f0c9c4;
}

.wg-success {
  color: #136935;
  background: #edfaef;
  border: 1px solid #d0ead6;
}

.wg-unlinked,
.wg-no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
  text-align: center;
  padding: 35px 20px;
  min-height: 330px;
}

.wg-unlinked p,
.wg-no-selection p {
  max-width: 45ch;
  color: var(--wg-muted);
}

.wg-dialog {
  width:
    min(
      540px,
      calc(100vw - 32px)
    );

  max-height:
    calc(100dvh - 40px);

  padding: 20px;
  margin: auto;
  border: 1px solid #e8e2d5;
  border-radius: 15px;
  background: #fdfbf5;
  color: #11151b;
  overflow: auto;
  box-shadow:
    0 20px 70px #15120b33;
}

.wg-dialog::backdrop {
  background: #252b355e;
}

.wg-editor-heading,
.wg-editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.wg-editor-heading {
  margin-bottom: 18px;
}

.wg-editor-heading h2 {
  font-size: 21px;
  font-weight: 550;
}

.wg-editor-footer {
  justify-content: flex-end;
  margin-top: 18px;
}

.wg-dialog fieldset {
  border: 0;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 13px;
  min-width: 0;
}

.wg-dialog label {
  display: grid;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
}

.wg-dialog input,
.wg-dialog textarea,
.wg-dialog select {
  width: 100%;
  min-width: 0;
  min-height: 38px;
  padding: 8px 10px;
  border: 1px solid #dcd7cc;
  border-radius: 8px;
  background: #fffefb;
  color: #172132;
  font-size: 14px;
}

.wg-dialog textarea {
  resize: vertical;
}

.wg-editor-grid {
  display: grid;
  grid-template-columns:
    1fr 1fr;
  gap: 13px;
}

@media (min-width: 1500px) {
  .wg-columns {
    grid-template-columns:
      minmax(280px, 1.02fr)
      minmax(460px, 1.66fr)
      minmax(285px, 1fr);
  }
}

@media (max-width: 1200px) {
  .wg-columns {
    grid-template-columns:
      minmax(240px, .9fr)
      minmax(0, 1.6fr);
  }

  .wg-right {
    grid-column: 1 / -1;

    grid-template-columns:
      1fr 1fr 1fr;

    align-items: start;
  }

  .wg-metric {
    padding-inline: 17px;
    gap: 13px;
  }

  .wg-metric span {
    font-size: 12px;
  }

  .wg-detail-overview {
    flex-wrap: wrap;
  }

  .wg-gauge {
    width: 230px;
  }
}

@media (max-width: 900px) {
  .wg {
    padding: 16px 12px;
  }

  .wg-summary {
    grid-template-columns:
      1fr 1fr;

    padding: 12px 0;
    row-gap: 15px;
  }

  .wg-metric:nth-child(2) {
    border-right: 0;
  }

  .wg-gauge {
    height: 130px;
  }

  .wg-columns {
    grid-template-columns:
      minmax(215px, .85fr)
      minmax(0, 1.3fr);
  }

  .wg-goal {
    gap: 10px;
    padding-inline: 9px;
  }

  .wg-goal-title {
    flex-wrap: wrap;
    gap: 5px;
  }

  .wg-right {
    grid-template-columns:
      1fr 1fr;
  }

  .wg-details {
    grid-column: 1 / -1;
  }

  .wg-detail-heading {
    flex-wrap: wrap;
  }
}

@media (max-width: 650px) {
  .wg-header {
    align-items: flex-start;
    flex-wrap: wrap;
    margin-inline: 0;
  }

  .wg-header h1 {
    font-size: 28px;
  }

  .wg-header p {
    font-size: 13px;
  }

  .wg-crumb {
    margin-left: 0;
    margin-bottom: 14px;
  }

  .wg-toolbar {
    gap: 9px;
  }

  .wg-search {
    width: 100%;
  }

  .wg-filters {
    gap: 6px;
  }

  .wg-pill {
    padding-inline: 13px;
    font-size: 12px;
  }

  .wg-extra-filter {
    max-width: 132px;
  }

  .wg-columns {
    grid-template-columns:
      minmax(0, 1fr);
  }

  .wg-list {
    min-height: 0;
  }

  .wg-goal-items {
    max-height: 335px;
  }

  .wg-goal-title {
    flex-wrap: nowrap;
  }

  .wg-right {
    grid-column: auto;

    grid-template-columns:
      minmax(0, 1fr);
  }

  .wg-details {
    grid-column: auto;
  }

  .wg-summary {
    gap: 10px 0;
  }

  .wg-metric {
    padding-inline: 13px;
    gap: 10px;
  }

  .wg-metric > svg {
    width: 22px;
    height: 22px;
  }

  .wg-metric strong {
    font-size: 25px;
  }

  .wg-metric span {
    white-space: normal;
    font-size: 11px;
  }

  .wg-gauge {
    width: 180px;
    height: 118px;
  }

  .wg-gauge svg {
    height: 140px;
    bottom: 0;
  }

  .wg-gauge > span {
    font-size: 10px;
    bottom: 24px;
  }

  .wg-main-detail {
    padding-inline: 12px;
  }

  .wg-detail-progress {
    min-width: 110px;
  }

  .wg-detail-overview > button {
    width: 100%;
  }

  .wg-editor-grid {
    grid-template-columns:
      1fr;
  }
}
`;