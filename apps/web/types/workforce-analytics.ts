export interface AnalyticsWindow {
  start_at:
    string;

  end_at:
    string;
}


export interface AnalyticsSeriesPoint {
  date:
    string;

  value:
    number;
}


export interface AnalyticsNamedUsage {
  name:
    string;

  duration_seconds:
    number;

  event_count:
    number;
}


export interface AnalyticsTrendSeries {
  key:
    string;

  points:
    AnalyticsSeriesPoint[];
}


export interface AnalyticsOverviewResponse {
  workspace_id:
    string;

  scope:
    string;

  window:
    AnalyticsWindow;

  employees:
    number;

  activity_events:
    number;

  active_events:
    number;

  idle_events:
    number;

  attendance_records:
    number;

  worked_minutes:
    number;

  app_intervals:
    number;

  app_seconds:
    number;

  website_intervals:
    number;

  website_seconds:
    number;

  goals_total:
    number;

  goals_completed:
    number;

  goals_average_progress:
    number;
}


export interface AnalyticsActivityResponse {
  workspace_id:
    string;

  scope:
    string;

  window:
    AnalyticsWindow;

  total_events:
    number;

  active_events:
    number;

  idle_events:
    number;

  average_idle_seconds:
    number;

  daily:
    AnalyticsSeriesPoint[];
}


export interface AnalyticsAttendanceResponse {
  workspace_id:
    string;

  scope:
    string;

  window:
    AnalyticsWindow;

  total_records:
    number;

  worked_minutes:
    number;

  break_minutes:
    number;

  status_breakdown:
    Record<
      string,
      number
    >;

  daily:
    AnalyticsSeriesPoint[];
}


export interface AnalyticsProductivityResponse {
  workspace_id:
    string;

  scope:
    string;

  window:
    AnalyticsWindow;

  activity_events:
    number;

  active_events:
    number;

  idle_events:
    number;

  app_seconds:
    number;

  website_seconds:
    number;

  worked_minutes:
    number;

  goals_total:
    number;

  goals_completed:
    number;

  goals_average_progress:
    number;
}


export interface AnalyticsAppsResponse {
  workspace_id:
    string;

  scope:
    string;

  window:
    AnalyticsWindow;

  total_intervals:
    number;

  total_seconds:
    number;

  top_apps:
    AnalyticsNamedUsage[];
}


export interface AnalyticsWebsitesResponse {
  workspace_id:
    string;

  scope:
    string;

  window:
    AnalyticsWindow;

  total_intervals:
    number;

  total_seconds:
    number;

  top_websites:
    AnalyticsNamedUsage[];
}


export interface AnalyticsGoalsResponse {
  workspace_id:
    string;

  scope:
    string;

  window:
    AnalyticsWindow;

  total:
    number;

  active:
    number;

  completed:
    number;

  cancelled:
    number;

  archived:
    number;

  average_progress:
    number;
}


export interface AnalyticsTrendsResponse {
  workspace_id:
    string;

  scope:
    string;

  window:
    AnalyticsWindow;

  series:
    AnalyticsTrendSeries[];
}