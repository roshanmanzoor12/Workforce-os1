export interface AnalyticsWindow {
  start_at: string;
  end_at: string;
}

export interface AnalyticsOverviewResponse {
  workspace_id: string;
  scope: string;
  window: AnalyticsWindow;

  employees: number;
  activity_events: number;
  active_events: number;
  idle_events: number;

  attendance_records: number;
  worked_minutes: number;

  app_intervals: number;
  app_seconds: number;

  website_intervals: number;
  website_seconds: number;

  goals_total: number;
  goals_completed: number;
  goals_average_progress: number;
}