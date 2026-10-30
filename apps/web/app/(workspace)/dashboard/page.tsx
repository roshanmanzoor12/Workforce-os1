"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  Activity,
  ArrowRight,
  BarChart3,
  Building2,
  CalendarDays,
  Check,
  ChevronRight,
  Clock3,
  FileText,
  Folder,
  Laptop2,
  Megaphone,
  Monitor,
  Plane,
  Plus,
  RefreshCcw,
  ShieldCheck,
  TriangleAlert,
  UserPlus,
  Users,
  Wallet,
} from "lucide-react";

import { useRouter } from "next/navigation";
import { InviteMembersButton } from "@/components/workspace/invite-members-button";
import { ManagerDashboard } from "@/components/dashboard/manager-dashboard";
import { MemberDashboard } from "@/components/dashboard/member-dashboard";
import { getWorkspaceTemplate } from "@/lib/workspace/templates";

import {
  WorkspaceRequired,
} from "@/components/workspace/workspace-required";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  departmentsService,
  type Department,
} from "@/services/departments.service";

import {
  devicesService,
  type Device,
} from "@/services/devices.service";

import {
  teamsService,
  type Team,
} from "@/services/teams.service";

import {
  employeesService,
  type Employee,
  type EmploymentStatus,
} from "@/services/employees.service";


type LoadState =
  | "loading"
  | "ready"
  | "error";

type DashboardErrors = {
  employees?: string;
  departments?: string;
  devices?: string;
  teams?: string;
};


function errorMessage(
  cause: unknown,
  fallback: string,
): string {
  return cause instanceof Error
    ? cause.message
    : fallback;
}


function formatDate(
  value: Date,
): string {
  return new Intl.DateTimeFormat(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  ).format(value);
}


function initials(
  employee: Employee,
): string {
  const first =
    employee.first_name?.trim().charAt(0) ?? "";

  const last =
    employee.last_name?.trim().charAt(0) ?? "";

  return (
    `${first}${last}`.toUpperCase() ||
    employee.full_name?.trim().charAt(0).toUpperCase() ||
    "?"
  );
}


export default function DashboardPage() {
  return (
    <WorkspaceRequired>
      <RoleSpecificDashboard />
    </WorkspaceRequired>
  );
}

function RoleSpecificDashboard() {
  const {
    workspaceId,
    workspaceLoading,
    workspaceBootstrap,
    membership,
    effectiveNavigationView,
  } = useWorkspace();

  // Wait until the selected workspace's actual role has loaded.
  // Never show the owner dashboard as a fallback for an unknown membership.
  if (!workspaceId || !membership || workspaceLoading || !workspaceBootstrap) {
    return (
      <main role="status" aria-live="polite" style={{ padding: 24 }}>
        Loading your workspace access…
      </main>
    );
  }

  if (effectiveNavigationView === "member") return <MemberDashboard />;
  if (effectiveNavigationView === "client") return <MemberDashboard client />;
  if (effectiveNavigationView === "manager") return <ManagerDashboard />;

  // Admin and owner have the company overview, with backend APIs still
  // responsible for permission and data-scope enforcement.
  return <DashboardContent />;
}


