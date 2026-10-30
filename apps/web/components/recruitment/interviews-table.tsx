"use client";

import {
  CalendarClock,
  MoreHorizontal,
} from "lucide-react";

import type {
  InterviewResponse,
} from "@/types/recruitment";


interface InterviewsTableProps {
  interviews:
    InterviewResponse[];

  loading:
    boolean;

  onDelete:
    (
      interviewId: string,
    ) => Promise<void>;
}


function statusLabel(
  status:
    InterviewResponse["status"],
) {
  return (
    status
      .replace(
        "_",
        " ",
      )
      .replace(
        /^./,
        (
          value,
        ) =>
          value.toUpperCase(),
      )
  );
}


export function InterviewsTable({
  interviews,

  loading,

  onDelete,
}: InterviewsTableProps) {
  async function remove(
    interview:
      InterviewResponse,
  ) {
    const confirmed =
      window.confirm(
        "Delete this interview record?",
      );


    if (!confirmed) {
      return;
    }


    await onDelete(
      interview.id,
    );
  }


  return (
    <section
      className="panel"
    >
      <header
        className="panel-header"
      >
        <div>
          <h2>
            Interviews
          </h2>

          <p className="text-label">
            Scheduled recruitment interviews for this workspace.
          </p>
        </div>
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
                160,

              display:
                "grid",

              placeItems:
                "center",
            }}
          >
            Loading interviews...
          </div>
        ) : interviews.length ===
          0 ? (
          <div
            className="panel-body"
            style={{
              minHeight:
                160,

              display:
                "grid",

              placeItems:
                "center",

              textAlign:
                "center",
            }}
          >
            <div>
              <CalendarClock
                size={25}
              />

              <p className="text-label">
                No interviews scheduled.
              </p>
            </div>
          </div>
        ) : (
          <table
            style={{
              width:
                "100%",

              minWidth:
                680,

              borderCollapse:
                "collapse",
            }}
          >
            <thead>
              <tr>
                <th>
                  Candidate ID
                </th>

                <th>
                  Starts
                </th>

                <th>
                  Ends
                </th>

                <th>
                  Status
                </th>

                <th>
                  Notes
                </th>

                <th />
              </tr>
            </thead>

            <tbody>
              {interviews.map(
                (
                  interview,
                ) => (
                  <tr
                    key={
                      interview.id
                    }
                  >
                    <td>
                      <code>
                        {
                          interview.candidate_id
                        }
                      </code>
                    </td>

                    <td>
                      {new Date(
                        interview.starts_at,
                      ).toLocaleString()}
                    </td>

                    <td>
                      {interview.ends_at
                        ? new Date(
                            interview.ends_at,
                          ).toLocaleString()
                        : "—"}
                    </td>

                    <td>
                      <span className="status-badge">
                        {
                          statusLabel(
                            interview.status,
                          )
                        }
                      </span>
                    </td>

                    <td>
                      {
                        interview.notes ||
                        "—"
                      }
                    </td>

                    <td>
                      <button
                        type="button"
                        onClick={() =>
                          void remove(
                            interview,
                          )
                        }
                        aria-label="Interview actions"
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