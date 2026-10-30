"use client";

import { useState } from "react";

import {
  FileSearch,
  Filter,
  ShieldAlert,
  UserCheck,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

const events = [
  [
    "09:45:22",
    "James Fuller",
    "User login",
    "Authentication",
    "Success",
  ],
  [
    "09:42:11",
    "Theresa Webb",
    "Payroll approval",
    "Payroll",
    "Success",
  ],
  [
    "09:38:18",
    "Ralph Edwards",
    "Device policy changed",
    "Security",
    "Warning",
  ],
  [
    "09:31:05",
    "Dianne Russell",
    "Employee profile updated",
    "Employees",
    "Success",
  ],
  [
    "09:24:42",
    "Unknown",
    "Invalid login attempt",
    "Authentication",
    "Failed",
  ],
];

export default function AuditPage() {
  const [filter, setFilter] = useState("all");

  const visible =
    filter === "all"
      ? events
      : events.filter(
          (event) =>
            String(event[4]).toLowerCase() ===
            filter,
        );

  return (
    <div
      style={{
        maxWidth: 1600,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Audit Log"
        description="Review security, account and administrative events across Workforce OS."
        actions={
          <select
            className="select"
            value={filter}
            onChange={(event) =>
              setFilter(event.target.value)
            }
            style={{ width: 170 }}
          >
            <option value="all">All Events</option>
            <option value="success">Success</option>
            <option value="warning">Warnings</option>
            <option value="failed">Failed</option>
          </select>
        }
      />

      <div
        className="metric-grid"
        style={{ marginBottom: 16 }}
      >
        <MetricCard
          label="Events Today"
          value="1,842"
          icon={<FileSearch size={21} />}
          tone="brand"
        />

        <MetricCard
          label="Security Events"
          value="28"
          icon={<ShieldAlert size={21} />}
          tone="warning"
        />

        <MetricCard
          label="Successful Actions"
          value="1,796"
          icon={<UserCheck size={21} />}
          tone="success"
        />

        <MetricCard
          label="Failed Actions"
          value="18"
          icon={<ShieldAlert size={21} />}
          tone="danger"
        />
      </div>

      <section
        className="panel"
        style={{ overflow: "hidden" }}
      >
        <div className="panel-header">
          <h2 className="text-section-title">
            Recent Audit Events
          </h2>

          <Button
            variant="outline"
            size="sm"
          >
            <Filter size={14} />
            Filters
          </Button>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Category</th>
                <th>Result</th>
              </tr>
            </thead>

            <tbody>
              {visible.map(
                ([
                  time,
                  actor,
                  action,
                  category,
                  result,
                ]) => (
                  <tr
                    key={`${time}-${action}`}
                  >
                    <td>{time}</td>
                    <td>{actor}</td>
                    <td>{action}</td>
                    <td>{category}</td>
                    <td>
                      <StatusBadge
                        variant={
                          result ===
                          "Success"
                            ? "success"
                            : result ===
                                "Warning"
                              ? "warning"
                              : "danger"
                        }
                      >
                        {result}
                      </StatusBadge>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}