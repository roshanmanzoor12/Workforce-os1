export interface ReviewCycleCreate {
  name: string;
  starts_on: string;
  ends_on: string;
}

export interface CyclePublic {
  id: string;
  workspace_id: string;
  name: string;
  starts_on: string;
  ends_on: string;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface ReviewCreate {
  cycle_id: string;
  employee_id: string;
  rating: number;
  summary: string;
}

export interface ReviewPublic {
  id: string;
  workspace_id: string;
  cycle_id: string;
  employee_id: string;
  rating: number;
  summary: string;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface ReviewList {
  items: ReviewPublic[];
  total: number;
}