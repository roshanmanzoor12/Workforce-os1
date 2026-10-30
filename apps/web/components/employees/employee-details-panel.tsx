import {
  BriefcaseBusiness,
  Laptop,
  Mail,
  Phone,
  User,
  Wifi,
} from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";
import type { EmployeeDetailView } from "@/types/employee";

interface EmployeeDetailsPanelProps {
  employee?: EmployeeDetailView | null;
}

function DetailRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value?: string | null;
}) {
  return (
    <div
      style={{
        display: "flex",
        gap: 10,
        padding: "11px 0",
        borderBottom:
          "1px solid var(--color-border-subtle)",
      }}
    >
      <span
        style={{
          width: 20,
          flex: "0 0 20px",
          color: "#777b80",
        }}
      >
        {icon}
      </span>

      <span>
        <span
          style={{
            display: "block",
            color:
              "var(--color-text-muted)",
            fontSize: 10,
          }}
        >
          {label}
        </span>

        <span
          style={{
            display: "block",
            marginTop: 3,
            color: "#303235",
            fontSize: 12,
            fontWeight: 500,
          }}
        >
          {value || "—"}
        </span>
      </span>
    </div>
  );
}

export function EmployeeDetailsPanel({
  employee,
}: EmployeeDetailsPanelProps) {
  if (!employee) {
    return (
      <aside className="panel">
        <div className="panel-header">
          <h2 className="text-section-title">
            Employee Overview
          </h2>
        </div>

        <EmptyState
          icon={
            <User
              size={20}
              strokeWidth={1.7}
            />
          }
          title="Select an employee"
          description="Employee identity, assigned device, presence and recent activity will appear here."
          minHeight={360}
        />
      </aside>
    );
  }

  return (
    <aside
      className="panel"
      style={{
        overflow: "hidden",
      }}
    >
      <div
        style={{
          padding: 18,
          borderBottom:
            "1px solid var(--color-border-subtle)",
          textAlign: "center",
        }}
      >
        <div
          className="avatar avatar--xl"
          style={{
            margin: "0 auto",
          }}
        >
          {employee.avatarUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={employee.avatarUrl}
              alt=""
            />
          ) : (
            employee.displayName
              .slice(0, 1)
              .toUpperCase()
          )}
        </div>

        <h2
          style={{
            marginTop: 10,
            color: "var(--color-ink)",
            fontSize: 15,
            fontWeight: 600,
          }}
        >
          {employee.displayName}
        </h2>

        <p
          style={{
            marginTop: 3,
            color:
              "var(--color-text-muted)",
            fontSize: 11,
          }}
        >
          {employee.jobTitle ||
            employee.role ||
            "Employee"}
        </p>

        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 6,
            marginTop: 10,
          }}
        >
          <StatusBadge
            variant={
              employee.accountStatus ===
              "active"
                ? "active"
                : "inactive"
            }
          >
            {employee.accountStatus}
          </StatusBadge>

          <StatusBadge
            variant={
              employee.presence ===
              "online"
                ? "online"
                : "offline"
            }
          >
            {employee.presence}
          </StatusBadge>
        </div>
      </div>

      <div
        style={{
          padding: "4px 16px 16px",
        }}
      >
        <DetailRow
          icon={
            <Mail
              size={15}
              strokeWidth={1.7}
            />
          }
          label="Email"
          value={employee.email}
        />

        <DetailRow
          icon={
            <Phone
              size={15}
              strokeWidth={1.7}
            />
          }
          label="Phone"
          value={employee.phone}
        />

        <DetailRow
          icon={
            <BriefcaseBusiness
              size={15}
              strokeWidth={1.7}
            />
          }
          label="Department"
          value={employee.department}
        />

        <DetailRow
          icon={
            <Laptop
              size={15}
              strokeWidth={1.7}
            />
          }
          label="Assigned Device"
          value={employee.deviceName}
        />

        <DetailRow
          icon={
            <Wifi
              size={15}
              strokeWidth={1.7}
            />
          }
          label="Device Last Seen"
          value={
            employee.deviceLastSeenLabel
          }
        />
      </div>
    </aside>
  );
}