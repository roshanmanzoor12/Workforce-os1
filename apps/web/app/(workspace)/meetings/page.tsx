"use client";

import {
  CalendarClock,
  Check,
  CheckCircle2,
  Clock3,
  MapPin,
  Mic,
  MonitorPlay,
  Plus,
  RefreshCcw,
  Search,
  Square,
  UserPlus,
  Users,
  Video,
  X,
  XCircle,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  WorkspaceRequired,
} from "@/components/workspace/workspace-required";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  employeesService,
  type Employee,
} from "@/services/employees.service";

import {
  meetingsService,
} from "@/services/meetings.service";

import type {
  MeetingInvitationPublic,
  MeetingParticipantPublic,
  MeetingPublic,
  MeetingStatus,
  MeetingType,
} from "@/types/meetings";


type ViewMode =
  | "meetings"
  | "invitations";


function formatDateTime(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }


  const date =
    new Date(
      value,
    );


  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }


  return date.toLocaleString();
}


function pretty(
  value: string,
): string {
  return value
    .replace(
      /_/g,
      " ",
    )
    .split(" ")
    .filter(Boolean)
    .map(
      (
        part,
      ) =>
        part
          .charAt(0)
          .toUpperCase() +
        part.slice(1),
    )
    .join(" ");
}


function toLocalInputValue(
  value: string,
): string {
  const date =
    new Date(value);


  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "";
  }


  const offset =
    date.getTimezoneOffset() *
    60000;


  return new Date(
    date.getTime() -
      offset,
  )
    .toISOString()
    .slice(
      0,
      16,
    );
}


export default function MeetingsPage() {
  return (
    <WorkspaceRequired>
      <MeetingsContent />
    </WorkspaceRequired>
  );
}


