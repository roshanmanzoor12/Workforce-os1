"use client";

import { useState } from "react";

import {
  CalendarDays,
  CheckCircle2,
  FolderKanban,
  Plus,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

const initialProjects = [
  {
    name: "Workforce OS Web",
    team: "Product",
    progress: 74,
    deadline: "Jun 14",
  },
  {
    name: "Employee Agent",
    team: "Engineering",
    progress: 62,
    deadline: "Jun 28",
  },
  {
    name: "Q2 Website Refresh",
    team: "Design",
    progress: 91,
    deadline: "May 30",
  },
  {
    name: "Payroll Automation",
    team: "Finance",
    progress: 48,
    deadline: "Jul 12",
  },
];

export default function ProjectsPage() {
  const [projects, setProjects] =
    useState(initialProjects);

  function addProject() {
    setProjects((current) => [
      ...current,
      {
        name: `New Project ${current.length + 1}`,
        team: "General",
        progress: 0,
        deadline: "TBD",
      },
    ]);
  }

  return (
    <div
      style={{
        maxWidth: 1600,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Projects"
        description="Plan initiatives, coordinate teams and track project delivery."
        actions={
          <Button onClick={addProject}>
            <Plus size={15} />
            New Project
          </Button>
        }
      />

      <div
        className="metric-grid"
        style={{ marginBottom: 16 }}
      >
        <MetricCard
          label="Active Projects"
          value={projects.length}
          icon={
            <FolderKanban size={21} />
          }
          tone="brand"
        />
        <MetricCard
          label="On Track"
          value="8"
          icon={
            <CheckCircle2 size={21} />
          }
          tone="success"
        />
        <MetricCard
          label="Team Members"
          value="46"
          icon={<Users size={21} />}
        />
        <MetricCard
          label="Due This Month"
          value="5"
          icon={
            <CalendarDays size={21} />
          }
          tone="warning"
        />
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit,minmax(320px,1fr))",
          gap: 14,
        }}
      >
        {projects.map((project) => (
          <section
            key={project.name}
            className="panel"
            style={{ padding: 18 }}
          >
            <div
              style={{
                display: "flex",
                justifyContent:
                  "space-between",
                gap: 10,
              }}
            >
              <div>
                <h2
                  style={{
                    color:
                      "var(--color-ink)",
                    fontSize: 14,
                    fontWeight: 600,
                  }}
                >
                  {project.name}
                </h2>

                <p
                  className="text-label"
                  style={{ marginTop: 4 }}
                >
                  {project.team}
                </p>
              </div>

              <StatusBadge
                variant={
                  project.progress >= 80
                    ? "success"
                    : project.progress >= 50
                      ? "warning"
                      : "info"
                }
              >
                {project.progress}%
              </StatusBadge>
            </div>

            <div
              style={{
                marginTop: 20,
              }}
            >
              <div
                style={{
                  height: 7,
                  borderRadius: 999,
                  background: "#ece8df",
                }}
              >
                <div
                  style={{
                    width: `${project.progress}%`,
                    height: "100%",
                    borderRadius: 999,
                    background:
                      "var(--color-brand)",
                  }}
                />
              </div>
            </div>

            <div
              style={{
                display: "flex",
                justifyContent:
                  "space-between",
                marginTop: 18,
              }}
            >
              <span className="text-label">
                Deadline
              </span>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                }}
              >
                {project.deadline}
              </span>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}