"use client";

import {
  Activity,
  AppWindow,
  BarChart3,
  Clock3,
  Globe2,
  RefreshCcw,
  Target,
  Users,
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
  AnalyticsActivityResponse,
  AnalyticsAppsResponse,
  AnalyticsGoalsResponse,
  AnalyticsOverviewResponse,
  AnalyticsTrendsResponse,
  AnalyticsWebsitesResponse,
} from "@/types/workforce-analytics";


type RangeKey =
  | "7d"
  | "30d"
  | "90d";


function formatDuration(
  seconds:
    number,
): string {
  const safeSeconds =
    Math.max(
      0,
      seconds,
    );


  const hours =
    Math.floor(
      safeSeconds /
        3600,
    );


  const minutes =
    Math.floor(
      (
        safeSeconds %
        3600
      ) /
        60,
    );


  if (
    hours >
    0
  ) {
    return `${hours}h ${minutes}m`;
  }


  return `${minutes}m`;
}


function formatWorkedMinutes(
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


function buildRange(
  range:
    RangeKey,
) {
  const end =
    new Date();


  const start =
    new Date(
      end,
    );


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


function percentage(
  value:
    number,
  total:
    number,
): number {
  if (
    total <=
    0
  ) {
    return 0;
  }


  return Math.min(
    100,
    Math.max(
      0,
      (
        value /
        total
      ) *
        100,
    ),
  );
}


export default function AnalyticsPage() {
  return (
    <WorkspaceRequired>
      <AnalyticsContent />
    </WorkspaceRequired>
  );
}


function AnalyticsContent() {
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
    overview,
    setOverview,
  ] =
    useState<AnalyticsOverviewResponse | null>(
      null,
    );


  const [
    activity,
    setActivity,
  ] =
    useState<AnalyticsActivityResponse | null>(
      null,
    );


  const [
    apps,
    setApps,
  ] =
    useState<AnalyticsAppsResponse | null>(
      null,
    );


  const [
    websites,
    setWebsites,
  ] =
    useState<AnalyticsWebsitesResponse | null>(
      null,
    );


  const [
    goals,
    setGoals,
  ] =
    useState<AnalyticsGoalsResponse | null>(
      null,
    );


  const [
    trends,
    setTrends,
  ] =
    useState<AnalyticsTrendsResponse | null>(
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


          const window =
            buildRange(
              range,
            );


          const [
            overviewResponse,
            activityResponse,
            appsResponse,
            websitesResponse,
            goalsResponse,
            trendsResponse,
          ] =
            await Promise.all([
              workforceAnalyticsService.overview(
                workspaceId,
                window,
              ),

              workforceAnalyticsService.activity(
                workspaceId,
                window,
              ),

              workforceAnalyticsService.apps(
                workspaceId,
                window,
              ),

              workforceAnalyticsService.websites(
                workspaceId,
                window,
              ),

              workforceAnalyticsService.goals(
                workspaceId,
                window,
              ),

              workforceAnalyticsService.trends(
                workspaceId,
                window,
              ),
            ]);


          setOverview(
            overviewResponse,
          );


          setActivity(
            activityResponse,
          );


          setApps(
            appsResponse,
          );


          setWebsites(
            websitesResponse,
          );


          setGoals(
            goalsResponse,
          );


          setTrends(
            trendsResponse,
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load workspace analytics.",
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


  const activePercentage =
    percentage(
      activity?.active_events ??
        0,

      activity?.total_events ??
        0,
    );


  const idlePercentage =
    percentage(
      activity?.idle_events ??
        0,

      activity?.total_events ??
        0,
    );


  const completedGoalsPercentage =
    percentage(
      goals?.completed ??
        0,

      goals?.total ??
        0,
    );


  const maxAppSeconds =
    useMemo(
      () =>
        Math.max(
          1,

          ...(
            apps?.top_apps ??
            []
          ).map(
            (
              item,
            ) =>
              item.duration_seconds,
          ),
        ),
      [
        apps,
      ],
    );


  const maxWebsiteSeconds =
    useMemo(
      () =>
        Math.max(
          1,

          ...(
            websites
              ?.top_websites ??
            []
          ).map(
            (
              item,
            ) =>
              item.duration_seconds,
          ),
        ),
      [
        websites,
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
            <BarChart3
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
            Analytics
          </h1>


          <p
            className="text-label"
            style={{
              marginTop:
                4,
            }}
          >
            Operational analytics for{" "}
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
                380,
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
                <Users
                  size={
                    15
                  }
                />
              }
              label="Employees"
              value={
                String(
                  overview?.employees ??
                    0,
                )
              }
            />


            <Metric
              icon={
                <Activity
                  size={
                    15
                  }
                />
              }
              label="Activity Events"
              value={
                String(
                  overview?.activity_events ??
                    0,
                )
              }
            />


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
                formatWorkedMinutes(
                  overview?.worked_minutes ??
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
              label="Goals Completed"
              value={`${overview?.goals_completed ?? 0} / ${overview?.goals_total ?? 0}`}
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
                title="Activity"
                description="Recorded active and idle observations."
              />


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
                <ProgressRow
                  label="Active observations"
                  value={
                    activity?.active_events ??
                    0
                  }
                  percentage={
                    activePercentage
                  }
                />


                <ProgressRow
                  label="Idle observations"
                  value={
                    activity?.idle_events ??
                    0
                  }
                  percentage={
                    idlePercentage
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
                    label="Total Events"
                    value={
                      String(
                        activity?.total_events ??
                          0,
                      )
                    }
                  />


                  <SmallMetric
                    label="Average Idle"
                    value={
                      formatDuration(
                        activity?.average_idle_seconds ??
                          0,
                      )
                    }
                  />
                </div>
              </div>
            </section>


            <section
              className="panel"
            >
              <PanelHeader
                title="Goals"
                description="Workspace goal progress in the selected period."
              />


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
                <ProgressRow
                  label="Completed"
                  value={
                    goals?.completed ??
                    0
                  }
                  percentage={
                    completedGoalsPercentage
                  }
                />


                <div
                  style={{
                    display:
                      "grid",

                    gridTemplateColumns:
                      "repeat(3, 1fr)",

                    gap:
                      8,
                  }}
                >
                  <SmallMetric
                    label="Active"
                    value={
                      String(
                        goals?.active ??
                          0,
                      )
                    }
                  />


                  <SmallMetric
                    label="Completed"
                    value={
                      String(
                        goals?.completed ??
                          0,
                      )
                    }
                  />


                  <SmallMetric
                    label="Avg Progress"
                    value={`${Math.round(
                      goals?.average_progress ??
                        0,
                    )}%`}
                  />
                </div>
              </div>
            </section>
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
                title="Top Applications"
                description="Application usage duration from recorded intervals."
              />


              <div
                className="panel-body"
                style={{
                  display:
                    "grid",

                  gap:
                    8,

                  padding:
                    14,
                }}
              >
                {(apps?.top_apps ??
                  []).length ===
                0 ? (
                  <EmptyText text="No application usage recorded for this period." />
                ) : (
                  apps?.top_apps
                    .slice(
                      0,
                      8,
                    )
                    .map(
                      (
                        item,
                      ) => (
                        <UsageRow
                          key={
                            item.name
                          }
                          icon={
                            <AppWindow
                              size={
                                13
                              }
                            />
                          }
                          name={
                            item.name
                          }
                          seconds={
                            item.duration_seconds
                          }
                          width={
                            percentage(
                              item.duration_seconds,
                              maxAppSeconds,
                            )
                          }
                        />
                      ),
                    )
                )}
              </div>
            </section>


            <section
              className="panel"
            >
              <PanelHeader
                title="Top Websites"
                description="Domain usage retained by workspace analytics."
              />


              <div
                className="panel-body"
                style={{
                  display:
                    "grid",

                  gap:
                    8,

                  padding:
                    14,
                }}
              >
                {(websites?.top_websites ??
                  []).length ===
                0 ? (
                  <EmptyText text="No website usage recorded for this period." />
                ) : (
                  websites?.top_websites
                    .slice(
                      0,
                      8,
                    )
                    .map(
                      (
                        item,
                      ) => (
                        <UsageRow
                          key={
                            item.name
                          }
                          icon={
                            <Globe2
                              size={
                                13
                              }
                            />
                          }
                          name={
                            item.name
                          }
                          seconds={
                            item.duration_seconds
                          }
                          width={
                            percentage(
                              item.duration_seconds,
                              maxWebsiteSeconds,
                            )
                          }
                        />
                      ),
                    )
                )}
              </div>
            </section>
          </div>


          <section
            className="panel"
          >
            <PanelHeader
              title="Trend Series"
              description="Daily analytics series returned by the backend."
            />


            <div
              className="panel-body"
              style={{
                display:
                  "grid",

                gridTemplateColumns:
                  "repeat(auto-fit, minmax(260px, 1fr))",

                gap:
                  10,

                padding:
                  14,
              }}
            >
              {(trends?.series ??
                []).length ===
              0 ? (
                <EmptyText text="No trend series available for this period." />
              ) : (
                trends?.series.map(
                  (
                    series,
                  ) => (
                    <div
                      key={
                        series.key
                      }
                      style={{
                        padding:
                          12,

                        border:
                          "1px solid var(--color-border)",

                        borderRadius:
                          8,

                        background:
                          "#fffefa",
                      }}
                    >
                      <strong
                        style={{
                          fontSize:
                            10,

                          textTransform:
                            "capitalize",
                        }}
                      >
                        {series.key.replace(
                          /_/g,
                          " ",
                        )}
                      </strong>


                      <div
                        style={{
                          display:
                            "flex",

                          alignItems:
                            "end",

                          gap:
                            4,

                          height:
                            90,

                          marginTop:
                            12,
                        }}
                      >
                        {series.points.map(
                          (
                            point,
                          ) => {
                            const max =
                              Math.max(
                                1,

                                ...series.points.map(
                                  (
                                    item,
                                  ) =>
                                    item.value,
                                ),
                              );


                            const height =
                              Math.max(
                                4,

                                (
                                  point.value /
                                  max
                                ) *
                                  80,
                              );


                            return (
                              <div
                                key={
                                  point.date
                                }
                                title={`${point.date}: ${point.value}`}
                                style={{
                                  flex:
                                    1,

                                  minWidth:
                                    3,

                                  height,

                                  borderRadius:
                                    "3px 3px 0 0",

                                  background:
                                    "#c7a23b",
                                }}
                              />
                            );
                          },
                        )}
                      </div>
                    </div>
                  ),
                )
              )}
            </div>
          </section>
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


function ProgressRow({
  label,
  value,
  percentage: width,
}: {
  label:
    string;

  value:
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
          {value}
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
              `${width}%`,

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


function UsageRow({
  icon,
  name,
  seconds,
  width,
}: {
  icon:
    React.ReactNode;

  name:
    string;

  seconds:
    number;

  width:
    number;
}) {
  return (
    <div
      style={{
        display:
          "grid",

        gridTemplateColumns:
          "26px minmax(0, 1fr) auto",

        gap:
          8,

        alignItems:
          "center",
      }}
    >
      <div
        style={{
          display:
            "grid",

          width:
            26,

          height:
            26,

          placeItems:
            "center",

          borderRadius:
            6,

          background:
            "#f3efe5",

          color:
            "#765c0c",
        }}
      >
        {icon}
      </div>


      <div
        style={{
          minWidth:
            0,
        }}
      >
        <div
          style={{
            overflow:
              "hidden",

            textOverflow:
              "ellipsis",

            whiteSpace:
              "nowrap",

            fontSize:
              9,

            fontWeight:
              600,
          }}
        >
          {name}
        </div>


        <div
          style={{
            height:
              4,

            marginTop:
              5,

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
                `${width}%`,

              height:
                "100%",

              background:
                "#b99123",
            }}
          />
        </div>
      </div>


      <span
        className="text-label"
        style={{
          fontSize:
            8,

          whiteSpace:
            "nowrap",
        }}
      >
        {formatDuration(
          seconds,
        )}
      </span>
    </div>
  );
}


function EmptyText({
  text,
}: {
  text:
    string;
}) {
  return (
    <div
      style={{
        padding:
          22,

        textAlign:
          "center",

        color:
          "#7a7d80",

        fontSize:
          9,
      }}
    >
      {text}
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