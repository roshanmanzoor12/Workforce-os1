"use client";

import { useMemo, useState } from "react";

import {
  AppWindow,
  Clock3,
  Search,
  Users,
} from "lucide-react";

import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { SearchInput } from "@/components/ui/search-input";
import { StatusBadge } from "@/components/ui/status-badge";

const applications = [
  {
    name: "Google Chrome",
    category: "Browser",
    users: 328,
    usage: "486h",
    productive: true,
  },
  {
    name: "Microsoft Excel",
    category: "Productivity",
    users: 214,
    usage: "321h",
    productive: true,
  },
  {
    name: "Slack",
    category: "Communication",
    users: 298,
    usage: "282h",
    productive: true,
  },
  {
    name: "Figma",
    category: "Design",
    users: 86,
    usage: "174h",
    productive: true,
  },
  {
    name: "YouTube",
    category: "Media",
    users: 152,
    usage: "96h",
    productive: false,
  },
  {
    name: "Visual Studio Code",
    category: "Development",
    users: 126,
    usage: "268h",
    productive: true,
  },
];

export default function AppsPage() {
  const [search, setSearch] = useState("");

  const visibleApps = useMemo(
    () =>
      applications.filter((app) =>
        `${app.name} ${app.category}`
          .toLowerCase()
          .includes(search.toLowerCase()),
      ),
    [search],
  );

  return (
    <div
      style={{
        maxWidth: 1600,
        margin: "0 auto",
      }}
    >
      <PageHeader
        title="Applications"
        description="Review application usage across your workforce."
      />

      <div
        className="metric-grid"
        style={{ marginBottom: 16 }}
      >
        <MetricCard
          label="Tracked Applications"
          value="84"
          icon={<AppWindow size={21} />}
          tone="brand"
        />

        <MetricCard
          label="Active Today"
          value="52"
          icon={<AppWindow size={21} />}
          tone="success"
        />

        <MetricCard
          label="Active Users"
          value="328"
          icon={<Users size={21} />}
        />

        <MetricCard
          label="Application Time"
          value="1,842h"
          icon={<Clock3 size={21} />}
          tone="warning"
        />
      </div>

      <section className="panel">
        <div
          className="panel-header"
          style={{
            gap: 18,
          }}
        >
          <h2 className="text-section-title">
            Application Inventory
          </h2>

          <div style={{ width: 280 }}>
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search applications"
            />
          </div>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Application</th>
                <th>Category</th>
                <th>Users</th>
                <th>Total Usage</th>
                <th>Classification</th>
              </tr>
            </thead>

            <tbody>
              {visibleApps.map((app) => (
                <tr key={app.name}>
                  <td>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 9,
                      }}
                    >
                      <span
                        style={{
                          display: "grid",
                          width: 30,
                          height: 30,
                          placeItems: "center",
                          borderRadius: 7,
                          background:
                            "var(--color-brand-soft)",
                          color: "#a87300",
                        }}
                      >
                        <AppWindow size={15} />
                      </span>

                      <strong
                        style={{
                          fontSize: 12,
                        }}
                      >
                        {app.name}
                      </strong>
                    </div>
                  </td>

                  <td>{app.category}</td>
                  <td>{app.users}</td>
                  <td>{app.usage}</td>
                  <td>
                    <StatusBadge
                      variant={
                        app.productive
                          ? "success"
                          : "warning"
                      }
                    >
                      {app.productive
                        ? "Productive"
                        : "Neutral"}
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