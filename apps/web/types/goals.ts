export type GoalPriority =
  | "low"
  | "medium"
  | "high";


export type GoalStatus =
  | "active"
  | "completed"
  | "cancelled"
  | "archived";


export interface GoalPublic {
  id:
    string;

  owner_employee_id:
    string | null;

  owner_user_id?:
    string;

  title:
    string;

  description:
    string | null;

  status:
    GoalStatus;

  priority:
    GoalPriority;

  progress_percent:
    number;

  start_date:
    string | null;

  due_date:
    string | null;

  completed_at:
    string | null;

  created_at:
    string;

  updated_at:
    string;
}


export interface GoalListResponse {
  items:
    GoalPublic[];

  total:
    number;
}


export interface GoalCreateRequest {
  owner_employee_id:
    string;

  title:
    string;

  description?:
    string | null;

  priority?:
    GoalPriority;

  start_date?:
    string | null;

  due_date?:
    string | null;
}


export interface GoalUpdateRequest {
  title?:
    string | null;

  description?:
    string | null;

  priority?:
    GoalPriority | null;

  status?:
    GoalStatus | null;

  progress_percent?:
    number | null;

  start_date?:
    string | null;

  due_date?:
    string | null;
}