function MeetingsContent() {
  const {
    workspaceId,
    workspace,
  } =
    useWorkspace();


  const [
    meetings,
    setMeetings,
  ] =
    useState<MeetingPublic[]>(
      [],
    );


  const [
    invitations,
    setInvitations,
  ] =
    useState<MeetingInvitationPublic[]>(
      [],
    );


  const [
    employees,
    setEmployees,
  ] =
    useState<Employee[]>(
      [],
    );


  const [
    selectedMeetingId,
    setSelectedMeetingId,
  ] =
    useState<string | null>(
      null,
    );


  const [
    participants,
    setParticipants,
  ] =
    useState<MeetingParticipantPublic[]>(
      [],
    );


  const [
    view,
    setView,
  ] =
    useState<ViewMode>(
      "meetings",
    );


  const [
    search,
    setSearch,
  ] =
    useState(
      "",
    );


  const [
    statusFilter,
    setStatusFilter,
  ] =
    useState<
      MeetingStatus |
      "all"
    >(
      "all",
    );


  const [
    showCreate,
    setShowCreate,
  ] =
    useState(
      false,
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    detailLoading,
    setDetailLoading,
  ] =
    useState(
      false,
    );


  const [
    action,
    setAction,
  ] =
    useState<string | null>(
      null,
    );


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  const [
    success,
    setSuccess,
  ] =
    useState<string | null>(
      null,
    );


  const load =
    useCallback(
      async () => {
        if (
          !workspaceId
        ) {
          setLoading(
            false,
          );

          return;
        }


        try {
          setLoading(
            true,
          );

          setError(
            null,
          );


          const [
            meetingsResponse,
            invitationsResponse,
            employeesResponse,
          ] =
            await Promise.all([
              meetingsService.list(
                workspaceId,
              ),

              meetingsService.listMyInvitations(
                workspaceId,
              ),

              employeesService.list(
                workspaceId,
                {
                  includeInactive:
                    false,
                },
              ),
            ]);


          const meetingItems =
            meetingsResponse.meetings ??
            [];


          setMeetings(
            meetingItems,
          );


          setInvitations(
            invitationsResponse.invitations ??
              [],
          );


          setEmployees(
            employeesResponse.employees,
          );


          setSelectedMeetingId(
            (
              current,
            ) =>
              current &&
              meetingItems.some(
                (
                  item,
                ) =>
                  item.id ===
                  current,
              )
                ? current
                : meetingItems[0]?.id ??
                  null,
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load meetings.",
          );

        } finally {
          setLoading(
            false,
          );
        }
      },
      [
        workspaceId,
      ],
    );


  useEffect(
    () => {
      void load();
    },
    [
      load,
    ],
  );


  const selectedMeeting =
    useMemo(
      () =>
        meetings.find(
          (
            item,
          ) =>
            item.id ===
            selectedMeetingId,
        ) ??
        null,
      [
        meetings,
        selectedMeetingId,
      ],
    );


  useEffect(
    () => {
      if (
        !workspaceId ||
        !selectedMeetingId
      ) {
        setParticipants(
          [],
        );

        return;
      }


      async function loadDetail() {
        try {
          setDetailLoading(
            true,
          );


          const response =
            await meetingsService.get(
              workspaceId!,
              selectedMeetingId!,
            );


          setParticipants(
            response.participants ??
              [],
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load meeting details.",
          );

        } finally {
          setDetailLoading(
            false,
          );
        }
      }


      void loadDetail();
    },
    [
      workspaceId,
      selectedMeetingId,
    ],
  );


  const employeeMap =
    useMemo(
      () =>
        new Map(
          employees.map(
            (
              employee,
            ) => [
              employee.id,
              employee,
            ],
          ),
        ),
      [
        employees,
      ],
    );


  const filteredMeetings =
    useMemo(
      () => {
        const query =
          search
            .trim()
            .toLowerCase();


        return meetings.filter(
          (
            meeting,
          ) => {
            if (
              statusFilter !==
                "all" &&
              meeting.status !==
                statusFilter
            ) {
              return false;
            }


            if (
              !query
            ) {
              return true;
            }


            return [
              meeting.title,
              meeting.description ??
                "",
              meeting.location ??
                "",
              meeting.meeting_type,
              meeting.status,
            ]
              .join(" ")
              .toLowerCase()
              .includes(
                query,
              );
          },
        );
      },
      [
        meetings,
        search,
        statusFilter,
      ],
    );


  const pendingInvitationCount =
    invitations.filter(
      (
        invitation,
      ) =>
        invitation.participant_status ===
        "invited",
    ).length;


  async function refreshMeeting(
    meetingId: string,
  ) {
    if (
      !workspaceId
    ) {
      return;
    }


    const detail =
      await meetingsService.get(
        workspaceId,
        meetingId,
      );


    setMeetings(
      (
        current,
      ) =>
        current.map(
          (
            item,
          ) =>
            item.id ===
            detail.meeting.id
              ? detail.meeting
              : item,
        ),
    );


    setParticipants(
      detail.participants ??
        [],
    );
  }


  async function meetingAction(
    type:
      | "start"
      | "end"
      | "cancel",
  ) {
    if (
      !workspaceId ||
      !selectedMeeting ||
      action
    ) {
      return;
    }


    if (
      type ===
        "cancel" &&
      !window.confirm(
        `Cancel "${selectedMeeting.title}"?`,
      )
    ) {
      return;
    }


    try {
      setAction(
        type,
      );

      setError(
        null,
      );


      const response =
        type ===
        "start"
          ? await meetingsService.start(
              workspaceId,
              selectedMeeting.id,
            )
          : type ===
              "end"
            ? await meetingsService.end(
                workspaceId,
                selectedMeeting.id,
              )
            : await meetingsService.cancel(
                workspaceId,
                selectedMeeting.id,
              );


      setMeetings(
        (
          current,
        ) =>
          current.map(
            (
              item,
            ) =>
              item.id ===
              response.meeting.id
                ? response.meeting
                : item,
          ),
      );


      setSuccess(
        response.message,
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to update meeting.",
      );

    } finally {
      setAction(
        null,
      );
    }
  }


  async function respond(
    invitation:
      MeetingInvitationPublic,

    responseStatus:
      "accepted" |
      "declined",
  ) {
    if (
      !workspaceId ||
      action
    ) {
      return;
    }


    try {
      setAction(
        invitation.meeting_id,
      );


      const response =
        await meetingsService.respondToInvitation(
          workspaceId,
          invitation.meeting_id,
          responseStatus,
        );


      setInvitations(
        (
          current,
        ) =>
          current.map(
            (
              item,
            ) =>
              item.meeting_id ===
              invitation.meeting_id
                ? {
                    ...item,

                    participant_status:
                      response.participant.status,
                  }
                : item,
          ),
      );


      setSuccess(
        response.message,
      );


      await load();

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to respond to meeting invitation.",
      );

    } finally {
      setAction(
        null,
      );
    }
  }


  async function addParticipant(
    employeeId: string,
  ) {
    if (
      !workspaceId ||
      !selectedMeeting ||
      !employeeId ||
      action
    ) {
      return;
    }


    try {
      setAction(
        "participant",
      );


      await meetingsService.addParticipant(
        workspaceId,
        selectedMeeting.id,
        {
          employee_id:
            employeeId,

          participant_role:
            "participant",
        },
      );


      await refreshMeeting(
        selectedMeeting.id,
      );


      setSuccess(
        "Participant added.",
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to add participant.",
      );

    } finally {
      setAction(
        null,
      );
    }
  }


  async function removeParticipant(
    employeeId: string,
  ) {
    if (
      !workspaceId ||
      !selectedMeeting ||
      action
    ) {
      return;
    }


    try {
      setAction(
        employeeId,
      );


      await meetingsService.removeParticipant(
        workspaceId,
        selectedMeeting.id,
        employeeId,
      );


      await refreshMeeting(
        selectedMeeting.id,
      );


      setSuccess(
        "Participant removed.",
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to remove participant.",
      );

    } finally {
      setAction(
        null,
      );
    }
  }


  return (
    <div
      style={{
        display:
          "grid",

        gap:
          16,
      }}
    >
      <header
        style={{
          display:
            "flex",

          justifyContent:
            "space-between",

          alignItems:
            "flex-start",

          gap:
            14,
        }}
      >
        <div>
          <div
            style={{
              display:
                "flex",

              alignItems:
                "center",

              gap:
                6,

              color:
                "#9a7000",

              fontSize:
                10,

              fontWeight:
                600,
            }}
          >
            <CalendarClock
              size={
                13
              }
            />

            Workspace Meetings
          </div>


          <h1
            style={{
              marginTop:
                5,
            }}
          >
            Meetings
          </h1>


          <p
            className="text-label"
            style={{
              marginTop:
                4,
            }}
          >
            Schedule and manage meetings for{" "}
            {workspace?.name ??
              "this workspace"}.
          </p>
        </div>


        <div
          style={{
            display:
              "flex",

            gap:
              8,
          }}
        >
          <button
            type="button"
            className="button button--outline"
            onClick={() => {
              void load();
            }}
          >
            <RefreshCcw
              size={
                14
              }
            />

            Refresh
          </button>


          <button
            type="button"
            className="button button--primary"
            onClick={() =>
              setShowCreate(
                true,
              )
            }
          >
            <Plus
              size={
                14
              }
            />

            New Meeting
          </button>
        </div>
      </header>


      {error ? (
        <div
          style={errorStyle}
        >
          {error}
        </div>
      ) : null}


      {success ? (
        <div
          style={successStyle}
        >
          <CheckCircle2
            size={
              14
            }
          />

          {success}
        </div>
      ) : null}


      <div
        style={{
          display:
            "flex",

          gap:
            7,
        }}
      >
        <button
          type="button"
          className={
            view ===
            "meetings"
              ? "button button--primary"
              : "button button--outline"
          }
          onClick={() =>
            setView(
              "meetings",
            )
          }
        >
          <CalendarClock
            size={
              13
            }
          />

          Meetings
        </button>


        <button
          type="button"
          className={
            view ===
            "invitations"
              ? "button button--primary"
              : "button button--outline"
          }
          onClick={() =>
            setView(
              "invitations",
            )
          }
        >
          <Users
            size={
              13
            }
          />

          Invitations
          {pendingInvitationCount >
          0
            ? ` (${pendingInvitationCount})`
            : ""}
        </button>
      </div>


      {view ===
      "invitations" ? (
        <InvitationPanel
          invitations={
            invitations
          }
          action={
            action
          }
          onRespond={
            respond
          }
        />
      ) : (
        <>
          <section
            className="panel"
          >
            <div
              style={{
                display:
                  "grid",

                gridTemplateColumns:
                  "minmax(260px, 1fr) 180px",

                gap:
                  9,

                padding:
                  12,

                borderBottom:
                  "1px solid var(--color-border)",
              }}
            >
              <label
                style={{
                  position:
                    "relative",
                }}
              >
                <Search
                  size={
                    14
                  }
                  style={{
                    position:
                      "absolute",

                    left:
                      10,

                    top:
                      10,

                    color:
                      "#85878a",
                  }}
                />

                <input
                  value={
                    search
                  }
                  placeholder="Search meetings"
                  onChange={(
                    event,
                  ) =>
                    setSearch(
                      event.target.value,
                    )
                  }
                  style={{
                    ...inputStyle,

                    paddingLeft:
                      32,
                  }}
                />
              </label>


              <select
                value={
                  statusFilter
                }
                onChange={(
                  event,
                ) =>
                  setStatusFilter(
                    event.target.value as
                      | MeetingStatus
                      | "all",
                  )
                }
                style={inputStyle}
              >
                <option value="all">
                  All statuses
                </option>

                <option value="scheduled">
                  Scheduled
                </option>

                <option value="active">
                  Active
                </option>

                <option value="completed">
                  Completed
                </option>

                <option value="cancelled">
                  Cancelled
                </option>
              </select>
            </div>


            {loading ? (
              <div
                className="skeleton"
                style={{
                  height:
                    330,

                  margin:
                    14,
                }}
              />
            ) : filteredMeetings.length ===
              0 ? (
              <div
                style={{
                  padding:
                    36,

                  textAlign:
                    "center",

                  color:
                    "#777a7c",

                  fontSize:
                    10,
                }}
              >
                No meetings found.
              </div>
            ) : (
              <div
                style={{
                  display:
                    "grid",

                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(290px, 1fr))",

                  gap:
                    10,

                  padding:
                    12,
                }}
              >
                {filteredMeetings.map(
                  (
                    meeting,
                  ) => (
                    <MeetingCard
                      key={
                        meeting.id
                      }
                      meeting={
                        meeting
                      }
                      selected={
                        meeting.id ===
                        selectedMeetingId
                      }
                      onSelect={() =>
                        setSelectedMeetingId(
                          meeting.id,
                        )
                      }
                    />
                  ),
                )}
              </div>
            )}
          </section>


          {selectedMeeting ? (
            <MeetingDetail
              meeting={
                selectedMeeting
              }
              participants={
                participants
              }
              employees={
                employees
              }
              employeeMap={
                employeeMap
              }
              loading={
                detailLoading
              }
              action={
                action
              }
              onStart={() => {
                void meetingAction(
                  "start",
                );
              }}
              onEnd={() => {
                void meetingAction(
                  "end",
                );
              }}
              onCancel={() => {
                void meetingAction(
                  "cancel",
                );
              }}
              onAddParticipant={(
                employeeId,
              ) => {
                void addParticipant(
                  employeeId,
                );
              }}
              onRemoveParticipant={(
                employeeId,
              ) => {
                void removeParticipant(
                  employeeId,
                );
              }}
            />
          ) : null}
        </>
      )}


      {showCreate ? (
        <CreateMeetingModal
          employees={
            employees
          }
          workspaceId={
            workspaceId
          }
          onClose={() =>
            setShowCreate(
              false,
            )
          }
          onCreated={async (
            meeting,
          ) => {
            setShowCreate(
              false,
            );

            await load();

            setSelectedMeetingId(
              meeting.id,
            );
          }}
        />
      ) : null}
    </div>
  );
}


