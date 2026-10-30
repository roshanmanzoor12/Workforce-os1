"use client";

import { CalendarDays, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

const holidays = [
  ["New Year's Day", "Jan 1, 2026", "Company Holiday"],
  ["Memorial Day", "May 25, 2026", "Public Holiday"],
  ["Independence Day", "Jul 4, 2026", "Public Holiday"],
  ["Labor Day", "Sep 7, 2026", "Public Holiday"],
  ["Thanksgiving", "Nov 26, 2026", "Company Holiday"],
  ["Christmas Day", "Dec 25, 2026", "Company Holiday"],
];

export default function HolidaysPage() {
  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      <PageHeader
        title="Holidays"
        description="Manage company holidays and workforce calendar policies."
        actions={
          <Button>
            <Plus size={15} />
            Add Holiday
          </Button>
        }
      />

      <div
        className="metric-grid"
        style={{ marginBottom: 16 }}
      >
        <MetricCard
          label="Company Holidays"
          value="6"
          icon={<CalendarDays size={21} />}
          tone="brand"
        />

        <MetricCard
          label="Upcoming"
          value="3"
          icon={<CalendarDays size={21} />}
          tone="warning"
        />

        <MetricCard
          label="Locations"
          value="4"
          icon={<CalendarDays size={21} />}
        />

        <MetricCard
          label="Holiday Policies"
          value="3"
          icon={<CalendarDays size={21} />}
          tone="success"
        />
      </div>

      <section className="panel" style={{ overflow: "hidden" }}>
        <div className="panel-header">
          <h2 className="text-section-title">
            Holiday Calendar
          </h2>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Holiday</th>
                <th>Date</th>
                <th>Type</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {holidays.map(([name, date, type]) => (
                <tr key={name}>
                  <td>{name}</td>
                  <td>{date}</td>
                  <td>{type}</td>
                  <td>
                    <StatusBadge variant="success">
                      Active
                    </StatusBadge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}