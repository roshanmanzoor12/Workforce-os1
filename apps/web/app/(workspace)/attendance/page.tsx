"use client";

import {
  CalendarCheck2,
  CheckCircle2,
  Clock3,
  Coffee,
  LogIn,
  LogOut,
  RefreshCcw,
  Search,
  TimerReset,
  UserRound,
  X,
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
  attendanceService,
} from "@/services/attendance.service";

import {
  employeesService,
  type Employee,
} from "@/services/employees.service";

import type {
  AttendanceEventPublic,
  AttendanceEventType,
  AttendanceRecordPublic,
  AttendanceStatus,
  AttendanceSummaryResponse,
} from "@/types/attendance";


type RangeKey =
  | "7d"
  | "30d"
  | "90d";


function toDateInput(
  value:
    Date,
): string {
  return value
    .toISOString()
    .slice(
      0,
      10,
    );
}


function buildRange(
  range:
    RangeKey,
) {
  const end =
    new Date();

  const start =
    new Date(end);


  if (
    range ===
    "7d"
  ) {
    start.setDate(
      start.getDate() -
        7,
    );
  } else if (
    range ===
    "30d"
  ) {
    start.setDate(
      start.getDate() -
        30,
    );
  } else {
    start.setDate(
      start.getDate() -
        90,
    );
  }


  return {
    startDate:
      toDateInput(
        start,
      ),

    endDate:
      toDateInput(
        end,
      ),
  };
}