function MeetingCard({
  meeting,
  selected,
  onSelect,
}: {
  meeting:
    MeetingPublic;

  selected:
    boolean;

  onSelect:
    () => void;
}) {
  return (
    <button
      type="button"
      onClick={
        onSelect
      }
      style={{
        padding:
          13,

        border:
          selected
            ? "1px solid #b78b14"
            : "1px solid var(--color-border)",

        borderRadius:
          8,

        background:
          selected
            ? "#fff9e8"
            : "#fffefa",

        color:
          "inherit",

        textAlign:
          "left",

        cursor:
          "pointer",
      }}
    >
      <div
        style={{
          display:
            "flex",

          justifyContent:
            "space-between",

          gap:
            8,
        }}
      >
        <strong
          style={{
            fontSize:
              10,
          }}
        >
          {meeting.title}
        </strong>


        <StatusPill
          status={
            meeting.status
          }
        />
      </div>


      <div
        className="text-label"
        style={{
          marginTop:
            8,

          lineHeight:
            1.6,
        }}
      >
        <Clock3
          size={
            10
          }
          style={{
            marginRight:
              4,
          }}
        />

        {formatDateTime(
          meeting.scheduled_start_at,
        )}
      </div>


      <div
        className="text-label"
        style={{
          marginTop:
            4,

          textTransform:
            "capitalize",
        }}
      >
        {pretty(
          meeting.meeting_type,
        )}

        {meeting.location
          ? ` · ${meeting.location}`
          : ""}
      </div>
    </button>
  );
}


