"use client";

import { useState } from "react";

import {
  BriefcaseBusiness,
  Plus,
  UserCheck,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

const candidates = [
  [
    "Olivia Martin",
    "Senior Product Designer",
    "Interview",
  ],
  [
    "Noah Williams",
    "Frontend Developer",
    "Screening",
  ],
  [
    "Emma Davis",
    "HR Specialist",
    "Offer",
  ],
  [
    "Liam Anderson",
    "Backend Developer",
    "Interview",
  ],
  [
    "Sophia Miller",
    "Marketing Manager",
    "Applied",
  ],
];

export default function RecruitmentPage() {
  const [jobs, setJobs] = useState(12);

  return (
    <div
      style={{
        maxWidth: 1600,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Recruitment"
        description="Manage job openings, candidates and hiring pipelines."
        actions={
          <Button
            onClick={() =>
              setJobs((value) => value + 1)
            }
          >
            <Plus size={15} />
            Create Job
          </Button>
        }
      />

      <div
        className="metric-grid"
        style={{ marginBottom: 16 }}
      >
        <MetricCard
          label="Open Roles"
          value={jobs}
          icon={
            <BriefcaseBusiness
              size={21}
            />
          }
          tone="brand"
        />
        <MetricCard
          label="Candidates"
          value="148"
          icon={<Users size={21} />}
        />
        <MetricCard
          label="Interviews"
          value="24"
          icon={<UserCheck size={21} />}
          tone="warning"
        />
        <MetricCard
          label="Offers"
          value="7"
          icon={<UserCheck size={21} />}
          tone="success"
        />
      </div>

      <section
        className="panel"
        style={{ overflow: "hidden" }}
      >
        <div className="panel-header">
          <h2 className="text-section-title">
            Candidate Pipeline
          </h2>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Role</th>
                <th>Stage</th>
              </tr>
            </thead>

            <tbody>
              {candidates.map(
                ([candidate, role, stage]) => (
                  <tr key={candidate}>
                    <td>{candidate}</td>
                    <td>{role}</td>
                    <td>
                      <StatusBadge
                        variant={
                          stage === "Offer"
                            ? "success"
                            : stage ===
                                "Interview"
                              ? "warning"
                              : stage ===
                                  "Screening"
                                ? "info"
                                : "neutral"
                        }
                      >
                        {stage}
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