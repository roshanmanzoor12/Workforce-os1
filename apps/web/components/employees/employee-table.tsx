import {
  Laptop,
  Users,
} from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";
import type {
  EmployeeAccountStatus,
  EmployeeListItemView,
  EmployeePresence,
} from "@/types/employee";

interface EmployeeTableProps {
  employees: EmployeeListItemView[];
  selectedEmployeeId?: string | null;
  loading?: boolean;
  onSelectEmployee?: (
    employee: EmployeeListItemView,
  ) => void;
}

function accountVariant(
  status: EmployeeAccountStatus,
) {
  if (status === "active") {
    return "active" as const;
  }

  return "inactive" as const;
}

function presenceVariant(
  presence: EmployeePresence,
) {
  if (presence === "online") {
    return "online" as const;
  }

  if (presence === "offline") {
    return "offline" as const;
  }

  return "neutral" as const;
}

function presenceLabel(
  presence: EmployeePresence,
) {
  if (presence === "online") {
    return "Online";
  }

  if (presence === "offline") {
    return "Offline";
  }

  return "Unknown";
}

function getInitials(
  name: string,
) {
  const parts = name
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (parts.length === 0) {
    return "?";
  }

  if (parts.length === 1) {
    return (
      parts[0]?.slice(0, 1).toUpperCase() ??
      "?"
    );
  }

  return `${
    parts[0]?.slice(0, 1) ?? ""
  }${
    parts[
      parts.length - 1
    ]?.slice(0, 1) ?? ""
  }`.toUpperCase();
}

export function EmployeeTable({
  employees,
  selectedEmployeeId,
  loading = false,
  onSelectEmployee,
}: EmployeeTableProps) {
  if (loading) {
    return (
      <div
        style={{
          padding: 16,
        }}
      >
        {Array.from({
          length: 7,
        }).map((_, index) => (
          <div
            key={index}
            style={{
              display: "grid",
              gridTemplateColumns:
                "40px 1.6fr 1fr 1fr 90px 1fr 100px 100px",
              gap: 12,
              alignItems: "center",
              height: 54,
              borderBottom:
                "1px solid var(--color-border-subtle)",
            }}
          >
            {Array.from({
              length: 8,
            }).map((__, itemIndex) => (
              <div
                key={itemIndex}
                className="skeleton"
                style={{
                  width:
                    itemIndex === 0
                      ? 28
                      : "80%",
                  height:
                    itemIndex === 0
                      ? 28
                      : 10,
                  borderRadius:
                    itemIndex === 0
                      ? "50%"
                      : 5,
                }}
              />
            ))}
          </div>
        ))}
      </div>
    );
  }

  if (employees.length === 0) {
    return (
      <EmptyState
        icon={
          <Users
            size={21}
            strokeWidth={1.7}
          />
        }
        title="No employees to display"
        description="Employee records will appear here when the verified WorkforceOS employee API is connected."
        minHeight={340}
      />
    );
  }

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Department</th>
            <th>Role</th>
            <th>Status</th>
            <th>Device</th>
            <th>Presence</th>
            <th>Last Active</th>
          </tr>
        </thead>

        <tbody>
          {employees.map((employee) => {
            const selected =
              employee.id ===
              selectedEmployeeId;

            return (
              <tr
                key={employee.id}
                onClick={() =>
                  onSelectEmployee?.(
                    employee,
                  )
                }
                style={{
                  cursor:
                    onSelectEmployee
                      ? "pointer"
                      : "default",
                  background: selected
                    ? "var(--color-surface-selected)"
                    : undefined,
                }}
              >
                <td>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                    }}
                  >
                    <span className="avatar">
                      {employee.avatarUrl ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={
                            employee.avatarUrl
                          }
                          alt=""
                        />
                      ) : (
                        getInitials(
                          employee.displayName,
                        )
                      )}
                    </span>

                    <span
                      style={{
                        minWidth: 0,
                      }}
                    >
                      <span className="data-table__primary">
                        {
                          employee.displayName
                        }
                      </span>

                      {employee.email ? (
                        <span className="data-table__secondary">
                          {employee.email}
                        </span>
                      ) : null}
                    </span>
                  </div>
                </td>

                <td>
                  {employee.department ||
                    "—"}
                </td>

                <td>
                  {employee.role || "—"}
                </td>

                <td>
                  <StatusBadge
                    variant={accountVariant(
                      employee.accountStatus,
                    )}
                  >
                    {employee.accountStatus ===
                    "active"
                      ? "Active"
                      : employee.accountStatus ===
                          "inactive"
                        ? "Inactive"
                        : "Unknown"}
                  </StatusBadge>
                </td>

                <td>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    <Laptop
                      size={14}
                      strokeWidth={1.7}
                      color="#74787c"
                    />

                    <span>
                      {employee.deviceName ||
                        "No device"}
                    </span>
                  </div>
                </td>

                <td>
                  <StatusBadge
                    variant={presenceVariant(
                      employee.presence,
                    )}
                  >
                    {presenceLabel(
                      employee.presence,
                    )}
                  </StatusBadge>
                </td>

                <td>
                  {employee.lastActiveLabel ||
                    "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}