function MeetingDetail({
  meeting,
  participants,
  employees,
  employeeMap,
  loading,
  action,
  onStart,
  onEnd,
  onCancel,
  onAddParticipant,
  onRemoveParticipant,
}: {
  meeting:
    MeetingPublic;

  participants:
    MeetingParticipantPublic[];

  employees:
    Employee[];

  employeeMap:
    Map<
      string,
      Employee
    >;

  loading:
    boolean;

  action:
    string | null;

  onStart:
    () => void;

  onEnd:
    () => void;

  onCancel:
    () => void;

  onAddParticipant:
    (
      employeeId:
        string,
    ) => void;

  onRemoveParticipant:
    (
      employeeId:
        string,
    ) => void;
}) {
  const participantIds =
    new Set(
      participants.map(
        (
          item,
        ) =>
          item.employee_id,
      ),
    );


  const availableEmployees =
    employees.filter(
      (
        employee,
      ) =>
        !participantIds.has(
          employee.id,
        ),
    );


  return (
    <section
      className="panel"
    >
      <div
        style={{
          display:
            "flex",

          justifyContent:
            "space-between",

          gap:
            12,

          padding:
            "11px 14px",

          borderBottom:
            "1px solid var(--color-border)",
        }}
      >
        <div>
          <strong>
            {meeting.title}
          </strong>

          <div
            className="text-label"
            style={{
              marginTop:
                3,
            }}
          >
            Meeting details
          </div>
        </div>


        <div
          style={{
            display:
              "flex",

            gap:
              7,
          }}
        >
          {meeting.status ===
          "scheduled" ? (
            <>
              <button
                type="button"
                className="button button--primary"
                disabled={
                  action !==
                  null
                }
                onClick={
                  onStart
                }
              >
                <MonitorPlay
                  size={
                    13
                  }
                />

                Start
              </button>


              <button
                type="button"
                className="button button--outline"
                disabled={
                  action !==
                  null
                }
                onClick={
                  onCancel
                }
              >
                <XCircle
                  size={
                    13
                  }
                />

                Cancel
              </button>
            </>
          ) : null}


          {meeting.status ===
          "active" ? (
            <button
              type="button"
              className="button button--primary"
              disabled={
                action !==
                null
              }
              onClick={
                onEnd
              }
            >
              <Square
                size={
                  13
                }
              />

              End Meeting
            </button>
          ) : null}
        </div>
      </div>


      <div
        className="panel-body"
        style={{
          display:
            "grid",

          gridTemplateColumns:
            "minmax(0, 1fr) 360px",

          gap:
            14,

          padding:
            14,
        }}
      >
        <div
          style={{
            display:
              "grid",

            alignContent:
              "start",

            gap:
              10,
          }}
        >
          <Detail
            label="Description"
            value={
              meeting.description ??
              "No description"
            }
          />


          <div
            style={{
              display:
                "grid",

              gridTemplateColumns:
                "1fr 1fr",

              gap:
                8,
            }}
          >
            <Detail
              label="Type"
              value={
                pretty(
                  meeting.meeting_type,
                )
              }
            />

            <Detail
              label="Status"
              value={
                pretty(
                  meeting.status,
                )
              }
            />

            <Detail
              label="Scheduled Start"
              value={
                formatDateTime(
                  meeting.scheduled_start_at,
                )
              }
            />

            <Detail
              label="Scheduled End"
              value={
                formatDateTime(
                  meeting.scheduled_end_at,
                )
              }
            />

            <Detail
              label="Started"
              value={
                formatDateTime(
                  meeting.started_at,
                )
              }
            />

            <Detail
              label="Ended"
              value={
                formatDateTime(
                  meeting.ended_at,
                )
              }
            />

            <Detail
              label="Location"
              value={
                meeting.location ??
                "—"
              }
            />
          </div>
        </div>


        <div
          style={{
            display:
              "grid",

            alignContent:
              "start",

            gap:
              10,

            padding:
              12,

            border:
              "1px solid var(--color-border)",

            borderRadius:
              8,

            background:
              "#faf8f3",
          }}
        >
          <strong>
            Participants
          </strong>


          {availableEmployees.length >
          0 ? (
            <select
              defaultValue=""
              disabled={
                action !==
                null
              }
              onChange={(
                event,
              ) => {
                const employeeId =
                  event.target.value;

                if (
                  employeeId
                ) {
                  onAddParticipant(
                    employeeId,
                  );

                  event.currentTarget.value =
                    "";
                }
              }}
              style={inputStyle}
            >
              <option value="">
                + Add participant
              </option>


              {availableEmployees.map(
                (
                  employee,
                ) => (
                  <option
                    key={
                      employee.id
                    }
                    value={
                      employee.id
                    }
                  >
                    {employee.full_name} · {employee.employee_code}
                  </option>
                ),
              )}
            </select>
          ) : null}


          {loading ? (
            <div
              className="skeleton"
              style={{
                height:
                  160,
              }}
            />
          ) : participants.length ===
            0 ? (
            <div
              className="text-label"
            >
              No participants.
            </div>
          ) : (
            participants.map(
              (
                participant,
              ) => {
                const employee =
                  employeeMap.get(
                    participant.employee_id,
                  );


                return (
                  <div
                    key={
                      participant.id
                    }
                    style={{
                      display:
                        "grid",

                      gridTemplateColumns:
                        "minmax(0, 1fr) auto",

                      gap:
                        8,

                      alignItems:
                        "center",

                      padding:
                        9,

                      border:
                        "1px solid #ebe6dc",

                      borderRadius:
                        7,

                      background:
                        "#fffefa",
                    }}
                  >
                    <div>
                      <strong
                        style={{
                          display:
                            "block",

                          fontSize:
                            9,
                        }}
                      >
                        {employee?.full_name ??
                          participant.employee_id}
                      </strong>


                      <div
                        className="text-label"
                        style={{
                          marginTop:
                            2,

                          fontSize:
                            7,

                          textTransform:
                            "capitalize",
                        }}
                      >
                        {participant.participant_role}
                        {" · "}
                        {participant.status}
                      </div>
                    </div>


                    {participant.participant_role !==
                    "organizer" ? (
                      <button
                        type="button"
                        className="button button--outline"
                        disabled={
                          action !==
                          null
                        }
                        onClick={() =>
                          onRemoveParticipant(
                            participant.employee_id,
                          )
                        }
                      >
                        <X
                          size={
                            12
                          }
                        />
                      </button>
                    ) : null}
                  </div>
                );
              },
            )
          )}
        </div>
      </div>
    </section>
  );
}


