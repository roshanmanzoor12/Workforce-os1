export type AttendanceStatus =
  | "present"
  | "absent"
  | "late"
  | "half_day"
  | "on_leave"
  | "holiday";


export type AttendanceSource =
  | "manual"
  | "web"
  | "desktop_agent"
  | "import"
  | "system";


export type AttendanceEventType =
  | "check_in"
  | "check_out"
  | "break_start"
  | "break_end";


export interface AttendanceRecordPublic {
  id:
    string;

  employee_id:
    string;

  attendance_date:
    string;

  status:
    AttendanceStatus;

  source:
    AttendanceSource;

  check_in_at:
    string | null;

  check_out_at:
    string | null;

  worked_minutes:
    number;

  break_minutes:
    number;

  notes:
    string | null;

  created_by_user_id:
    string | null;

  updated_by_user_id:
    string | null;

  created_at:
    string;

  updated_at:
    string;
}


export interface AttendanceEventPublic {
  id:
    string;

  attendance_record_id:
    string;

  employee_id:
    string;

  event_type:
    AttendanceEventType;

  source:
    AttendanceSource;

  occurred_at:
    string;

  actor_user_id:
    string | null;

  notes:
    string | null;

  created_at:
    string;

  updated_at:
    string;
}


export interface AttendanceEventCreateRequest {
  event_type:
    AttendanceEventType;

  occurred_at:
    string;

  source?:
    AttendanceSource;

  notes?:
    string | null;
}


export interface AttendanceEventResponse {
  message:
    string;

  event:
    AttendanceEventPublic;
}


export interface AttendanceListResponse {
  attendance?:
    AttendanceRecordPublic[];

  total:
    number;
}


export interface AttendanceRecordDetailResponse {
  attendance:
    AttendanceRecordPublic;

  events?:
    AttendanceEventPublic[];
}


export interface AttendanceRecordUpdateRequest {
  status?:
    AttendanceStatus | null;

  source?:
    AttendanceSource | null;

  notes?:
    string | null;
}


export interface AttendanceRecordResponse {
  message:
    string;

  attendance:
    AttendanceRecordPublic;
}


export interface AttendanceSummaryResponse {
  employee_id:
    string;

  start_date:
    string;

  end_date:
    string;

  present_days:
    number;

  absent_days:
    number;

  late_days:
    number;

  half_days:
    number;

  leave_days:
    number;

  holiday_days:
    number;

  worked_minutes:
    number;

  break_minutes:
    number;
}