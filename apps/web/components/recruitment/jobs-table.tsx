"use client";

import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";

import {
  RecruitmentStatus,
} from "@/components/recruitment/recruitment-status";

import type {
  JobResponse,
} from "@/types/recruitment";

interface JobsTableProps {
  jobs: JobResponse[];
  loading?: boolean;
  selectedJobId?: string | null;
  onSelect?: (jobId: string) => void;
  onRefresh?: () => void;
  onEdit?: (job: JobResponse) => void;
}

function closingDate(
  value: string | null | undefined,
): string {
  if (!value) return "—";

  const date = new Date(value);

  return Number.isFinite(date.getTime())
    ? date.toLocaleDateString()
    : "Unknown";
}

export function JobsTable({
  jobs,
  loading = false,
  selectedJobId = null,
  onSelect,
  onRefresh,
  onEdit,
}: JobsTableProps) {
  return (
    <section
      className="panel"
      aria-busy={loading}
    >
      <header
        className="panel-header"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <div>
          <h2>Openings</h2>

          <p className="text-label">
            Live job records from WorkforceOS.
          </p>
        </div>

        {onRefresh ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={loading}
            aria-label="Refresh jobs"
          >
            <RefreshCw size={16} />
          </Button>
        ) : null}
      </header>

      {loading ? (
        <div
          className="panel-body"
          role="status"
        >
          Loading jobs…
        </div>
      ) : jobs.length === 0 ? (
        <div className="panel-body">
          No job openings yet.
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table
            className="data-table"
            style={{
              width: "100%",
              minWidth: 680,
              borderCollapse: "collapse",
            }}
          >
            <thead>
              <tr>
                <th>Position</th>
                <th>Type</th>
                <th>Location</th>
                <th>Closing</th>
                <th>Status</th>

                {onSelect || onEdit ? (
                  <th>Actions</th>
                ) : null}
              </tr>
            </thead>

            <tbody>
              {jobs.map((job) => {
                const selected =
                  selectedJobId === job.id;

                return (
                  <tr
                    key={job.id}
                    aria-selected={selected}
                    onClick={() =>
                      onSelect?.(job.id)
                    }
                    style={{
                      cursor: onSelect
                        ? "pointer"
                        : undefined,
                      background: selected
                        ? "var(--color-muted)"
                        : undefined,
                    }}
                  >
                    <td>
                      <strong>{job.title}</strong>

                      <div className="text-label">
                        {job.description
                          ? job.description.slice(0, 70)
                          : "No description"}
                      </div>
                    </td>

                    <td>
                      {job.employment_type || "—"}
                    </td>

                    <td>
                      {job.location ||
                        "Remote / unspecified"}
                    </td>

                    <td>
                      {closingDate(job.closing_date)}
                    </td>

                    <td>
                      <RecruitmentStatus
                        status={job.status}
                      />
                    </td>

                    {onSelect || onEdit ? (
                      <td>
                        <div
                          style={{
                            display: "flex",
                            gap: 8,
                            flexWrap: "wrap",
                          }}
                        >
                          {onSelect ? (
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              aria-pressed={selected}
                              onClick={(event) => {
                                event.stopPropagation();
                                onSelect(job.id);
                              }}
                            >
                              {selected
                                ? "Selected"
                                : "View details"}
                            </Button>
                          ) : null}

                          {onEdit ? (
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={(event) => {
                                event.stopPropagation();
                                onEdit(job);
                              }}
                            >
                              Edit
                            </Button>
                          ) : null}
                        </div>
                      </td>
                    ) : null}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}