function InvitationPanel({
  invitations,
  action,
  onRespond,
}: {
  invitations:
    MeetingInvitationPublic[];

  action:
    string | null;

  onRespond:
    (
      invitation:
        MeetingInvitationPublic,

      status:
        "accepted" |
        "declined",
    ) => Promise<void>;
}) {
  return (
    <section
      className="panel"
    >
      <div
        style={{
          padding:
            "11px 14px",

          borderBottom:
            "1px solid var(--color-border)",
        }}
      >
        <strong>
          My Meeting Invitations
        </strong>

        <p
          className="text-label"
          style={{
            marginTop:
              3,
          }}
        >
          Accept or decline meetings assigned to your employee account.
        </p>
      </div>


      {invitations.length ===
      0 ? (
        <div
          style={{
            padding:
              36,

            textAlign:
              "center",

            color:
              "#777a7c",

            fontSize:
              10,
          }}
        >
          No meeting invitations.
        </div>
      ) : (
        <div
          style={{
            display:
              "grid",

            gap:
              9,

            padding:
              12,
          }}
        >
          {invitations.map(
            (
              invitation,
            ) => (
              <div
                key={
                  invitation.meeting_id
                }
                style={{
                  display:
                    "grid",

                  gridTemplateColumns:
                    "minmax(0, 1fr) auto",

                  gap:
                    12,

                  alignItems:
                    "center",

                  padding:
                    12,

                  border:
                    "1px solid var(--color-border)",

                  borderRadius:
                    8,
                }}
              >
                <div>
                  <strong>
                    {invitation.title}
                  </strong>


                  <div
                    className="text-label"
                    style={{
                      marginTop:
                        4,
                    }}
                  >
                    {pretty(
                      invitation.meeting_type,
                    )}
                    {" · "}
                    {formatDateTime(
                      invitation.scheduled_start_at,
                    )}
                  </div>


                  <div
                    style={{
                      marginTop:
                        6,

                      fontSize:
                        8,

                      textTransform:
                        "capitalize",
                    }}
                  >
                    Response:{" "}
                    <strong>
                      {invitation.participant_status}
                    </strong>
                  </div>
                </div>


                {invitation.participant_status ===
                "invited" ? (
                  <div
                    style={{
                      display:
                        "flex",

                      gap:
                        7,
                    }}
                  >
                    <button
                      type="button"
                      className="button button--outline"
                      disabled={
                        action ===
                        invitation.meeting_id
                      }
                      onClick={() => {
                        void onRespond(
                          invitation,
                          "declined",
                        );
                      }}
                    >
                      <XCircle
                        size={
                          13
                        }
                      />

                      Decline
                    </button>


                    <button
                      type="button"
                      className="button button--primary"
                      disabled={
                        action ===
                        invitation.meeting_id
                      }
                      onClick={() => {
                        void onRespond(
                          invitation,
                          "accepted",
                        );
                      }}
                    >
                      <Check
                        size={
                          13
                        }
                      />

                      Accept
                    </button>
                  </div>
                ) : null}
              </div>
            ),
          )}
        </div>
      )}
    </section>
  );
}


