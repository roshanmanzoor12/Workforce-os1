import {
  api,
} from "@/lib/api/client";

import type {
  AnalyticsActivityResponse,
  AnalyticsAppsResponse,
  AnalyticsAttendanceResponse,
  AnalyticsGoalsResponse,
  AnalyticsOverviewResponse,
  AnalyticsProductivityResponse,
  AnalyticsTrendsResponse,
  AnalyticsWebsitesResponse,
} from "@/types/workforce-analytics";


export interface AnalyticsWindowQuery {
  startAt?:
    string | null;

  endAt?:
    string | null;
}


function buildQuery(
  options?:
    AnalyticsWindowQuery,
) {
  return {
    start_at:
      options?.startAt ??
      undefined,

    end_at:
      options?.endAt ??
      undefined,
  };
}


async function overview(
  workspaceId:
    string,

  options?:
    AnalyticsWindowQuery,
): Promise<AnalyticsOverviewResponse> {
  return api.get<AnalyticsOverviewResponse>(
    `/workspaces/${workspaceId}/analytics/overview`,
    {
      query:
        buildQuery(
          options,
        ),
    },
  );
}


async function activity(
  workspaceId:
    string,

  options?:
    AnalyticsWindowQuery,
): Promise<AnalyticsActivityResponse> {
  return api.get<AnalyticsActivityResponse>(
    `/workspaces/${workspaceId}/analytics/activity`,
    {
      query:
        buildQuery(
          options,
        ),
    },
  );
}


async function attendance(
  workspaceId:
    string,

  options?:
    AnalyticsWindowQuery,
): Promise<AnalyticsAttendanceResponse> {
  return api.get<AnalyticsAttendanceResponse>(
    `/workspaces/${workspaceId}/analytics/attendance`,
    {
      query:
        buildQuery(
          options,
        ),
    },
  );
}


async function productivity(
  workspaceId:
    string,

  options?:
    AnalyticsWindowQuery,
): Promise<AnalyticsProductivityResponse> {
  return api.get<AnalyticsProductivityResponse>(
    `/workspaces/${workspaceId}/analytics/productivity`,
    {
      query:
        buildQuery(
          options,
        ),
    },
  );
}


async function apps(
  workspaceId:
    string,

  options?:
    AnalyticsWindowQuery,
): Promise<AnalyticsAppsResponse> {
  return api.get<AnalyticsAppsResponse>(
    `/workspaces/${workspaceId}/analytics/apps`,
    {
      query:
        buildQuery(
          options,
        ),
    },
  );
}


async function websites(
  workspaceId:
    string,

  options?:
    AnalyticsWindowQuery,
): Promise<AnalyticsWebsitesResponse> {
  return api.get<AnalyticsWebsitesResponse>(
    `/workspaces/${workspaceId}/analytics/websites`,
    {
      query:
        buildQuery(
          options,
        ),
    },
  );
}


async function goals(
  workspaceId:
    string,

  options?:
    AnalyticsWindowQuery,
): Promise<AnalyticsGoalsResponse> {
  return api.get<AnalyticsGoalsResponse>(
    `/workspaces/${workspaceId}/analytics/goals`,
    {
      query:
        buildQuery(
          options,
        ),
    },
  );
}


async function trends(
  workspaceId:
    string,

  options?:
    AnalyticsWindowQuery,
): Promise<AnalyticsTrendsResponse> {
  return api.get<AnalyticsTrendsResponse>(
    `/workspaces/${workspaceId}/analytics/trends`,
    {
      query:
        buildQuery(
          options,
        ),
    },
  );
}


export const workforceAnalyticsService = {
  overview,

  activity,

  attendance,

  productivity,

  apps,

  websites,

  goals,

  trends,
};