function formatDateTime(
  value:
    string | null,
): string {
  if (
    !value
  ) {
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


function formatMinutes(
  minutes:
    number,
): string {
  const safe =
    Math.max(
      0,
      minutes,
    );

  const hours =
    Math.floor(
      safe /
        60,
    );

  const remaining =
    safe %
    60;


  return `${hours}h ${remaining}m`;
}


function pretty(
  value:
    string,
): string {
  return value
    .replace(
      /_/g,
      " ",
    )
    .split(" ")
    .filter(Boolean)
    .map(
      (part) =>
        part
          .charAt(0)
          .toUpperCase() +
        part.slice(1),
    )
    .join(" ");
}


export default function AttendancePage() {
  return (
    <WorkspaceRequired>
      <AttendanceContent />
    </WorkspaceRequired>
  );
}


function AttendanceContent() {
  const {
    workspaceId,

    workspace,
  } =
    useWorkspace();


  const [
    employees,
    setEmployees,
  ] =
    useState<Employee[]>(
      [],
    );


  const [
    records,
    setRecords,
  ] =
    useState<AttendanceRecordPublic[]>(
      [],
    );


  const [
    selectedRecord,
    setSelectedRecord,
  ] =
    useState<AttendanceRecordPublic | null>(
      null,
    );


  const [
    selectedEmployeeId,
    setSelectedEmployeeId,
  ] =
    useState(
      "",
    );


  const [
    selectedStatus,
    setSelectedStatus,
  ] =
    useState<
      AttendanceStatus |
      ""
    >(
      "",
    );


  const [
    search,
    setSearch,
  ] =
    useState(
      "",
    );


  const [
    range,
    setRange,
  ] =
    useState<RangeKey>(
      "30d",
    );


  const [
    detailEvents,
    setDetailEvents,
  ] =
    useState<AttendanceEventPublic[]>(
      [],
    );


  const [
    summary,
    setSummary,
  ] =
    useState<AttendanceSummaryResponse | null>(
      null,
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


  const dateRange =
    useMemo(
      () =>
        buildRange(
          range,
        ),
      [
        range,
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
            employeeResponse,
            attendanceResponse,
          ] =
            await Promise.all([
              employeesService.list(
                workspaceId,
                {
                  includeInactive:
                    true,
                },
              ),

              attendanceService.list(
                workspaceId,
                {
                  employeeId:
                    selectedEmployeeId ||
                    null,

                  startDate:
                    dateRange.startDate,

                  endDate:
                    dateRange.endDate,

                  status:
                    selectedStatus ||
                    null,
                },
              ),
            ]);


          setEmployees(
            employeeResponse.employees,
          );


          setRecords(
            attendanceResponse.attendance ??
              [],
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load attendance records.",
          );

        } finally {
          setLoading(
            false,
          );
        }
      },
      [
        workspaceId,
        selectedEmployeeId,
        selectedStatus,
        dateRange.startDate,
        dateRange.endDate,
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


  const visibleRecords =
    useMemo(
      () => {
        const query =
          search
            .trim()
            .toLowerCase();


        if (
          !query
        ) {
          return records;
        }


        return records.filter(
          (
            record,
          ) => {
            const employee =
              employeeMap.get(
                record.employee_id,
              );


            const text =
              [
                employee?.full_name ??
                  "",
                employee?.employee_code ??
                  "",
                employee?.work_email ??
                  "",
                record.attendance_date,
                record.status,
                record.source,
              ]
                .join(" ")
                .toLowerCase();


            return text.includes(
              query,
            );
          },
        );
      },
      [
        records,
        search,
        employeeMap,
      ],
    );


  const presentCount =
    records.filter(
      (
        record,
      ) =>
        record.status ===
        "present",
    ).length;


  const lateCount =
    records.filter(
      (
        record,
      ) =>
        record.status ===
        "late",
    ).length;


  const absentCount =
    records.filter(
      (
        record,
      ) =>
        record.status ===
        "absent",
    ).length;


  const totalWorkedMinutes =
    records.reduce(
      (
        total,
        record,
      ) =>
        total +
        record.worked_minutes,
      0,
    );


  async function openRecord(
    record:
      AttendanceRecordPublic,
  ) {
    if (
      !workspaceId
    ) {
      return;
    }


    setSelectedRecord(
      record,
    );


    setDetailEvents(
      [],
    );


    setSummary(
      null,
    );


    try {
      setDetailLoading(
        true,
      );


      setError(
        null,
      );


      const [
        detail,
        employeeSummary,
      ] =
        await Promise.all([
          attendanceService.get(
            workspaceId,
            record.id,
          ),

          attendanceService.summary(
            workspaceId,
            record.employee_id,
            dateRange.startDate,
            dateRange.endDate,
          ),
        ]);


      setSelectedRecord(
        detail.attendance,
      );


      setDetailEvents(
        detail.events ??
          [],
      );


      setSummary(
        employeeSummary,
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to load attendance detail.",
      );

    } finally {
      setDetailLoading(
        false,
      );
    }
  }


  async function recordEvent(
    eventType:
      AttendanceEventType,
  ) {
    if (
      !workspaceId ||
      !selectedRecord ||
      action
    ) {
      return;
    }


    try {
      setAction(
        eventType,
      );


      setError(
        null,
      );


      setSuccess(
        null,
      );


      const response =
        await attendanceService.recordEvent(
          workspaceId,
          selectedRecord.employee_id,
          {
            event_type:
              eventType,

            occurred_at:
              new Date().toISOString(),

            source:
              "web",
          },
        );


      setSuccess(
        response.message,
      );


      const refreshed =
        await attendanceService.get(
          workspaceId,
          selectedRecord.id,
        );


      setSelectedRecord(
        refreshed.attendance,
      );


      setDetailEvents(
        refreshed.events ??
          [],
      );


      await load();

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to record attendance event.",
      );

    } finally {
      setAction(
        null,
      );
    }
  }


  async function changeStatus(
    value:
      AttendanceStatus,
  ) {
    if (
      !workspaceId ||
      !selectedRecord ||
      action
    ) {
      return;
    }


    try {
      setAction(
        "status",
      );


      setError(
        null,
      );


      const response =
        await attendanceService.update(
          workspaceId,
          selectedRecord.id,
          {
            status:
              value,
          },
        );


      setSelectedRecord(
        response.attendance,
      );


      setRecords(
        (
          current,
        ) =>
          current.map(
            (
              record,
            ) =>
              record.id ===
              response.attendance.id
                ? response.attendance
                : record,
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
          : "Unable to update attendance status.",
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
      <div
        style={{
          display:
            "flex",

          alignItems:
            "flex-start",

          justifyContent:
            "space-between",

          gap:
            16,
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
            <CalendarCheck2
              size={
                13
              }
            />

            Workforce Attendance
          </div>


          <h1
            style={{
              marginTop:
                5,
            }}
          >
            Attendance
          </h1>


          <p
            className="text-label"
            style={{
              marginTop:
                4,
            }}
          >
            Attendance records and employee time activity for{" "}
            {workspace?.name ??
              "this workspace"}.
          </p>
        </div>


        <button
          type="button"
          className="button button--outline"
          disabled={
            loading
          }
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
      </div>


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
            "grid",

          gridTemplateColumns:
            "repeat(4, minmax(0, 1fr))",

          gap:
            10,
        }}
      >
        <Metric
          label="Present"
          value={
            String(
              presentCount,
            )
          }
        />


        <Metric
          label="Late"
          value={
            String(
              lateCount,
            )
          }
        />


        <Metric
          label="Absent"
          value={
            String(
              absentCount,
            )
          }
        />


        <Metric
          label="Worked Time"
          value={
            formatMinutes(
              totalWorkedMinutes,
            )
          }
        />
      </div>


      <section
        className="panel"
      >
        <div
          style={{
            display:
              "grid",

            gridTemplateColumns:
              "minmax(240px, 1fr) 200px 170px 145px",

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
              placeholder="Search employee, code or status"
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
              selectedEmployeeId
            }
            onChange={(
              event,
            ) =>
              setSelectedEmployeeId(
                event.target.value,
              )
            }
            style={inputStyle}
          >
            <option value="">
              All employees
            </option>


            {employees.map(
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


          <select
            value={
              selectedStatus
            }
            onChange={(
              event,
            ) =>
              setSelectedStatus(
                event.target.value as
                  | AttendanceStatus
                  | "",
              )
            }
            style={inputStyle}
          >
            <option value="">
              All statuses
            </option>

            <option value="present">
              Present
            </option>

            <option value="late">
              Late
            </option>

            <option value="absent">
              Absent
            </option>

            <option value="half_day">
              Half Day
            </option>

            <option value="on_leave">
              On Leave
            </option>

            <option value="holiday">
              Holiday
            </option>
          </select>


          <select
            value={
              range
            }
            onChange={(
              event,
            ) =>
              setRange(
                event.target.value as
                  RangeKey,
              )
            }
            style={inputStyle}
          >
            <option value="7d">
              Last 7 days
            </option>

            <option value="30d">
              Last 30 days
            </option>

            <option value="90d">
              Last 90 days
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
        ) : visibleRecords.length ===
          0 ? (
          <div
            style={{
              padding:
                36,

              textAlign:
                "center",

              color:
                "#7a7d80",

              fontSize:
                10,
            }}
          >
            No attendance records found.
          </div>
        ) : (
          <div
            style={{
              overflowX:
                "auto",
            }}
          >
            <table
              style={{
                width:
                  "100%",

                borderCollapse:
                  "collapse",

                fontSize:
                  9,
              }}
            >
              <thead>
                <tr>
                  <Th>
                    Employee
                  </Th>

                  <Th>
                    Date
                  </Th>

                  <Th>
                    Status
                  </Th>

                  <Th>
                    Check In
                  </Th>

                  <Th>
                    Check Out
                  </Th>

                  <Th>
                    Worked
                  </Th>

                  <Th>
                    Break
                  </Th>

                  <Th>
                    Source
                  </Th>
                </tr>
              </thead>


              <tbody>
                {visibleRecords.map(
                  (
                    record,
                  ) => {
                    const employee =
                      employeeMap.get(
                        record.employee_id,
                      );


                    const selected =
                      selectedRecord?.id ===
                      record.id;


                    return (
                      <tr
                        key={
                          record.id
                        }
                        onClick={() => {
                          void openRecord(
                            record,
                          );
                        }}
                        style={{
                          cursor:
                            "pointer",

                          background:
                            selected
                              ? "#faf5e7"
                              : undefined,
                        }}
                      >
                        <Td>
                          <strong>
                            {employee?.full_name ??
                              "Unknown employee"}
                          </strong>


                          <div
                            className="text-label"
                            style={{
                              marginTop:
                                2,

                              fontSize:
                                7,
                            }}
                          >
                            {employee?.employee_code ??
                              record.employee_id}
                          </div>
                        </Td>


                        <Td>
                          {
                            record.attendance_date
                          }
                        </Td>


                        <Td>
                          <StatusPill
                            status={
                              record.status
                            }
                          />
                        </Td>


                        <Td>
                          {formatDateTime(
                            record.check_in_at,
                          )}
                        </Td>


                        <Td>
                          {formatDateTime(
                            record.check_out_at,
                          )}
                        </Td>


                        <Td>
                          {formatMinutes(
                            record.worked_minutes,
                          )}
                        </Td>


                        <Td>
                          {formatMinutes(
                            record.break_minutes,
                          )}
                        </Td>


                        <Td>
                          {pretty(
                            record.source,
                          )}
                        </Td>
                      </tr>
                    );
                  },
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>


      {selectedRecord ? (
        <AttendanceDetail
          record={
            selectedRecord
          }
          employee={
            employeeMap.get(
              selectedRecord.employee_id,
            ) ??
            null
          }
          events={
            detailEvents
          }
          summary={
            summary
          }
          loading={
            detailLoading
          }
          action={
            action
          }
          onClose={() => {
            setSelectedRecord(
              null,
            );

            setDetailEvents(
              [],
            );

            setSummary(
              null,
            );
          }}
          onEvent={
            recordEvent
          }
          onStatus={
            changeStatus
          }
        />
      ) : null}
    </div>
  );
}


function AttendanceDetail({
  record,

  employee,

  events,

  summary,

  loading,

  action,

  onClose,

  onEvent,

  onStatus,
}: {
  record:
    AttendanceRecordPublic;

  employee:
    Employee | null;

  events:
    AttendanceEventPublic[];

  summary:
    AttendanceSummaryResponse | null;

  loading:
    boolean;

  action:
    string | null;

  onClose:
    () => void;

  onEvent:
    (
      event:
        AttendanceEventType,
    ) => Promise<void>;

  onStatus:
    (
      status:
        AttendanceStatus,
    ) => Promise<void>;
}) {
  return (
    <section
      className="panel"
    >
      <div
        style={{
          display:
            "flex",

          alignItems:
            "center",

          justifyContent:
            "space-between",

          gap:
            10,

          padding:
            "11px 14px",

          borderBottom:
            "1px solid var(--color-border)",
        }}
      >
        <div>
          <strong>
            {employee?.full_name ??
              "Attendance Detail"}
          </strong>


          <div
            className="text-label"
            style={{
              marginTop:
                2,
            }}
          >
            {employee?.employee_code ??
              record.employee_id}
            {" · "}
            {record.attendance_date}
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

          Close
        </button>
      </div>


      {loading ? (
        <div
          className="skeleton"
          style={{
            height:
              300,

            margin:
              14,
          }}
        />
      ) : (
        <div
          className="panel-body"
          style={{
            display:
              "grid",

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

              gridTemplateColumns:
                "repeat(4, minmax(0, 1fr))",

              gap:
                8,
            }}
          >
            <Detail
              label="Status"
              value={
                pretty(
                  record.status,
                )
              }
            />


            <Detail
              label="Worked Time"
              value={
                formatMinutes(
                  record.worked_minutes,
                )
              }
            />


            <Detail
              label="Break Time"
              value={
                formatMinutes(
                  record.break_minutes,
                )
              }
            />


            <Detail
              label="Source"
              value={
                pretty(
                  record.source,
                )
              }
            />
          </div>


          <div
            style={{
              display:
                "grid",

              gridTemplateColumns:
                "minmax(0, 1fr) minmax(0, 1fr)",

              gap:
                12,
            }}
          >
            <div
              style={{
                display:
                  "grid",

                gap:
                  9,

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
                Record Attendance Event
              </strong>


              <div
                style={{
                  display:
                    "grid",

                  gridTemplateColumns:
                    "1fr 1fr",

                  gap:
                    7,
                }}
              >
                <ActionButton
                  icon={
                    <LogIn
                      size={
                        13
                      }
                    />
                  }
                  label="Check In"
                  loading={
                    action ===
                    "check_in"
                  }
                  onClick={() => {
                    void onEvent(
                      "check_in",
                    );
                  }}
                />


                <ActionButton
                  icon={
                    <LogOut
                      size={
                        13
                      }
                    />
                  }
                  label="Check Out"
                  loading={
                    action ===
                    "check_out"
                  }
                  onClick={() => {
                    void onEvent(
                      "check_out",
                    );
                  }}
                />


                <ActionButton
                  icon={
                    <Coffee
                      size={
                        13
                      }
                    />
                  }
                  label="Break Start"
                  loading={
                    action ===
                    "break_start"
                  }
                  onClick={() => {
                    void onEvent(
                      "break_start",
                    );
                  }}
                />


                <ActionButton
                  icon={
                    <TimerReset
                      size={
                        13
                      }
                    />
                  }
                  label="Break End"
                  loading={
                    action ===
                    "break_end"
                  }
                  onClick={() => {
                    void onEvent(
                      "break_end",
                    );
                  }}
                />
              </div>


              <label
                style={{
                  display:
                    "grid",

                  gap:
                    5,

                  marginTop:
                    4,

                  fontSize:
                    8,
                }}
              >
                Attendance Status

                <select
                  value={
                    record.status
                  }
                  disabled={
                    action !==
                    null
                  }
                  onChange={(
                    event,
                  ) => {
                    void onStatus(
                      event.target.value as
                        AttendanceStatus,
                    );
                  }}
                  style={inputStyle}
                >
                  <option value="present">
                    Present
                  </option>

                  <option value="late">
                    Late
                  </option>

                  <option value="absent">
                    Absent
                  </option>

                  <option value="half_day">
                    Half Day
                  </option>

                  <option value="on_leave">
                    On Leave
                  </option>

                  <option value="holiday">
                    Holiday
                  </option>
                </select>
              </label>
            </div>


            <div
              style={{
                display:
                  "grid",

                alignContent:
                  "start",

                gap:
                  8,

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
                Employee Summary
              </strong>


              {summary ? (
                <div
                  style={{
                    display:
                      "grid",

                    gridTemplateColumns:
                      "1fr 1fr",

                    gap:
                      7,
                  }}
                >
                  <Detail
                    label="Present"
                    value={
                      String(
                        summary.present_days,
                      )
                    }
                  />

                  <Detail
                    label="Absent"
                    value={
                      String(
                        summary.absent_days,
                      )
                    }
                  />

                  <Detail
                    label="Late"
                    value={
                      String(
                        summary.late_days,
                      )
                    }
                  />

                  <Detail
                    label="Half Days"
                    value={
                      String(
                        summary.half_days,
                      )
                    }
                  />

                  <Detail
                    label="Leave"
                    value={
                      String(
                        summary.leave_days,
                      )
                    }
                  />

                  <Detail
                    label="Holidays"
                    value={
                      String(
                        summary.holiday_days,
                      )
                    }
                  />

                  <Detail
                    label="Worked"
                    value={
                      formatMinutes(
                        summary.worked_minutes,
                      )
                    }
                  />

                  <Detail
                    label="Break"
                    value={
                      formatMinutes(
                        summary.break_minutes,
                      )
                    }
                  />
                </div>
              ) : (
                <div
                  className="text-label"
                >
                  No summary data available.
                </div>
              )}
            </div>
          </div>


          <section
            style={{
              border:
                "1px solid var(--color-border)",

              borderRadius:
                8,

              overflow:
                "hidden",
            }}
          >
            <div
              style={{
                padding:
                  "9px 11px",

                borderBottom:
                  "1px solid var(--color-border)",

                background:
                  "#f7f4ee",
              }}
            >
              <strong>
                Event Timeline
              </strong>
            </div>


            {events.length ===
            0 ? (
              <div
                style={{
                  padding:
                    22,

                  textAlign:
                    "center",

                  color:
                    "#7c7e80",

                  fontSize:
                    9,
                }}
              >
                No attendance events recorded.
              </div>
            ) : (
              <div>
                {events
                  .slice()
                  .sort(
                    (
                      left,
                      right,
                    ) =>
                      new Date(
                        right.occurred_at,
                      ).getTime() -
                      new Date(
                        left.occurred_at,
                      ).getTime(),
                  )
                  .map(
                    (
                      event,
                    ) => (
                      <div
                        key={
                          event.id
                        }
                        style={{
                          display:
                            "grid",

                          gridTemplateColumns:
                            "32px minmax(0, 1fr) auto",

                          gap:
                            9,

                          alignItems:
                            "center",

                          padding:
                            "10px 11px",

                          borderBottom:
                            "1px solid #eeeae2",
                        }}
                      >
                        <div
                          style={{
                            display:
                              "grid",

                            width:
                              30,

                            height:
                              30,

                            placeItems:
                              "center",

                            borderRadius:
                              7,

                            background:
                              "#f3efe5",

                            color:
                              "#765c0c",
                          }}
                        >
                          <Clock3
                            size={
                              13
                            }
                          />
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
                            {pretty(
                              event.event_type,
                            )}
                          </strong>


                          <div
                            className="text-label"
                            style={{
                              marginTop:
                                2,

                              fontSize:
                                7,
                            }}
                          >
                            Source:{" "}
                            {pretty(
                              event.source,
                            )}
                          </div>
                        </div>


                        <div
                          className="text-label"
                          style={{
                            fontSize:
                              8,
                          }}
                        >
                          {formatDateTime(
                            event.occurred_at,
                          )}
                        </div>
                      </div>
                    ),
                  )}
              </div>
            )}
          </section>
        </div>
      )}
    </section>
  );
}


function ActionButton({
  icon,

  label,

  loading,

  onClick,
}: {
  icon:
    React.ReactNode;

  label:
    string;

  loading:
    boolean;

  onClick:
    () => void;
}) {
  return (
    <button
      type="button"
      className="button button--outline"
      disabled={
        loading
      }
      onClick={
        onClick
      }
    >
      {icon}

      {loading
        ? "Saving..."
        : label}
    </button>
  );
}


function Metric({
  label,

  value,
}: {
  label:
    string;

  value:
    string;
}) {
  return (
    <section
      className="panel"
      style={{
        padding:
          13,
      }}
    >
      <div
        className="text-label"
        style={{
          fontSize:
            8,
        }}
      >
        {label}
      </div>


      <strong
        style={{
          display:
            "block",

          marginTop:
            5,

          fontSize:
            20,
        }}
      >
        {value}
      </strong>
    </section>
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
        minWidth:
          0,

        padding:
          9,

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


      <strong
        style={{
          display:
            "block",

          marginTop:
            3,

          overflow:
            "hidden",

          textOverflow:
            "ellipsis",

          whiteSpace:
            "nowrap",

          fontSize:
            9,
        }}
      >
        {value}
      </strong>
    </div>
  );
}


function StatusPill({
  status,
}: {
  status:
    AttendanceStatus;
}) {
  const positive =
    status ===
      "present" ||
    status ===
      "holiday";


  const warning =
    status ===
      "late" ||
    status ===
      "half_day";


  return (
    <span
      style={{
        display:
          "inline-block",

        padding:
          "3px 7px",

        borderRadius:
          999,

        background:
          positive
            ? "#edf8e9"
            : warning
              ? "#fff5dc"
              : "#f1eeee",

        color:
          positive
            ? "#34732a"
            : warning
              ? "#8b6500"
              : "#6b6363",

        fontSize:
          8,

        textTransform:
          "capitalize",
      }}
    >
      {pretty(
        status,
      )}
    </span>
  );
}


function Th({
  children,
}: {
  children:
    React.ReactNode;
}) {
  return (
    <th
      style={{
        padding:
          "9px 11px",

        borderBottom:
          "1px solid var(--color-border)",

        background:
          "#f7f4ee",

        color:
          "#6c6e70",

        fontSize:
          8,

        textAlign:
          "left",

        whiteSpace:
          "nowrap",
      }}
    >
      {children}
    </th>
  );
}


function Td({
  children,
}: {
  children:
    React.ReactNode;
}) {
  return (
    <td
      style={{
        padding:
          "10px 11px",

        borderBottom:
          "1px solid #efebe3",

        verticalAlign:
          "middle",
      }}
    >
      {children}
    </td>
  );
}


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