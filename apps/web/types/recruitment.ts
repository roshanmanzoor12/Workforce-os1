export type JobStatus =
  | "draft"
  | "open"
  | "paused"
  | "closed";


export type CandidateStatus =
  | "new"
  | "screening"
  | "interview"
  | "offer"
  | "hired"
  | "rejected"
  | "withdrawn";


export type InterviewStatus =
  | "scheduled"
  | "completed"
  | "cancelled"
  | "no_show";


export interface JobResponse {
  id: string;

  title: string;

  department_id:
    | string
    | null;

  description:
    | string
    | null;

  location:
    | string
    | null;

  employment_type:
    | string
    | null;

  closing_date:
    | string
    | null;

  status:
    JobStatus;
}


export interface JobListResponse {
  items: JobResponse[];

  total: number;
}


export interface JobCreateRequest {
  title: string;

  department_id:
    | string
    | null;

  description:
    | string
    | null;

  location:
    | string
    | null;

  employment_type:
    | string
    | null;

  closing_date:
    | string
    | null;
}


export interface JobUpdateRequest {
  title?:
    | string
    | null;

  department_id?:
    | string
    | null;

  description?:
    | string
    | null;

  location?:
    | string
    | null;

  employment_type?:
    | string
    | null;

  closing_date?:
    | string
    | null;

  status?:
    | JobStatus
    | null;
}


export interface CandidateResponse {
  id: string;

  job_id: string;

  first_name: string;

  last_name: string;

  email: string;

  phone:
    | string
    | null;

  resume_url:
    | string
    | null;

  notes:
    | string
    | null;

  status:
    CandidateStatus;
}


export interface CandidateListResponse {
  items: CandidateResponse[];

  total: number;
}


export interface CandidateCreateRequest {
  job_id: string;

  first_name: string;

  last_name: string;

  email: string;

  phone?:
    | string
    | null;

  resume_url?:
    | string
    | null;

  notes?:
    | string
    | null;
}


export interface CandidateUpdateRequest {
  first_name?:
    | string
    | null;

  last_name?:
    | string
    | null;

  email?:
    | string
    | null;

  phone?:
    | string
    | null;

  resume_url?:
    | string
    | null;

  notes?:
    | string
    | null;

  status?:
    | CandidateStatus
    | null;
}


export interface InterviewResponse {
  id: string;

  candidate_id: string;

  interviewer_user_id:
    | string
    | null;

  starts_at: string;

  ends_at:
    | string
    | null;

  status:
    InterviewStatus;

  notes:
    | string
    | null;
}


export interface InterviewListResponse {
  items: InterviewResponse[];

  total: number;
}


export interface InterviewCreateRequest {
  candidate_id: string;

  interviewer_user_id?:
    | string
    | null;

  starts_at: string;

  ends_at?:
    | string
    | null;

  notes?:
    | string
    | null;
}


export interface InterviewUpdateRequest {
  interviewer_user_id?:
    | string
    | null;

  starts_at?:
    | string
    | null;

  ends_at?:
    | string
    | null;

  status?:
    | InterviewStatus
    | null;

  notes?:
    | string
    | null;
}