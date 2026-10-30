"use client";

import {
  Activity,
  AppWindow,
  Clock3,
  Globe2,
  RefreshCcw,
  Target,
  TimerReset,
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
  workforceAnalyticsService,
} from "@/services/workforce-analytics.service";

import type {
  AnalyticsProductivityResponse,
} from "@/types/workforce-analytics";


type RangeKey =
  | "7d"
  | "30d"
  | "90d";


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
    startAt:
      start.toISOString(),

    endAt:
      end.toISOString(),
  };
}


function formatSeconds(
  seconds:
    number,
) {
  const safe =
    Math.max(
      0,
      seconds,
    );

  const hours =
    Math.floor(
      safe /
        3600,
    );

  const minutes =
    Math.floor(
      (
        safe %
        3600
      ) /
        60,
    );


  return `${hours}h ${minutes}m`;
}


function formatMinutes(
  minutes:
    number,
) {
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


function ratio(
  value:
    number,

  total:
    number,
) {
  if (
    total <=
    0
  ) {
    return 0;
  }


  return Math.max(
    0,

    Math.min(
      100,

      (
        value /
        total
      ) *
        100,
    ),
  );
}


export default function ProductivityPage() {
  return (
    <WorkspaceRequired>
      <ProductivityContent />
    </WorkspaceRequired>
  );
}


function ProductivityContent() {
  const {
    workspaceId,

    workspace,
  } =
    useWorkspace();


  const [
    range,
    setRange,
  ] =
    useState<RangeKey>(
      "30d",
    );


  const [
    data,
    setData,
  ] =
    useState<AnalyticsProductivityResponse | null>(
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
    error,
    setError,
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


          const response =
            await workforceAnalyticsService.productivity(
              workspaceId,
              buildRange(
                range,
              ),
            );


          setData(
            response,
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load productivity analytics.",
          );

        } finally {
          setLoading(
            false,
          );
        }
      },
      [
        workspaceId,
        range,
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


  const activeShare =
    useMemo(
      () =>
        ratio(
          data?.active_events ??
            0,

          data?.activity_events ??
            0,
        ),
      [
        data,
      ],
    );


  const idleShare =
    useMemo(
      () =>
        ratio(
          data?.idle_events ??
            0,

          data?.activity_events ??
            0,
        ),
      [
        data,
      ],
    );


  const goalCompletion =
    useMemo(
      () =>
        ratio(
          data?.goals_completed ??
            0,

          data?.goals_total ??
            0,
        ),
      [
        data,
      ],
    );


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
            <Activity
              size={
                13
              }
            />

            Workforce Intelligence
          </div>


          <h1
            style={{
              marginTop:
                5,
            }}
          >
            Productivity
          </h1>


          <p
            className="text-label"
            style={{
              marginTop:
                4,
            }}
          >
            Activity and work-pattern analytics for{" "}
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
            style={{
              ...inputStyle,

              width:
                135,
            }}
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
      </div>


      {error ? (
        <div
          style={errorStyle}
        >
          {error}
        </div>
      ) : null}


      {loading ? (
        <>
          <div
            className="skeleton"
            style={{
              height:
                110,
            }}
          />

          <div
            className="skeleton"
            style={{
              height:
                340,
            }}
          />
        </>
      ) : (
        <>
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
              icon={
                <Clock3
                  size={
                    15
                  }
                />
              }
              label="Worked Time"
              value={
                formatMinutes(
                  data?.worked_minutes ??
                    0,
                )
              }
            />


            <Metric
              icon={
                <AppWindow
                  size={
                    15
                  }
                />
              }
              label="Application Time"
              value={
                formatSeconds(
                  data?.app_seconds ??
                    0,
                )
              }
            />


            <Metric
              icon={
                <Globe2
                  size={
                    15
                  }
                />
              }
              label="Website Time"
              value={
                formatSeconds(
                  data?.website_seconds ??
                    0,
                )
              }
            />


            <Metric
              icon={
                <Target
                  size={
                    15
                  }
                />
              }
              label="Goal Progress"
              value={`${Math.round(
                data?.goals_average_progress ??
                  0,
              )}%`}
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
            <section
              className="panel"
            >
              <PanelHeader
                title="Activity Distribution"
                description="Recorded active and idle state observations."
              />


              <div
                className="panel-body"
                style={{
                  display:
                    "grid",

                  gap:
                    16,

                  padding:
                    14,
                }}
              >
                <Progress
                  label="Active observations"
                  count={
                    data?.active_events ??
                    0
                  }
                  percentage={
                    activeShare
                  }
                />


                <Progress
                  label="Idle observations"
                  count={
                    data?.idle_events ??
                    0
                  }
                  percentage={
                    idleShare
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
                  <SmallMetric
                    label="Total Activity Events"
                    value={
                      String(
                        data?.activity_events ??
                          0,
                      )
                    }
                  />


                  <SmallMetric
                    label="Backend Scope"
                    value={
                      data?.scope ??
                      "—"
                    }
                  />
                </div>
              </div>
            </section>


            <section
              className="panel"
            >
              <PanelHeader
                title="Goal Completion"
                description="Goal outcomes in the same analytics window."
              />


              <div
                className="panel-body"
                style={{
                  display:
                    "grid",

                  gap:
                    16,

                  padding:
                    14,
                }}
              >
                <Progress
                  label="Completed goals"
                  count={
                    data?.goals_completed ??
                    0
                  }
                  percentage={
                    goalCompletion
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
                  <SmallMetric
                    label="Total Goals"
                    value={
                      String(
                        data?.goals_total ??
                          0,
                      )
                    }
                  />


                  <SmallMetric
                    label="Average Progress"
                    value={`${Math.round(
                      data?.goals_average_progress ??
                        0,
                    )}%`}
                  />
                </div>
              </div>
            </section>
          </div>


          <section
            className="panel"
          >
            <PanelHeader
              title="Work Signals"
              description="Raw aggregate signals from the backend, without assigning a productivity score."
            />


            <div
              className="panel-body"
              style={{
                display:
                  "grid",

                gridTemplateColumns:
                  "repeat(3, minmax(0, 1fr))",

                gap:
                  10,

                padding:
                  14,
              }}
            >
              <SignalCard
                icon={
                  <TimerReset
                    size={
                      16
                    }
                  />
                }
                title="Activity Events"
                value={
                  String(
                    data?.activity_events ??
                      0,
                  )
                }
                text="Active and idle endpoint observations recorded during the selected window."
              />


              <SignalCard
                icon={
                  <AppWindow
                    size={
                      16
                    }
                  />
                }
                title="Application Usage"
                value={
                  formatSeconds(
                    data?.app_seconds ??
                      0,
                  )
                }
                text="Total duration represented by application-use intervals."
              />


              <SignalCard
                icon={
                  <Globe2
                    size={
                      16
                    }
                  />
                }
                title="Website Usage"
                value={
                  formatSeconds(
                    data?.website_seconds ??
                      0,
                  )
                }
                text="Total duration represented by retained website/domain intervals."
              />
            </div>
          </section>


          <div
            style={{
              padding:
                11,

              border:
                "1px solid #e6dcc0",

              borderRadius:
                8,

              background:
                "#fff9e8",

              color:
                "#745e19",

              fontSize:
                9,

              lineHeight:
                1.6,
            }}
          >
            WorkforceOS shows observable work signals separately. Active/idle time, application duration, website duration, and goal progress are not automatically converted into a judgment about an employee&apos;s performance.
          </div>
        </>
      )}
    </div>
  );
}


function Metric({
  icon,
  label,
  value,
}: {
  icon:
    React.ReactNode;

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
        style={{
          display:
            "flex",

          alignItems:
            "center",

          justifyContent:
            "space-between",
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


        <div
          style={{
            color:
              "#997000",
          }}
        >
          {icon}
        </div>
      </div>


      <strong
        style={{
          display:
            "block",

          marginTop:
            6,

          fontSize:
            20,
        }}
      >
        {value}
      </strong>
    </section>
  );
}


function PanelHeader({
  title,
  description,
}: {
  title:
    string;

  description:
    string;
}) {
  return (
    <div
      style={{
        padding:
          "11px 14px",

        borderBottom:
          "1px solid var(--color-border)",
      }}
    >
      <strong>
        {title}
      </strong>


      <p
        className="text-label"
        style={{
          marginTop:
            3,
        }}
      >
        {description}
      </p>
    </div>
  );
}


function Progress({
  label,
  count,
  percentage,
}: {
  label:
    string;

  count:
    number;

  percentage:
    number;
}) {
  return (
    <div
      style={{
        display:
          "grid",

        gap:
          6,
      }}
    >
      <div
        style={{
          display:
            "flex",

          justifyContent:
            "space-between",

          gap:
            10,

          fontSize:
            9,
        }}
      >
        <span>
          {label}
        </span>

        <strong>
          {count}
        </strong>
      </div>


      <div
        style={{
          height:
            6,

          overflow:
            "hidden",

          borderRadius:
            999,

          background:
            "#ece9e1",
        }}
      >
        <div
          style={{
            width:
              `${percentage}%`,

            height:
              "100%",

            background:
              "#b99123",
          }}
        />
      </div>
    </div>
  );
}


function SmallMetric({
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
          "#faf8f3",
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
            4,

          fontSize:
            11,
        }}
      >
        {value}
      </strong>
    </div>
  );
}


function SignalCard({
  icon,
  title,
  value,
  text,
}: {
  icon:
    React.ReactNode;

  title:
    string;

  value:
    string;

  text:
    string;
}) {
  return (
    <div
      style={{
        padding:
          12,

        border:
          "1px solid #ebe7de",

        borderRadius:
          8,

        background:
          "#fffefa",
      }}
    >
      <div
        style={{
          color:
            "#93700d",
        }}
      >
        {icon}
      </div>


      <strong
        style={{
          display:
            "block",

          marginTop:
            8,

          fontSize:
            10,
        }}
      >
        {title}
      </strong>


      <div
        style={{
          marginTop:
            5,

          fontSize:
            17,

          fontWeight:
            700,
        }}
      >
        {value}
      </div>


      <p
        className="text-label"
        style={{
          marginTop:
            7,

          lineHeight:
            1.55,
        }}
      >
        {text}
      </p>
    </div>
  );
}


const inputStyle = {
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