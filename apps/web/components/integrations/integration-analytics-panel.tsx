"use client";

import {
  Activity,
  Clock3,
  Users,
  Target,
} from "lucide-react";

import type {
  AnalyticsOverviewResponse,
} from "@/types/integration-analytics";

export function IntegrationAnalyticsPanel({
  data,
}: {
  data: AnalyticsOverviewResponse | null;
}) {
  if (!data) {
    return (
      <div className="empty-state">
        <Activity size={24} />

        <strong>
          Analytics unavailable
        </strong>

        <span>
          No integration analytics response is currently available.
        </span>
      </div>
    );
  }

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns:
          "repeat(4, minmax(0, 1fr))",
        gap: 10,
      }}
    >
      <Metric
        icon={<Users size={15} />}
        label="Employees"
        value={data.employees}
      />

      <Metric
        icon={<Activity size={15} />}
        label="Activity Events"
        value={data.activity_events}
      />

      <Metric
        icon={<Clock3 size={15} />}
        label="Worked Minutes"
        value={data.worked_minutes}
      />

      <Metric
        icon={<Target size={15} />}
        label="Goals Completed"
        value={data.goals_completed}
      />
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
}) {
  return (
    <div
      style={{
        padding: 12,
        border:
          "1px solid var(--color-border)",
        borderRadius: 7,
        background: "#fffefa",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          color:
            "var(--color-text-muted)",
          fontSize: 10,
        }}
      >
        {icon}
        {label}
      </div>

      <strong
        style={{
          display: "block",
          marginTop: 8,
          fontSize: 20,
        }}
      >
        {value.toLocaleString()}
      </strong>
    </div>
  );
}