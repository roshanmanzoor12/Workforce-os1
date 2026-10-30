export interface MonitoringCapabilityResponse {
  monitoring_view:
    boolean;

  monitoring_manage:
    boolean;

  live_screen_view:
    boolean;

  settings_manage:
    boolean;
}


export interface MonitoringControlSummaryResponse {
  role_key:
    string;

  capabilities:
    MonitoringCapabilityResponse;

  permissions?:
    string[];
}


export interface MonitoringAccessResponse {
  permission:
    string;

  allowed:
    boolean;
}