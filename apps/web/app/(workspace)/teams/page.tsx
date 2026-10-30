"use client";

import { useState } from "react";

import {
  Plus,
  UserRoundPlus,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";

const initialTeams = [
  {
    name: "Engineering",
    lead: "Dianne Russell",
    members: 32,
  },
  {
    name: "Design",
    lead: "Marvin McKinney",
    members: 14,
  },
  {
    name: "Marketing",
    lead: "Theresa Webb",
    members: 18,
  },
  {
    name: "Sales",
    lead: "Cameron Williamson",
    members: 27,
  },
];

export default function TeamsPage() {
  const [teams, setTeams] =
    useState(initialTeams);

  return (
    <div
      style={{
        maxWidth: 1450,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Teams"
        description="Organize employees into collaborative workspace teams."
        actions={
          <Button
            onClick={() =>
              setTeams((current) => [
                ...current,
                {
                  name: `New Team ${
                    current.length + 1
                  }`,
                  lead: "Unassigned",
                  members: 0,
                },
              ])
            }
          >
            <Plus size={15} />
            Create Team
          </Button>
        }
      />

      <div
        className="metric-grid"
        style={{ marginBottom: 16 }}
      >
        <MetricCard
          label="Teams"
          value={teams.length}
          icon={<Users size={21} />}
          tone="brand"
        />
        <MetricCard
          label="Team Members"
          value="91"
          icon={<Users size={21} />}
        />
        <MetricCard
          label="Team Leads"
          value="8"
          icon={<UserRoundPlus size={21} />}
          tone="success"
        />
        <MetricCard
          label="Open Seats"
          value="12"
          icon={<Users size={21} />}
          tone="warning"
        />
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit,minmax(280px,1fr))",
          gap: 14,
        }}
      >
        {teams.map((team) => (
          <section
            key={team.name}
            className="panel"
            style={{ padding: 18 }}
          >
            <h2
              style={{
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              {team.name}
            </h2>

            <div
              style={{
                marginTop: 16,
              }}
            >
              <span className="text-label">
                Team Lead
              </span>
              <div
                style={{
                  marginTop: 4,
                  fontSize: 12,
                }}
              >
                {team.lead}
              </div>
            </div>

            <div
              style={{
                marginTop: 16,
              }}
            >
              <span className="text-label">
                Members
              </span>
              <div
                style={{
                  marginTop: 4,
                  fontSize: 22,
                }}
              >
                {team.members}
              </div>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}