function CreateMeetingModal({
  employees,
  workspaceId,
  onClose,
  onCreated,
}: {
  employees:
    Employee[];

  workspaceId:
    string | null;

  onClose:
    () => void;

  onCreated:
    (
      meeting:
        MeetingPublic,
    ) => Promise<void>;
}) {
  const [
    title,
    setTitle,
  ] =
    useState(
      "",
    );


  const [
    description,
    setDescription,
  ] =
    useState(
      "",
    );


  const [
    meetingType,
    setMeetingType,
  ] =
    useState<MeetingType>(
      "video",
    );


  const [
    scheduledStart,
    setScheduledStart,
  ] =
    useState(
      "",
    );


  const [
    scheduledEnd,
    setScheduledEnd,
  ] =
    useState(
      "",
    );


  const [
    location,
    setLocation,
  ] =
    useState(
      "",
    );


  const [
    participantIds,
    setParticipantIds,
  ] =
    useState<string[]>(
      [],
    );


  const [
    saving,
    setSaving,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  function toggleParticipant(
    employeeId: string,
  ) {
    setParticipantIds(
      (
        current,
      ) =>
        current.includes(
          employeeId,
        )
          ? current.filter(
              (
                id,
              ) =>
                id !==
                employeeId,
            )
          : [
              ...current,
              employeeId,
            ],
    );
  }


  async function create() {
    if (
      !workspaceId ||
      !title.trim() ||
      !scheduledStart ||
      saving
    ) {
      return;
    }


    const start =
      new Date(
        scheduledStart,
      );


    const end =
      scheduledEnd
        ? new Date(
            scheduledEnd,
          )
        : null;


    if (
      Number.isNaN(
        start.getTime(),
      )
    ) {
      setError(
        "Start time is invalid.",
      );

      return;
    }


    if (
      end &&
      (
        Number.isNaN(
          end.getTime(),
        ) ||
        end <=
          start
      )
    ) {
      setError(
        "End time must be after the start time.",
      );

      return;
    }


    try {
      setSaving(
        true,
      );

      setError(
        null,
      );


      const response =
        await meetingsService.create(
          workspaceId,
          {
            title:
              title.trim(),

            description:
              description.trim() ||
              null,

            meeting_type:
              meetingType,

            scheduled_start_at:
              start.toISOString(),

            scheduled_end_at:
              end
                ? end.toISOString()
                : null,

            location:
              location.trim() ||
              null,

            participant_employee_ids:
              participantIds,
          },
        );


      await onCreated(
        response.meeting,
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to create meeting.",
      );

    } finally {
      setSaving(
        false,
      );
    }
  }


  return (
    <div
      style={{
        position:
          "fixed",

        inset:
          0,

        zIndex:
          100,

        display:
          "grid",

        placeItems:
          "center",

        padding:
          20,

        background:
          "rgba(31,30,28,.38)",
      }}
    >
      <section
        className="panel"
        style={{
          width:
            "100%",

          maxWidth:
            640,

          maxHeight:
            "90vh",

          overflowY:
            "auto",
        }}
      >
        <div
          style={{
            display:
              "flex",

            justifyContent:
              "space-between",

            alignItems:
              "center",

            padding:
              "12px 14px",

            borderBottom:
              "1px solid var(--color-border)",
          }}
        >
          <div>
            <strong>
              Schedule Meeting
            </strong>

            <div
              className="text-label"
              style={{
                marginTop:
                  3,
              }}
            >
              Invite workspace employees.
            </div>
          </div>


          <button
            type="button"
            className="button button--outline"
            onClick={
              onClose
            }
          >
            <X
              size={
                13
              }
            />
          </button>
        </div>


        <div
          style={{
            display:
              "grid",

            gap:
              12,

            padding:
              14,
          }}
        >
          {error ? (
            <div
              style={errorStyle}
            >
              {error}
            </div>
          ) : null}


          <label
            style={labelStyle}
          >
            Title

            <input
              value={
                title
              }
              maxLength={
                200
              }
              onChange={(
                event,
              ) =>
                setTitle(
                  event.target.value,
                )
              }
              style={inputStyle}
            />
          </label>


          <label
            style={labelStyle}
          >
            Description

            <textarea
              value={
                description
              }
              rows={
                4
              }
              maxLength={
                5000
              }
              onChange={(
                event,
              ) =>
                setDescription(
                  event.target.value,
                )
              }
              style={{
                ...inputStyle,

                height:
                  "auto",

                padding:
                  10,
              }}
            />
          </label>


          <div
            style={{
              display:
                "grid",

              gridTemplateColumns:
                "1fr 1fr",

              gap:
                10,
            }}
          >
            <label
              style={labelStyle}
            >
              Meeting Type

              <select
                value={
                  meetingType
                }
                onChange={(
                  event,
                ) =>
                  setMeetingType(
                    event.target.value as
                      MeetingType,
                  )
                }
                style={inputStyle}
              >
                <option value="video">
                  Video
                </option>

                <option value="voice">
                  Voice
                </option>

                <option value="in_person">
                  In Person
                </option>
              </select>
            </label>


            <label
              style={labelStyle}
            >
              Location

              <input
                value={
                  location
                }
                maxLength={
                  500
                }
                placeholder="Room or address"
                onChange={(
                  event,
                ) =>
                  setLocation(
                    event.target.value,
                  )
                }
                style={inputStyle}
              />
            </label>
          </div>


          <div
            style={{
              display:
                "grid",

              gridTemplateColumns:
                "1fr 1fr",

              gap:
                10,
            }}
          >
            <label
              style={labelStyle}
            >
              Start

              <input
                type="datetime-local"
                value={
                  scheduledStart
                }
                onChange={(
                  event,
                ) =>
                  setScheduledStart(
                    event.target.value,
                  )
                }
                style={inputStyle}
              />
            </label>


            <label
              style={labelStyle}
            >
              End

              <input
                type="datetime-local"
                value={
                  scheduledEnd
                }
                onChange={(
                  event,
                ) =>
                  setScheduledEnd(
                    event.target.value,
                  )
                }
                style={inputStyle}
              />
            </label>
          </div>


          <div
            style={{
              display:
                "grid",

              gap:
                8,
            }}
          >
            <strong
              style={{
                fontSize:
                  9,
              }}
            >
              Participants
            </strong>


            <div
              style={{
                display:
                  "grid",

                gridTemplateColumns:
                  "repeat(2, minmax(0, 1fr))",

                gap:
                  7,

                maxHeight:
                  240,

                overflowY:
                  "auto",
              }}
            >
              {employees.map(
                (
                  employee,
                ) => {
                  const selected =
                    participantIds.includes(
                      employee.id,
                    );


                  return (
                    <button
                      key={
                        employee.id
                      }
                      type="button"
                      onClick={() =>
                        toggleParticipant(
                          employee.id,
                        )
                      }
                      style={{
                        display:
                          "grid",

                        gridTemplateColumns:
                          "24px minmax(0,1fr)",

                        alignItems:
                          "center",

                        gap:
                          8,

                        padding:
                          9,

                        border:
                          selected
                            ? "1px solid #b78b14"
                            : "1px solid var(--color-border)",

                        borderRadius:
                          7,

                        background:
                          selected
                            ? "#fff8e4"
                            : "#fffefa",

                        textAlign:
                          "left",

                        cursor:
                          "pointer",
                      }}
                    >
                      <div
                        style={{
                          display:
                            "grid",

                          width:
                            24,

                          height:
                            24,

                          placeItems:
                            "center",

                          borderRadius:
                            6,

                          background:
                            selected
                              ? "#2c2d2f"
                              : "#efebe2",

                          color:
                            selected
                              ? "#fff"
                              : "#666",
                        }}
                      >
                        {selected ? (
                          <Check
                            size={
                              12
                            }
                          />
                        ) : (
                          <UserPlus
                            size={
                              11
                            }
                          />
                        )}
                      </div>


                      <div>
                        <strong
                          style={{
                            display:
                              "block",

                            fontSize:
                              9,
                          }}
                        >
                          {employee.full_name}
                        </strong>

                        <span
                          className="text-label"
                          style={{
                            fontSize:
                              7,
                          }}
                        >
                          {employee.employee_code}
                        </span>
                      </div>
                    </button>
                  );
                },
              )}
            </div>
          </div>
        </div>


        <div
          style={{
            display:
              "flex",

            justifyContent:
              "flex-end",

            gap:
              8,

            padding:
              "12px 14px",

            borderTop:
              "1px solid var(--color-border)",
          }}
        >
          <button
            type="button"
            className="button button--outline"
            disabled={
              saving
            }
            onClick={
              onClose
            }
          >
            Cancel
          </button>


          <button
            type="button"
            className="button button--primary"
            disabled={
              saving ||
              !title.trim() ||
              !scheduledStart
            }
            onClick={() => {
              void create();
            }}
          >
            <CalendarClock
              size={
                13
              }
            />

            {saving
              ? "Scheduling..."
              : "Schedule Meeting"}
          </button>
        </div>
      </section>
    </div>
  );
}


function Detail({
  label,
  value,
}: {
  label:
    string;

  value:
    string;
}) {
  return (
    <div
      style={{
        padding:
          10,

        border:
          "1px solid #ece8df",

        borderRadius:
          7,

        background:
          "#fffefa",
      }}
    >
      <div
        className="text-label"
        style={{
          fontSize:
            7,
        }}
      >
        {label}
      </div>

      <div
        style={{
          marginTop:
            4,

          fontSize:
            9,

          lineHeight:
            1.55,

          whiteSpace:
            label ===
            "Description"
              ? "pre-wrap"
              : undefined,
        }}
      >
        {value}
      </div>
    </div>
  );
}


function StatusPill({
  status,
}: {
  status:
    MeetingStatus;
}) {
  const active =
    status ===
    "active";

  const completed =
    status ===
    "completed";


  return (
    <span
      style={{
        display:
          "inline-flex",

        alignItems:
          "center",

        gap:
          4,

        padding:
          "3px 7px",

        borderRadius:
          999,

        background:
          active
            ? "#edf8e9"
            : completed
              ? "#eceff4"
              : "#f3efe5",

        color:
          active
            ? "#34732a"
            : "#686a6c",

        fontSize:
          7,

        textTransform:
          "capitalize",
      }}
    >
      {status ===
      "active" ? (
        <Video
          size={
            9
          }
        />
      ) : status ===
        "completed" ? (
        <CheckCircle2
          size={
            9
          }
        />
      ) : (
        <Clock3
          size={
            9
          }
        />
      )}

      {pretty(
        status,
      )}
    </span>
  );
}


const labelStyle = {
  display:
    "grid",

  gap:
    5,

  fontSize:
    9,
} as const;


const inputStyle = {
  width:
    "100%",

  height:
    36,

  padding:
    "0 10px",

  border:
    "1px solid var(--color-border)",

  borderRadius:
    7,

  outline:
    "none",

  background:
    "#fffefa",

  color:
    "#303235",

  fontSize:
    10,
} as const;


const errorStyle = {
  padding:
    "10px 12px",

  border:
    "1px solid #efc6c6",

  borderRadius:
    7,

  background:
    "#fff0f0",

  color:
    "#b52b2b",

  fontSize:
    10,
} as const;


const successStyle = {
  display:
    "flex",

  alignItems:
    "center",

  gap:
    6,

  padding:
    "10px 12px",

  border:
    "1px solid #cce5c4",

  borderRadius:
    7,

  background:
    "#f0faed",

  color:
    "#34732a",

  fontSize:
    10,
} as const;