function DashboardContent() {
  const router = useRouter();

  const {
    workspaceId,
    workspace,
    membership,
    canManage,
  } = useWorkspace();

  const words = getWorkspaceTemplate(workspace?.workspace_type);

  const [employees, setEmployees] =
    useState<Employee[]>([]);

  const [departments, setDepartments] =
    useState<Department[]>([]);

  const [devices, setDevices] =
    useState<Device[]>([]);

  const [teams, setTeams] =
    useState<Team[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [states, setStates] =
    useState<Record<keyof DashboardErrors, LoadState>>({
      employees: "loading",
      departments: "loading",
      devices: "loading",
      teams: "loading",
    });

  const [errors, setErrors] =
    useState<DashboardErrors>({});

  const [updatedAt, setUpdatedAt] =
    useState<Date | null>(null);

  const [today, setToday] =
    useState<Date | null>(null);

  const requestId = useRef(0);

  useEffect(() => {
    setToday(new Date());
  }, []);

  const loadDashboard = useCallback(
    async (clearPrevious = false) => {
      if (!workspaceId) {
        return;
      }

      const currentRequest =
        ++requestId.current;

      setLoading(true);
      setErrors({});

      if (clearPrevious) {
        setEmployees([]);
        setDepartments([]);
        setDevices([]);
        setTeams([]);
        setUpdatedAt(null);

        setStates({
          employees: "loading",
          departments: "loading",
          devices: "loading",
          teams: "loading",
        });
      }

      const [
        employeeResult,
        departmentResult,
        deviceResult,
        teamResult,
      ] = await Promise.allSettled([
        employeesService.list(workspaceId),
        departmentsService.list(workspaceId),
        devicesService.list(workspaceId),
        teamsService.list(workspaceId),
      ]);

      if (
        currentRequest !==
        requestId.current
      ) {
        return;
      }

      const nextErrors: DashboardErrors = {};

      const nextStates: Record<
        keyof DashboardErrors,
        LoadState
      > = {
        employees: "ready",
        departments: "ready",
        devices: "ready",
        teams: "ready",
      };

      if (
        employeeResult.status ===
        "fulfilled"
      ) {
        setEmployees(
          employeeResult.value.employees,
        );
      } else {
        setEmployees([]);

        nextStates.employees =
          "error";

        nextErrors.employees =
          errorMessage(
            employeeResult.reason,
            "Employees could not be loaded.",
          );
      }

      if (
        departmentResult.status ===
        "fulfilled"
      ) {
        setDepartments(
          departmentResult.value.departments,
        );
      } else {
        setDepartments([]);

        nextStates.departments =
          "error";

        nextErrors.departments =
          errorMessage(
            departmentResult.reason,
            "Departments could not be loaded.",
          );
      }

      if (
        deviceResult.status ===
        "fulfilled"
      ) {
        setDevices(
          deviceResult.value.devices,
        );
      } else {
        setDevices([]);

        nextStates.devices =
          "error";

        nextErrors.devices =
          errorMessage(
            deviceResult.reason,
            "Devices could not be loaded.",
          );
      }

      if (teamResult.status === "fulfilled") {
        setTeams(teamResult.value.teams);
      } else {
        setTeams([]);
        nextStates.teams = "error";
        nextErrors.teams = errorMessage(
          teamResult.reason,
          "Teams could not be loaded.",
        );
      }

      setStates(nextStates);
      setErrors(nextErrors);

      if (
        Object.keys(nextErrors).length <
        4
      ) {
        setUpdatedAt(new Date());
      }

      setLoading(false);
    },
    [workspaceId],
  );

  useEffect(() => {
    void loadDashboard(true);

    return () => {
      requestId.current += 1;
    };
  }, [loadDashboard]);

  const activeEmployees = useMemo(
    () =>
      employees.filter(
        (employee) =>
          employee.employment_status ===
            "active" &&
          employee.is_active,
      ),
    [employees],
  );

  const employeesOnLeave = useMemo(
    () =>
      employees.filter(
        (employee) =>
          employee.employment_status ===
          "on_leave",
      ),
    [employees],
  );

  const activeDevices = useMemo(
    () =>
      devices.filter(
        (device) =>
          device.status === "active" &&
          device.is_active,
      ),
    [devices],
  );

  const assignedDevices = useMemo(
    () =>
      devices.filter(
        (device) =>
          Boolean(device.employee_id),
      ),
    [devices],
  );

  const departmentNames = useMemo(
    () =>
      new Map(
        departments.map(
          (department) => [
            department.id,
            department.name,
          ],
        ),
      ),
    [departments],
  );

  const quickEmployees =
    employees.slice(0, 6);

  const weekDays = useMemo(() => {
    if (!today) {
      return [];
    }

    const monday =
      new Date(today);

    monday.setHours(12, 0, 0, 0);

    const dayOffset =
      (monday.getDay() + 6) % 7;

    monday.setDate(
      monday.getDate() -
        dayOffset,
    );

    return Array.from(
      { length: 5 },
      (_, index) => {
        const date =
          new Date(monday);

        date.setDate(
          monday.getDate() +
            index,
        );

        return {
          key:
            date.toISOString(),
          day:
            new Intl.DateTimeFormat(
              "en-GB",
              { weekday: "short" },
            ).format(date),
          date:
            new Intl.DateTimeFormat(
              "en-GB",
              {
                day: "numeric",
                month: "short",
              },
            ).format(date),
        };
      },
    );
  }, [today]);

  function metricValue(
    source: keyof DashboardErrors,
    value: number,
  ): number | string {
    return states[source] ===
      "ready"
      ? value
      : "—";
  }

  const loadedSourceCount =
    Object.values(states).filter(
      (state) =>
        state === "ready",
    ).length;

  return (
    <main
      className="wh-home"
      aria-labelledby="wh-page-title"
      aria-busy={loading}
    >
      <header className="wh-heading">
        <div>
          <h1 id="wh-page-title">
            {words.home}
          </h1>

          <p>
            {workspace?.workspace_type === "agency"
              ? "Your agency, client delivery and people at a glance."
              : "Your company, people and work at a glance."}
          </p>
        </div>

        <div className="wh-heading-actions">
          <span className="wh-date">
            <CalendarDays size={17} />

            {today
              ? formatDate(today)
              : "Today"}
          </span>

          <button
            type="button"
            className="wh-button wh-button-light"
            onClick={() =>
              void loadDashboard()
            }
            disabled={loading}
            aria-label="Refresh dashboard"
          >
            <RefreshCcw
              size={15}
              className={
                loading
                  ? "wh-spinning"
                  : undefined
              }
            />

            {loading
              ? "Refreshing"
              : "Refresh"}
          </button>

          <button
            type="button"
            className="wh-button wh-button-outline"
            onClick={() =>
              router.push("/reports")
            }
          >
            <BarChart3 size={16} />

            View reports
          </button>

          <InviteMembersButton />
        </div>
      </header>

      {Object.keys(errors).length >
      0 ? (
        <section
          className="wh-error"
          role="alert"
        >
          <TriangleAlert size={18} />

          <div>
            <strong>
              Some workspace data could
              not be loaded.
            </strong>

            {Object.entries(errors).map(
              ([source, message]) => (
                <p key={source}>
                  {message}
                </p>
              ),
            )}
          </div>

          <button
            type="button"
            className="wh-button wh-button-outline"
            disabled={loading}
            onClick={() =>
              void loadDashboard()
            }
          >
            Try again
          </button>
        </section>
      ) : null}

      <section
        className="wh-summary"
        aria-label="Workspace summary"
      >
        <SummaryMetric
          icon={<Users />}
          value={metricValue(
            "employees",
            employees.length,
          )}
          label={workspace?.workspace_type === "agency" ? "Agency team members" : "Total employees"}
        />

        <SummaryMetric
          icon={<Users />}
          value={metricValue(
            "employees",
            activeEmployees.length,
          )}
          label="Active employees"
          dot="green"
        />

        <SummaryMetric
          icon={<Laptop2 />}
          value={metricValue(
            "devices",
            devices.length,
          )}
          label="Registered devices"
        />

        <SummaryMetric
          icon={<CalendarDays />}
          value={metricValue(
            "employees",
            employeesOnLeave.length,
          )}
          label="On leave"
          dot="yellow"
        />

        <SummaryMetric
          icon={<Building2 />}
          value={metricValue(
            "departments",
            departments.length,
          )}
          label={words.departments}
        />
      </section>

      <div className="wh-primary-grid">
        <section className="wh-card wh-attendance">
          <CardHeader
            icon={<CalendarDays />}
            title="Attendance overview"
            action={
              <TextAction
                onClick={() =>
                  router.push(
                    "/attendance",
                  )
                }
              >
                View attendance
              </TextAction>
            }
          />

          <div
            className="wh-legend"
            aria-label="Attendance categories"
          >
            <LegendItem
              tone="present"
              label="Present"
              value="—"
            />

            <LegendItem
              tone="late"
              label="Late"
              value="—"
            />

            <LegendItem
              tone="absent"
              label="Absent"
              value="—"
            />

            <LegendItem
              tone="leave"
              label="On leave"
              value={metricValue(
                "employees",
                employeesOnLeave.length,
              )}
            />
          </div>

          <div
            className="wh-chart"
            role="img"
            aria-label="Attendance chart. Daily attendance data is not connected."
          >
            <div
              className="wh-chart-grid"
              aria-hidden="true"
            >
              {[0, 1, 2, 3, 4].map(
                (line) => (
                  <span
                    key={line}
                    className="wh-chart-line"
                  />
                ),
              )}
            </div>

            <div className="wh-chart-message">
              <CalendarDays size={26} />

              <strong>
                Daily attendance is not
                available yet
              </strong>

              <span>
                Attendance records will
                appear here when connected.
              </span>
            </div>

            <div
              className="wh-chart-days"
              aria-hidden="true"
            >
              {weekDays.map(
                (day) => (
                  <div key={day.key}>
                    <strong>
                      {day.day}
                    </strong>

                    <span>
                      {day.date}
                    </span>
                  </div>
                ),
              )}
            </div>
          </div>
        </section>

        <div className="wh-right-stack">
          <section className="wh-card wh-approvals">
            <CardHeader
              icon={<Clock3 />}
              title="Approvals"
            />

            <div className="wh-approval-list">
              <ApprovalRow
                icon={<Plane />}
                label="Leave requests"
              />

              <ApprovalRow
                icon={<FileText />}
                label="Payroll run"
                onOpen={() =>
                  router.push("/payroll")
                }
              />

              <ApprovalRow
                icon={<Users />}
                label="Onboarding"
                onOpen={() =>
                  router.push(
                    "/employees",
                  )
                }
              />
            </div>

            <p className="wh-footnote">
              Approval counts are not
              connected.
            </p>
          </section>

          <section className="wh-card wh-meetings">
            <CardHeader
              icon={<CalendarDays />}
              title="Upcoming meetings"
              action={
                <TextAction
                  onClick={() =>
                    router.push(
                      "/meetings",
                    )
                  }
                >
                  View all
                </TextAction>
              }
            />

            <EmptyState
              compact
              icon={<CalendarDays />}
              title="Meeting schedule unavailable"
              description="Open meetings to view your schedule."
            />
          </section>
        </div>
      </div>

      <div className="wh-secondary-grid">
        <section className="wh-card wh-projects">
          <CardHeader
            icon={<Folder />}
            title="Active projects"
          />

          <div className="wh-table-scroll">
            <table className="wh-table wh-project-table">
              <thead>
                <tr>
                  <th scope="col">
                    Project
                  </th>

                  <th scope="col">
                    Department
                  </th>

                  <th scope="col">
                    Progress
                  </th>

                  <th scope="col">
                    Due date
                  </th>
                </tr>
              </thead>

              <tbody>
                <tr>
                  <td
                    colSpan={4}
                    className="wh-table-empty"
                  >
                    Project data is not
                    connected.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className="wh-card wh-people">
          <CardHeader
            icon={<Users />}
            title="People & teams"
          />

          <div className="wh-people-stats">
            <div>
              <span className="wh-icon-circle">
                <Building2 size={25} />
              </span>

              <div>
                <strong>
                  {metricValue(
                    "departments",
                    departments.length,
                  )}
                </strong>

                <span>
                  Departments
                </span>
              </div>
            </div>

            <div>
              <span className="wh-icon-circle">
                <Users size={25} />
              </span>

              <div>
                <strong>{metricValue("teams", teams.length)}</strong>

                <span>
                  Teams
                </span>
              </div>
            </div>
          </div>

          <div className="wh-card-footer">
            <TextAction
              onClick={() =>
                router.push(
                  "/employees",
                )
              }
            >
              Employee directory
            </TextAction>
          </div>
        </section>

        <section className="wh-card wh-payroll">
          <CardHeader
            icon={<Wallet />}
            title="Payroll overview"
          />

          <div className="wh-payroll-month">
            <strong>
              {today
                ? new Intl.DateTimeFormat(
                    "en-GB",
                    {
                      month: "long",
                      year: "numeric",
                    },
                  ).format(today)
                : "Current period"}
            </strong>
          </div>

          <div className="wh-payroll-next">
            <CalendarDays size={23} />

            <div>
              <span>
                Next payroll
              </span>

              <strong>
                Not available
              </strong>
            </div>
          </div>

          <button
            type="button"
            className="wh-button wh-button-dark wh-button-full"
            onClick={() =>
              router.push("/payroll")
            }
          >
            Open payroll

            <ArrowRight size={15} />
          </button>
        </section>
      </div>

      <div className="wh-bottom-grid">
        <section className="wh-card wh-monitoring">
          <CardHeader
            icon={<Monitor />}
            title="Monitoring & devices"
          />

          <div className="wh-monitoring-stats">
            <MiniMetric
              icon={<ShieldCheck />}
              value={metricValue(
                "devices",
                assignedDevices.length,
              )}
              label="Assigned"
              detail="devices"
            />

            <MiniMetric
              icon={<Laptop2 />}
              value={metricValue(
                "devices",
                activeDevices.length,
              )}
              label="Active devices"
              detail="registered as active"
            />

            <MiniMetric
              icon={
                <TriangleAlert />
              }
              value="—"
              label="Alerts"
              detail="not connected"
              warning
            />
          </div>

          <div className="wh-monitoring-actions">
            <button
              type="button"
              className="wh-button wh-button-outline"
              onClick={() =>
                router.push("/devices")
              }
            >
              View devices
            </button>

            <button
              type="button"
              className="wh-button wh-button-dark"
              onClick={() =>
                router.push(
                  "/monitoring",
                )
              }
            >
              Open monitoring

              <ArrowRight size={15} />
            </button>
          </div>
        </section>

        <section className="wh-card wh-updates">
          <CardHeader
            icon={<Megaphone />}
            title={words.updates}
          />

          <EmptyState
            compact
            icon={<Megaphone />}
            title="Updates are not connected"
            description={workspace?.workspace_type === "agency" ? "Agency activity will appear here when available." : "Company activity will appear here when available."}
          />
        </section>

        <section className="wh-card wh-workspace-status">
          <CardHeader
            icon={<Activity />}
            title="Workspace status"
          />

          <dl className="wh-status-list">
            <div>
              <dt>Workspace</dt>

              <dd
                title={
                  workspace?.name ??
                  undefined
                }
              >
                {workspace?.name ??
                  "—"}
              </dd>
            </div>

            <div>
              <dt>Status</dt>

              <dd>
                <span
                  className={
                    workspace?.status === "ready"
                      ? "wh-status-value wh-status-value-active"
                      : "wh-status-value"
                  }
                >
                  {workspace?.status === "ready" ? (
                    <span
                      className="wh-dot wh-dot-green"
                      aria-hidden="true"
                    />
                  ) : null}

                  {workspace?.status ??
                    "—"}
                </span>
              </dd>
            </div>

            <div>
              <dt>Your role</dt>

              <dd className="wh-capitalize">
                {membership?.role_key ??
                  "—"}
              </dd>
            </div>
          </dl>

          <div
            className="wh-updated"
            aria-live="polite"
          >
            <RefreshCcw size={14} />

            <span>
              {loading
                ? "Updating"
                : `${loadedSourceCount}/4 sources loaded`}
            </span>

            <time
              dateTime={
                updatedAt?.toISOString()
              }
            >
              {updatedAt
                ? new Intl.DateTimeFormat(
                    "en-GB",
                    {
                      hour: "2-digit",
                      minute: "2-digit",
                    },
                  ).format(updatedAt)
                : "—"}
            </time>
          </div>
        </section>
      </div>

      <details className="wh-card wh-employee-details">
        <summary>
          <span>
            <Users size={20} />

            Employee quick list

            <span className="wh-count">
              {metricValue(
                "employees",
                employees.length,
              )}
            </span>
          </span>

          <ChevronRight
            size={18}
            className="wh-details-chevron"
          />
        </summary>

        <div className="wh-employee-toolbar">
          <p>
            Employees in{" "}
            {workspace?.name ??
              "your workspace"}.
          </p>

          <TextAction
            onClick={() =>
              router.push(
                "/employees",
              )
            }
          >
            View all employees
          </TextAction>
        </div>

        {states.employees ===
        "loading" ? (
          <EmptyState
            icon={<Users />}
            title="Loading employees"
            description="Your workspace records are loading."
          />
        ) : states.employees ===
          "error" ? (
          <EmptyState
            icon={<TriangleAlert />}
            title="Employees could not be loaded"
            description="Use Refresh to try again."
          />
        ) : quickEmployees.length ===
          0 ? (
          <div className="wh-empty-employees">
            <EmptyState
              icon={<Users />}
              title="No employees yet"
              description="Add your first employee to get started."
            />

            {canManage ? (
              <button
                type="button"
                className="wh-button wh-button-yellow"
                onClick={() =>
                  router.push(
                    "/employees?create=1",
                  )
                }
              >
                <Plus size={16} />

                Add employee
              </button>
            ) : null}
          </div>
        ) : (
          <div className="wh-table-scroll">
            <table className="wh-table wh-employee-table">
              <thead>
                <tr>
                  <th scope="col">
                    Employee
                  </th>

                  <th scope="col">
                    Employee code
                  </th>

                  <th scope="col">
                    Department
                  </th>

                  <th scope="col">
                    Job title
                  </th>

                  <th scope="col">
                    Status
                  </th>
                </tr>
              </thead>

              <tbody>
                {quickEmployees.map(
                  (employee) => (
                    <tr
                      key={
                        employee.id
                      }
                    >
                      <td>
                        <div className="wh-employee">
                          <span
                            className="wh-avatar"
                            aria-hidden="true"
                          >
                            {initials(
                              employee,
                            )}
                          </span>

                          <div>
                            <strong>
                              {
                                employee.full_name
                              }
                            </strong>

                            <span>
                              {employee.work_email ??
                                "No work email"}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td>
                        {
                          employee.employee_code
                        }
                      </td>

                      <td>
                        {employee.department_id
                          ? departmentNames.get(
                              employee.department_id,
                            ) ?? "—"
                          : "—"}
                      </td>

                      <td>
                        {employee.job_title ??
                          "—"}
                      </td>

                      <td>
                        <EmploymentBadge
                          status={
                            employee.employment_status
                          }
                        />
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </details>

      <style jsx global>{`
        .wh-home {
          --wh-page: #fcfbf8;
          --wh-surface: #fffefd;
          --wh-soft: #f4f3f0;
          --wh-cream: #fff9ec;
          --wh-line: #e9e5dd;
          --wh-cream-line: #f0e6cf;
          --wh-ink: #17212e;
          --wh-muted: #626d7d;
          --wh-yellow: #ffc535;
          --wh-yellow-soft: #fff0c6;
          --wh-accent: #996000;
          --wh-dark: #252d31;
          --wh-green: #16824b;
          --wh-red: #bd3535;

          width: 100%;
          min-width: 0;
          max-width: 1680px;
          margin: 0 auto;
          padding: 0;
          color: var(--wh-ink);
          font-family: inherit;
          font-size: 13px;
          line-height: 1.45;
          font-variant-numeric: tabular-nums;
          container-type: inline-size;
          container-name: workspace-home;
        }

        .wh-home,
        .wh-home * {
          box-sizing: border-box;
        }

        .wh-home ::selection {
          color: #17212e;
          background: #ffe39a;
        }

        .wh-home h1,
        .wh-home h2,
        .wh-home p,
        .wh-home dl,
        .wh-home dd {
          margin: 0;
        }

        .wh-home button,
        .wh-home summary {
          -webkit-tap-highlight-color: transparent;
        }

        .wh-home button {
          font: inherit;
        }

        .wh-home button:focus-visible,
        .wh-home summary:focus-visible {
          outline: 3px solid var(--wh-yellow);
          outline-offset: 3px;
        }

        .wh-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
          margin-bottom: 18px;
          padding: 0 4px;
        }

        .wh-heading h1 {
          font-size: clamp(24px, 2.2vw, 30px);
          font-weight: 750;
          letter-spacing: -0.035em;
          line-height: 1.18;
        }

        .wh-heading p {
          margin-top: 4px;
          color: var(--wh-muted);
          font-size: 15px;
        }

        .wh-heading-actions {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: flex-end;
          gap: 10px;
        }

        .wh-date {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          margin-right: 12px;
          color: var(--wh-muted);
          white-space: nowrap;
        }

        .wh-button {
          display: inline-flex;
          min-height: 36px;
          align-items: center;
          justify-content: center;
          gap: 9px;
          padding: 8px 13px;
          border: 1px solid var(--wh-line);
          border-radius: 8px;
          background: var(--wh-surface);
          color: var(--wh-ink);
          font-size: 12px;
          font-weight: 600;
          line-height: 1.25;
          text-decoration: none;
          white-space: nowrap;
          cursor: pointer;
          transition:
            background-color 150ms ease,
            border-color 150ms ease;
        }

        .wh-button:hover:not(:disabled) {
          background: var(--wh-soft);
          border-color: #c8c2b7;
        }

        .wh-button:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        .wh-button-outline {
          border-color: #a5abb2;
        }

        .wh-button-dark {
          background: var(--wh-dark);
          border-color: var(--wh-dark);
          color: #fff;
        }

        .wh-button-dark:hover:not(:disabled) {
          background: #394349;
          border-color: #394349;
        }

        .wh-button-yellow {
          color: #17212e;
          background: var(--wh-yellow);
          border-color: var(--wh-yellow);
        }

        .wh-button-yellow:hover:not(:disabled) {
          background: #ffd15d;
          border-color: #ffd15d;
        }

        .wh-button-full {
          width: 100%;
        }

        .wh-summary {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          margin-bottom: 15px;
          padding: 14px 10px;
          border: 1px solid var(--wh-cream-line);
          border-radius: 13px;
          background: var(--wh-cream);
        }

        .wh-summary-item {
          display: flex;
          min-width: 0;
          align-items: center;
          justify-content: center;
          gap: 17px;
          padding: 2px 14px;
        }

        .wh-summary-item + .wh-summary-item {
          border-left: 1px solid var(--wh-cream-line);
        }

        .wh-summary-icon {
          position: relative;
          display: inline-flex;
          flex-shrink: 0;
          align-items: center;
          justify-content: center;
        }

        .wh-summary-icon > svg {
          width: 29px;
          height: 29px;
          stroke-width: 1.7;
        }

        .wh-summary-icon > .wh-dot {
          position: absolute;
          top: 1px;
          right: -10px;
        }

        .wh-summary-item strong {
          display: block;
          font-size: 27px;
          font-weight: 720;
          letter-spacing: -0.035em;
          line-height: 1.1;
        }

        .wh-summary-item small {
          display: block;
          margin-top: 3px;
          color: var(--wh-muted);
          font-size: 12px;
        }

        .wh-dot {
          display: inline-block;
          width: 9px;
          height: 9px;
          flex-shrink: 0;
          border-radius: 50%;
        }

        .wh-dot-green {
          background: #18ad63;
        }

        .wh-dot-yellow {
          background: var(--wh-yellow);
        }

        .wh-card {
          min-width: 0;
          border: 1px solid var(--wh-line);
          border-radius: 13px;
          background: var(--wh-surface);
          overflow: hidden;
        }

        .wh-primary-grid {
          display: grid;
          grid-template-columns:
            minmax(0, 1.47fr)
            minmax(0, 1fr);
          gap: 14px;
          margin-bottom: 14px;
        }

        .wh-right-stack {
          display: grid;
          grid-template-rows: auto 1fr;
          gap: 13px;
          min-width: 0;
        }

        .wh-card-header {
          display: flex;
          min-height: 48px;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 14px 17px 8px;
        }

        .wh-card-heading {
          display: flex;
          min-width: 0;
          align-items: center;
          gap: 12px;
        }

        .wh-card-heading > svg {
          width: 21px;
          height: 21px;
          flex-shrink: 0;
          stroke-width: 1.8;
        }

        .wh-card-heading h2 {
          font-size: 16px;
          font-weight: 700;
          line-height: 1.25;
          letter-spacing: -0.025em;
        }

        .wh-text-action {
          display: inline-flex;
          flex-shrink: 0;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 3px 0;
          border: 0;
          background: transparent;
          color: var(--wh-accent);
          font-size: 12px;
          line-height: 1.4;
          white-space: nowrap;
          cursor: pointer;
        }

        .wh-text-action:hover {
          text-decoration: underline;
          text-underline-offset: 4px;
        }

        .wh-attendance {
          min-height: 334px;
        }

        .wh-legend {
          display: flex;
          flex-wrap: wrap;
          gap: 13px 25px;
          padding: 12px 18px 3px;
        }

        .wh-legend-item {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          color: var(--wh-muted);
          font-size: 12px;
        }

        .wh-legend-item strong {
          margin-left: 4px;
          color: var(--wh-ink);
          font-weight: 600;
        }

        .wh-legend-dot {
          width: 13px;
          height: 13px;
          border-radius: 50%;
        }

        .wh-legend-present {
          background: #f8b900;
        }

        .wh-legend-late {
          background: #ffe5a0;
        }

        .wh-legend-absent {
          background: #ff927f;
        }

        .wh-legend-leave {
          background: #a5a8ad;
        }

        .wh-chart {
          position: relative;
          height: 232px;
          margin: 12px 26px 10px 42px;
        }

        .wh-chart-grid {
          position: absolute;
          inset: 12px 0 43px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          border-left: 1px solid #d3d5d9;
          border-bottom: 1px solid #d3d5d9;
        }

        .wh-chart-line {
          display: block;
          width: 100%;
          border-top: 1px dashed var(--wh-line);
        }

        .wh-chart-message {
          position: absolute;
          inset: 12px 0 43px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 7px;
          padding: 15px;
          text-align: center;
        }

        .wh-chart-message > svg {
          color: var(--wh-accent);
        }

        .wh-chart-message strong {
          padding: 2px 8px;
          background: var(--wh-surface);
          font-size: 13px;
          font-weight: 600;
        }

        .wh-chart-message > span {
          max-width: 290px;
          padding: 2px 8px;
          background: var(--wh-surface);
          color: var(--wh-muted);
          font-size: 12px;
        }

        .wh-chart-days {
          position: absolute;
          right: 0;
          bottom: 0;
          left: 0;
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          text-align: center;
        }

        .wh-chart-days strong,
        .wh-chart-days span {
          display: block;
          color: var(--wh-muted);
          font-size: 11px;
          font-weight: 400;
        }

        .wh-approval-list {
          margin: 0 15px;
          border: 1px solid var(--wh-line);
          border-radius: 8px;
          overflow: hidden;
        }

        .wh-approval-row {
          display: grid;
          grid-template-columns:
            22px minmax(0, 1fr) 35px auto;
          min-height: 39px;
          align-items: center;
          gap: 10px;
          padding: 4px 6px 4px 10px;
        }

        .wh-approval-row + .wh-approval-row {
          border-top: 1px solid var(--wh-line);
        }

        .wh-approval-row > svg {
          width: 17px;
          height: 17px;
          stroke-width: 1.8;
        }

        .wh-approval-row > span {
          font-size: 12px;
        }

        .wh-approval-count {
          display: inline-grid;
          width: 30px;
          height: 30px;
          place-items: center;
          border-radius: 50%;
          background: var(--wh-cream);
          font-size: 13px;
          font-weight: 650;
        }

        .wh-review-button {
          min-height: 29px;
          gap: 9px;
          padding: 5px 10px;
          font-size: 11px;
        }

        .wh-footnote {
          padding: 5px 17px 9px;
          color: var(--wh-muted);
          font-size: 10px;
        }

        .wh-meetings .wh-empty {
          min-height: 87px;
        }

        .wh-secondary-grid {
          display: grid;
          grid-template-columns:
            minmax(0, 2.12fr)
            minmax(0, 1.09fr)
            minmax(0, 1fr);
          gap: 14px;
          margin-bottom: 13px;
        }

        .wh-projects,
        .wh-people,
        .wh-payroll {
          min-height: 185px;
        }

        .wh-table-scroll {
          min-width: 0;
          overflow-x: auto;
          scrollbar-width: thin;
          scrollbar-color: #c8c2b7 transparent;
        }

        .wh-table {
          width: 100%;
          border-collapse: separate;
          border-spacing: 0;
          color: var(--wh-ink);
          text-align: left;
        }

        .wh-table th {
          padding: 7px 10px;
          background: var(--wh-soft);
          font-size: 11px;
          font-weight: 500;
          white-space: nowrap;
        }

        .wh-table td {
          padding: 10px;
          border-bottom: 1px solid var(--wh-line);
          font-size: 12px;
          vertical-align: middle;
        }

        .wh-table tbody tr:last-child td {
          border-bottom: 0;
        }

        .wh-project-table {
          width: calc(100% - 32px);
          min-width: 390px;
          margin: 0 16px 10px;
        }

        .wh-project-table th:first-child {
          border-radius: 7px 0 0 7px;
        }

        .wh-project-table th:last-child {
          border-radius: 0 7px 7px 0;
        }

        .wh-table .wh-table-empty {
          height: 83px;
          color: var(--wh-muted);
          text-align: center;
        }

        .wh-people-stats {
          display: grid;
          grid-template-columns: 1fr 1fr;
          align-items: center;
          padding: 17px 13px 21px;
        }

        .wh-people-stats > div {
          display: flex;
          min-width: 0;
          align-items: center;
          justify-content: center;
          gap: 11px;
        }

        .wh-people-stats > div + div {
          border-left: 1px solid var(--wh-line);
        }

        .wh-icon-circle {
          display: inline-flex;
          width: 45px;
          height: 45px;
          flex-shrink: 0;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          background: var(--wh-yellow-soft);
          color: var(--wh-ink);
        }

        .wh-people-stats strong {
          display: block;
          font-size: 23px;
          font-weight: 700;
          line-height: 1.2;
        }

        .wh-people-stats div > span:not(.wh-icon-circle) {
          display: block;
          color: var(--wh-muted);
          font-size: 11px;
        }

        .wh-card-footer {
          display: flex;
          justify-content: center;
          margin: 0 16px;
          padding: 8px 0 10px;
          border-top: 1px solid var(--wh-line);
        }

        .wh-payroll {
          padding-bottom: 10px;
        }

        .wh-payroll-month {
          padding: 1px 16px 9px;
          font-size: 13px;
        }

        .wh-payroll-month strong {
          font-weight: 600;
        }

        .wh-payroll-next {
          display: flex;
          align-items: center;
          gap: 12px;
          margin: 0 15px 8px;
          padding: 9px 12px;
          border-radius: 8px;
          background: var(--wh-soft);
        }

        .wh-payroll-next span,
        .wh-payroll-next strong {
          display: block;
          color: var(--wh-muted);
          font-size: 11px;
          font-weight: 400;
        }

        .wh-payroll-next strong {
          margin-top: 2px;
          color: var(--wh-ink);
          font-size: 12px;
        }

        .wh-payroll > .wh-button {
          width: calc(100% - 30px);
          min-height: 32px;
          margin: 0 15px;
        }

        .wh-bottom-grid {
          display: grid;
          grid-template-columns:
            minmax(0, 1.85fr)
            minmax(0, 1.42fr)
            minmax(0, 0.9fr);
          gap: 13px;
          margin-bottom: 15px;
        }

        .wh-monitoring,
        .wh-updates,
        .wh-workspace-status {
          min-height: 173px;
        }

        .wh-monitoring-stats {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          padding: 8px 13px;
        }

        .wh-mini-metric {
          display: flex;
          min-width: 0;
          align-items: center;
          gap: 10px;
          padding: 0 9px;
        }

        .wh-mini-metric + .wh-mini-metric {
          border-left: 1px solid var(--wh-line);
        }

        .wh-mini-metric .wh-icon-circle {
          width: 43px;
          height: 43px;
          color: #835600;
        }

        .wh-mini-metric .wh-icon-circle svg {
          width: 24px;
          height: 24px;
          stroke-width: 1.8;
        }

        .wh-mini-copy {
          min-width: 0;
        }

        .wh-mini-copy > span,
        .wh-mini-copy > small {
          display: block;
          color: var(--wh-muted);
          font-size: 10px;
          line-height: 1.35;
        }

        .wh-mini-copy > strong {
          display: block;
          margin: 2px 0;
          font-size: 23px;
          font-weight: 700;
          letter-spacing: -0.025em;
          line-height: 1.15;
        }

        .wh-mini-warning .wh-icon-circle,
        .wh-mini-warning .wh-mini-copy > strong {
          color: var(--wh-red);
        }

        .wh-monitoring-actions {
          display: flex;
          flex-wrap: wrap;
          justify-content: flex-end;
          gap: 10px;
          padding: 8px 14px 11px;
        }

        .wh-monitoring-actions .wh-button {
          min-height: 31px;
          font-size: 11px;
        }

        .wh-status-list {
          padding: 3px 15px 8px;
        }

        .wh-status-list > div {
          display: flex;
          min-width: 0;
          justify-content: space-between;
          gap: 12px;
          padding: 4px 0;
          font-size: 11px;
        }

        .wh-status-list dt {
          flex-shrink: 0;
          color: var(--wh-muted);
        }

        .wh-status-list dd {
          min-width: 0;
          max-width: 64%;
          overflow: hidden;
          text-align: right;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .wh-status-value {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          text-transform: capitalize;
        }

        .wh-status-value-active {
          color: var(--wh-green);
        }

        .wh-status-value .wh-dot {
          width: 7px;
          height: 7px;
        }

        .wh-capitalize {
          text-transform: capitalize;
        }

        .wh-updated {
          display: flex;
          align-items: center;
          gap: 7px;
          margin: 0 15px;
          padding: 9px 0;
          border-top: 1px solid var(--wh-line);
          color: var(--wh-muted);
          font-size: 10px;
        }

        .wh-updated time {
          margin-left: auto;
          white-space: nowrap;
        }

        .wh-empty {
          display: flex;
          min-height: 122px;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 18px;
          text-align: center;
        }

        .wh-empty > svg {
          width: 25px;
          height: 25px;
          margin-bottom: 3px;
          color: var(--wh-accent);
          stroke-width: 1.5;
        }

        .wh-empty > strong {
          font-size: 12px;
          font-weight: 600;
        }

        .wh-empty > p {
          max-width: 300px;
          color: var(--wh-muted);
          font-size: 11px;
        }

        .wh-empty-compact {
          min-height: 100px;
          padding: 10px 17px 16px;
        }

        .wh-empty-compact > svg {
          display: none;
        }

        .wh-error {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 15px;
          padding: 14px;
          border: 1px solid #edc4ba;
          border-radius: 10px;
          background: #fff5f1;
          color: #8d3025;
        }

        .wh-error > svg {
          flex-shrink: 0;
          margin-top: 2px;
        }

        .wh-error > div {
          min-width: 0;
          flex: 1;
        }

        .wh-error strong {
          font-size: 12px;
        }

        .wh-error p {
          margin-top: 3px;
          overflow-wrap: anywhere;
          font-size: 12px;
        }

        .wh-employee-details > summary {
          display: flex;
          min-height: 51px;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 13px 17px;
          list-style: none;
          cursor: pointer;
        }

        .wh-employee-details > summary::-webkit-details-marker {
          display: none;
        }

        .wh-employee-details > summary > span {
          display: inline-flex;
          align-items: center;
          gap: 11px;
          font-size: 14px;
          font-weight: 650;
        }

        .wh-count {
          padding: 1px 7px;
          border-radius: 6px;
          background: var(--wh-cream);
          color: var(--wh-accent);
          font-size: 11px;
        }

        .wh-details-chevron {
          transition: transform 150ms ease;
        }

        .wh-employee-details[open] .wh-details-chevron {
          transform: rotate(90deg);
        }

        .wh-employee-details[open] > summary {
          border-bottom: 1px solid var(--wh-line);
        }

        .wh-employee-toolbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 15px;
          padding: 12px 17px;
        }

        .wh-employee-toolbar p {
          color: var(--wh-muted);
          font-size: 12px;
        }

        .wh-employee-table {
          min-width: 760px;
        }

        .wh-employee-table th,
        .wh-employee-table td {
          padding-right: 17px;
          padding-left: 17px;
        }

        .wh-employee {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .wh-avatar {
          display: inline-grid;
          width: 33px;
          height: 33px;
          flex-shrink: 0;
          place-items: center;
          border-radius: 50%;
          background: var(--wh-soft);
          color: var(--wh-muted);
          font-size: 11px;
          font-weight: 600;
        }

        .wh-employee strong,
        .wh-employee div > span {
          display: block;
        }

        .wh-employee strong {
          font-size: 12px;
          font-weight: 600;
        }

        .wh-employee div > span {
          margin-top: 2px;
          color: var(--wh-muted);
          font-size: 11px;
        }

        .wh-employment-badge {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 3px 8px;
          border-radius: 7px;
          background: var(--wh-soft);
          color: var(--wh-muted);
          font-size: 10px;
          white-space: nowrap;
        }

        .wh-employment-active {
          background: #edf8ef;
          color: #1a713c;
        }

        .wh-employment-leave {
          background: #fff4d4;
          color: #805700;
        }

        .wh-employment-danger {
          background: #fff0ed;
          color: #a63628;
        }

        .wh-empty-employees {
          padding-bottom: 20px;
          text-align: center;
        }

        .wh-spinning {
          animation: wh-spin 900ms linear infinite;
        }

        @keyframes wh-spin {
          to {
            transform: rotate(360deg);
          }
        }

        html.dark .wh-home,
        body.dark .wh-home,
        .dark .wh-home,
        [data-theme="dark"] .wh-home {
          --wh-page: #15191d;
          --wh-surface: #1c2227;
          --wh-soft: #252c32;
          --wh-cream: #302a1d;
          --wh-line: #353d43;
          --wh-cream-line: #50432a;
          --wh-ink: #f2f4f7;
          --wh-muted: #b3bdc8;
          --wh-yellow-soft: #493b1d;
          --wh-accent: #ffd16c;
          --wh-dark: #303a42;
          --wh-green: #7ae0a4;
          --wh-red: #ff9d91;
        }

        .dark .wh-home .wh-error,
        [data-theme="dark"] .wh-home .wh-error {
          border-color: #684239;
          background: #352522;
          color: #ffc1b4;
        }

        .dark .wh-home .wh-employment-active,
        [data-theme="dark"] .wh-home .wh-employment-active {
          background: #203b2b;
          color: #9ae5b3;
        }

        .dark .wh-home .wh-employment-leave,
        [data-theme="dark"] .wh-home .wh-employment-leave {
          background: #40351d;
          color: #ffe09b;
        }

        .dark .wh-home .wh-employment-danger,
        [data-theme="dark"] .wh-home .wh-employment-danger {
          background: #432b29;
          color: #ffb5a8;
        }

        .dark .wh-home .wh-mini-metric .wh-icon-circle,
        [data-theme="dark"] .wh-home .wh-mini-metric .wh-icon-circle {
          color: #ffd16c;
        }

        .dark .wh-home .wh-mini-warning .wh-icon-circle,
        [data-theme="dark"] .wh-home .wh-mini-warning .wh-icon-circle {
          color: #ff9d91;
        }

        @container workspace-home (max-width: 1100px) {
          .wh-heading {
            align-items: flex-start;
          }

          .wh-heading-actions {
            max-width: 390px;
          }

          .wh-date {
            margin-right: 0;
          }

          .wh-summary-item {
            gap: 12px;
            padding-right: 8px;
            padding-left: 8px;
          }

          .wh-summary-item strong {
            font-size: 24px;
          }

          .wh-summary-item small {
            font-size: 11px;
          }

          .wh-primary-grid {
            grid-template-columns:
              minmax(0, 1.3fr)
              minmax(0, 1fr);
          }

          .wh-secondary-grid {
            grid-template-columns:
              minmax(0, 1.6fr)
              minmax(0, 1fr);
          }

          .wh-payroll {
            grid-column: 1 / -1;
          }

          .wh-bottom-grid {
            grid-template-columns:
              minmax(0, 1.4fr)
              minmax(0, 1fr);
          }

          .wh-workspace-status {
            grid-column: 1 / -1;
          }
        }

        @container workspace-home (max-width: 800px) {
          .wh-heading {
            flex-direction: column;
            gap: 14px;
          }

          .wh-heading-actions {
            max-width: none;
            justify-content: flex-start;
          }

          .wh-summary {
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 16px 0;
          }

          .wh-summary-item {
            justify-content: flex-start;
            padding-left: 18px;
          }

          .wh-summary-item:nth-child(4) {
            border-left: 0;
          }

          .wh-primary-grid {
            grid-template-columns: minmax(0, 1fr);
          }

          .wh-right-stack {
            grid-template-columns:
              minmax(0, 1fr)
              minmax(0, 1fr);
            grid-template-rows: auto;
          }

          .wh-bottom-grid {
            grid-template-columns: minmax(0, 1fr);
          }

          .wh-workspace-status {
            grid-column: auto;
          }
        }

        @container workspace-home (max-width: 560px) {
          .wh-heading {
            padding: 0;
          }

          .wh-heading h1 {
            font-size: 25px;
          }

          .wh-heading p {
            font-size: 13px;
          }

          .wh-heading-actions {
            width: 100%;
            gap: 8px;
          }

          .wh-date {
            width: 100%;
            margin-bottom: 2px;
            font-size: 12px;
          }

          .wh-heading-actions .wh-button {
            min-height: 40px;
            flex: 1 1 auto;
            padding: 9px 10px;
            font-size: 11px;
          }

          .wh-summary {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            padding: 14px 5px;
          }

          .wh-summary-item {
            gap: 14px;
            padding-left: 14px;
          }

          .wh-summary-item:nth-child(odd) {
            border-left: 0;
          }

          .wh-summary-item:nth-child(even) {
            border-left: 1px solid var(--wh-cream-line);
          }

          .wh-summary-item strong {
            font-size: 24px;
          }

          .wh-summary-icon > svg {
            width: 25px;
            height: 25px;
          }

          .wh-right-stack,
          .wh-secondary-grid {
            grid-template-columns: minmax(0, 1fr);
          }

          .wh-payroll {
            grid-column: auto;
          }

          .wh-card-header {
            gap: 8px;
            padding-right: 13px;
            padding-left: 13px;
          }

          .wh-card-heading {
            gap: 8px;
          }

          .wh-card-heading h2 {
            font-size: 15px;
          }

          .wh-text-action {
            gap: 5px;
            font-size: 11px;
          }

          .wh-legend {
            gap: 10px 17px;
            padding-right: 13px;
            padding-left: 13px;
          }

          .wh-chart {
            margin-right: 15px;
            margin-left: 20px;
          }

          .wh-chart-message strong {
            max-width: 220px;
          }

          .wh-monitoring-stats {
            gap: 13px;
            padding: 10px 15px;
            grid-template-columns: minmax(0, 1fr);
          }

          .wh-mini-metric {
            padding: 0;
          }

          .wh-mini-metric + .wh-mini-metric {
            padding-top: 12px;
            border-top: 1px solid var(--wh-line);
            border-left: 0;
          }

          .wh-mini-copy {
            display: grid;
            flex: 1;
            grid-template-columns:
              minmax(0, 1fr) auto;
            align-items: center;
            gap: 2px 15px;
          }

          .wh-mini-copy > strong {
            grid-column: 2;
            grid-row: 1 / 3;
          }

          .wh-mini-copy > small {
            grid-column: 1;
          }

          .wh-monitoring-actions .wh-button {
            min-height: 40px;
            flex: 1;
          }

          .wh-review-button {
            min-height: 36px;
          }

          .wh-error {
            flex-wrap: wrap;
          }

          .wh-error > .wh-button {
            margin-left: 30px;
          }

          .wh-employee-toolbar {
            align-items: flex-start;
            flex-direction: column;
            gap: 6px;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .wh-home *,
          .wh-home *::before,
          .wh-home *::after {
            animation: none !important;
            transition: none !important;
          }
        }
      `}</style>
    </main>
  );
}


function CardHeader({
  icon,
  title,
  action,
}: {
  icon: ReactNode;
  title: string;
  action?: ReactNode;
}) {
  return (
    <header className="wh-card-header">
      <div className="wh-card-heading">
        {icon}

        <h2>{title}</h2>
      </div>

      {action}
    </header>
  );
}


function TextAction({
  children,
  onClick,
}: {
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className="wh-text-action"
      onClick={onClick}
    >
      {children}

      <ArrowRight
        size={14}
        aria-hidden="true"
      />
    </button>
  );
}


function SummaryMetric({
  icon,
  value,
  label,
  dot,
}: {
  icon: ReactNode;
  value: string | number;
  label: string;
  dot?: "green" | "yellow";
}) {
  return (
    <div className="wh-summary-item">
      <span
        className="wh-summary-icon"
        aria-hidden="true"
      >
        {icon}

        {dot ? (
          <span
            className={`wh-dot wh-dot-${dot}`}
          />
        ) : null}
      </span>

      <div>
        <strong>{value}</strong>

        <small>{label}</small>
      </div>
    </div>
  );
}


function LegendItem({
  tone,
  label,
  value,
}: {
  tone:
    | "present"
    | "late"
    | "absent"
    | "leave";
  label: string;
  value: string | number;
}) {
  return (
    <span className="wh-legend-item">
      <span
        className={`wh-legend-dot wh-legend-${tone}`}
        aria-hidden="true"
      />

      {label}

      <strong>{value}</strong>
    </span>
  );
}


function ApprovalRow({
  icon,
  label,
  onOpen,
}: {
  icon: ReactNode;
  label: string;
  onOpen?: () => void;
}) {
  return (
    <div className="wh-approval-row">
      {icon}

      <span>{label}</span>

      <strong
        className="wh-approval-count"
        aria-label="Count unavailable"
      >
        â€”
      </strong>

      <button
        type="button"
        className="wh-button wh-review-button"
        onClick={onOpen}
        disabled={!onOpen}
        title={
          onOpen
            ? `Open ${label.toLowerCase()}`
            : "Leave approvals are not connected."
        }
      >
        Open

        <ChevronRight
          size={13}
          aria-hidden="true"
        />
      </button>
    </div>
  );
}


function MiniMetric({
  icon,
  value,
  label,
  detail,
  warning = false,
}: {
  icon: ReactNode;
  value: string | number;
  label: string;
  detail: string;
  warning?: boolean;
}) {
  return (
    <div
      className={
        warning
          ? "wh-mini-metric wh-mini-warning"
          : "wh-mini-metric"
      }
    >
      <span
        className="wh-icon-circle"
        aria-hidden="true"
      >
        {icon}
      </span>

      <div className="wh-mini-copy">
        <span>{label}</span>

        <strong>{value}</strong>

        <small>{detail}</small>
      </div>
    </div>
  );
}


function EmptyState({
  icon,
  title,
  description,
  compact = false,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  compact?: boolean;
}) {
  return (
    <div
      className={
        compact
          ? "wh-empty wh-empty-compact"
          : "wh-empty"
      }
    >
      {icon}

      <strong>{title}</strong>

      <p>{description}</p>
    </div>
  );
}


function EmploymentBadge({
  status,
}: {
  status: EmploymentStatus;
}) {
  let label = "Unknown";
  let className =
    "wh-employment-badge";

  switch (status) {
    case "active":
      label = "Active";

      className +=
        " wh-employment-active";

      break;

    case "on_leave":
      label = "On leave";

      className +=
        " wh-employment-leave";

      break;

    case "suspended":
      label = "Suspended";

      className +=
        " wh-employment-danger";

      break;

    case "terminated":
      label = "Terminated";

      break;
  }

  return (
    <span className={className}>
      {status === "active" ? (
        <Check
          size={11}
          aria-hidden="true"
        />
      ) : null}

      {label}
    </span>
  );
}
