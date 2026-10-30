export type PlanCode =
  string;


export type SubscriptionStatus =
  string;


export interface BillingPlanPublic {
  code:
    PlanCode;

  display_name:
    string;

  workspace_limit:
    number;

  member_limit_per_workspace:
    number;

  monitoring_enabled:
    boolean;

  live_screen_enabled:
    boolean;

  advanced_analytics_enabled:
    boolean;
}


export interface BillingPlansResponse {
  plans:
    BillingPlanPublic[];
}


export interface CurrentSubscriptionPublic {
  plan_code:
    PlanCode;

  status:
    SubscriptionStatus;

  current_period_start:
    string | null;

  current_period_end:
    string | null;
}


export interface AccountEntitlementsPublic {
  plan_code:
    PlanCode;

  subscription_status:
    SubscriptionStatus;

  workspace_limit:
    number | null;

  workspace_count:
    number;

  create_workspace:
    boolean;

  monitoring:
    boolean;

  live_screen:
    boolean;

  advanced_analytics:
    boolean;
}


export interface WorkspaceCreationAccessResponse {
  allowed:
    boolean;

  reason:
    string | null;

  workspace_limit:
    number | null;

  workspace_count:
    number;
}
