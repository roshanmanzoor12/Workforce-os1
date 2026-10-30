"use client";

import { useState } from "react";

import {
  Clock3,
  Moon,
  Plus,
  Sun,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

const initialShifts = [
  {
    name: "General Shift",
    time: "09:00 - 18:00",
    employees: 128,
    status: "Active",
  },
  {
    name: "Afternoon Shift",
    time: "13:00 - 22:00",
    employees: 64,
    status: "Upcoming",
  },
  {
    name: "Night Shift",
    time: "22:00 - 06:00",
    employees: 42,
    status: "Upcoming",
  },
];

export default function ShiftsPage() {
  const [shifts, setShifts] =
    useState(initialShifts);

  return (
    <div
      style={{
        maxWidth: 1400,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Shift Management"
        description="Create schedules and manage workforce shift assignments."
        actions={
          <Button
            onClick={() =>
              setShifts((current) => [
                ...current,
                {
                  name: `Shift ${
                    current.length + 1
                  }`,
                  time: "09:00 - 17:00",
                  employees: 0,
                  status: "Draft",
                },
              ])
            }
          >
            <Plus size={15} />
            New Shift
          </Button>
        }
      />

      <div
        className="metric-grid"
        style={{ marginBottom: 16 }}
      >
        <MetricCard
          label="Total Shifts"
          value={shifts.length}
          icon={<Clock3 size={21} />}
          tone="brand"
        />
        <MetricCard
          label="Day Shift"
          value="128"
          icon={<Sun size={21} />}
          tone="success"
        />
        <MetricCard
          label="Night Shift"
          value="42"
          icon={<Moon size={21} />}
        />
        <MetricCard
          label="Scheduled Employees"
          value="234"
          icon={<Users size={21} />}
        />
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2 className="text-section-title">
            Shift Schedule
          </h2>
        </div>

        <div className="panel-body">
          {shifts.map((shift) => (
            <div
              key={shift.name}
              style={{
                display: "grid",
                gridTemplateColumns:
                  "1fr 180px 140px 120px",
                gap: 16,
                alignItems: "center",
                padding: "14px 0",
                borderBottom:
                  "1px solid var(--color-border-subtle)",
              }}
            >
              <strong
                style={{ fontSize: 12 }}
              >
                {shift.name}
              </strong>

              <span
                style={{ fontSize: 11 }}
              >
                {shift.time}
              </span>

              <span
                style={{ fontSize: 11 }}
              >
                {shift.employees} employees
              </span>

              <StatusBadge
                variant={
                  shift.status === "Active"
                    ? "success"
                    : shift.status === "Draft"
                      ? "neutral"
                      : "info"
                }
              >
                {shift.status}
              </StatusBadge>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}