"use client";

import {
  MoreHorizontal,
  RefreshCw,
} from "lucide-react";

import type {
  CandidateResponse,
} from "@/types/recruitment";


interface CandidatesTableProps {
  candidates:
    CandidateResponse[];

  loading:
    boolean;

  onRefresh:
    () => void;
}


function statusLabel(
  status:
    CandidateResponse["status"],
) {
  return (
    status
      .charAt(0)
      .toUpperCase() +
    status.slice(1)
  );
}


export function CandidatesTable({
  candidates,

  loading,

  onRefresh,
}: CandidatesTableProps) {
  return (
    <section
      className="panel"
    >
      <header
        className="panel-header"
        style={{
          display:
            "flex",

          justifyContent:
            "space-between",

          alignItems:
            "center",

          gap:
            12,
        }}
      >
        <div>
          <h2>
            Candidates
          </h2>

          <p className="text-label">
            Candidates currently stored in this workspace.
          </p>
        </div>

        <button
          type="button"
          onClick={
            onRefresh
          }
          disabled={
            loading
          }
          aria-label="Refresh candidates"
          title="Refresh candidates"
          style={{
            width:
              36,

            height:
              36,

            display:
              "grid",

            placeItems:
              "center",

            border:
              "1px solid var(--color-border)",

            borderRadius:
              8,

            background:
              "var(--color-surface)",

            cursor:
              "pointer",
          }}
        >
          <RefreshCw
            size={16}
            className={
              loading
                ? "spin"
                : undefined
            }
          />
        </button>
      </header>

      <div
        style={{
          overflowX:
            "auto",
        }}
      >
        {loading ? (
          <div
            className="panel-body text-label"
            style={{
              minHeight:
                180,

              display:
                "grid",

              placeItems:
                "center",
            }}
          >
            Loading candidates...
          </div>
        ) : candidates.length ===
          0 ? (
          <div
            className="panel-body text-label"
            style={{
              minHeight:
                180,

              display:
                "grid",

              placeItems:
                "center",

              textAlign:
                "center",
            }}
          >
            No candidates found for the selected job.
          </div>
        ) : (
          <table
            style={{
              width:
                "100%",

              minWidth:
                700,

              borderCollapse:
                "collapse",
            }}
          >
            <thead>
              <tr>
                <th>
                  Candidate
                </th>

                <th>
                  Email
                </th>

                <th>
                  Phone
                </th>

                <th>
                  Status
                </th>

                <th>
                  Resume
                </th>

                <th />
              </tr>
            </thead>

            <tbody>
              {candidates.map(
                (
                  candidate,
                ) => (
                  <tr
                    key={
                      candidate.id
                    }
                  >
                    <td>
                      <strong>
                        {
                          candidate.first_name
                        }{" "}
                        {
                          candidate.last_name
                        }
                      </strong>

                      {candidate.notes ? (
                        <div className="text-label">
                          {
                            candidate.notes.slice(
                              0,
                              65,
                            )
                          }
                        </div>
                      ) : null}
                    </td>

                    <td>
                      {
                        candidate.email
                      }
                    </td>

                    <td>
                      {
                        candidate.phone ||
                        "—"
                      }
                    </td>

                    <td>
                      <span className="status-badge">
                        {
                          statusLabel(
                            candidate.status,
                          )
                        }
                      </span>
                    </td>

                    <td>
                      {candidate.resume_url ? (
                        <a
                          href={
                            candidate.resume_url
                          }
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>

                    <td>
                      <button
                        type="button"
                        aria-label={`Actions for ${candidate.first_name} ${candidate.last_name}`}
                        style={{
                          width:
                            32,

                          height:
                            32,

                          display:
                            "grid",

                          placeItems:
                            "center",

                          border:
                            0,

                          borderRadius:
                            7,

                          background:
                            "transparent",

                          cursor:
                            "pointer",
                        }}
                      >
                        <MoreHorizontal
                          size={17}
                        />
                      </button>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}