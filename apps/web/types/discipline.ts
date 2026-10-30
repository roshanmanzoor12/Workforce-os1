export type IncidentStatus =
  | "open"
  | "under_review"
  | "resolved"
  | "dismissed";

export interface IncidentCreate {
  employee_id: string;
  category: string;
  summary: string;
  details?: string | null;
  action?: string | null;
}

export interface IncidentUpdate {
  status?: IncidentStatus | null;
  action?: string | null;
}

export interface IncidentPublic {
  id: string;
  employee_id: string;
  reported_by_user_id: string;
  category: string;
  summary: string;
  details: string | null;
  action: string | null;
  status: string;
  created_at: string;
  resolved_at: string | null;
}

export interface IncidentList {
  items: IncidentPublic[];
  total: number;
}