export type MeetingType =
  | "video"
  | "voice"
  | "in_person";


export type MeetingStatus =
  | "scheduled"
  | "active"
  | "completed"
  | "cancelled";


export type MeetingParticipantRole =
  | "organizer"
  | "participant";


export type MeetingParticipantStatus =
  | "invited"
  | "accepted"
  | "declined";


export interface MeetingPublic {
  id: string;

  title: string;

  description: string | null;

  meeting_type: MeetingType;

  status: MeetingStatus;

  scheduled_start_at: string;

  scheduled_end_at: string | null;

  started_at: string | null;

  ended_at: string | null;

  location: string | null;

  created_by_user_id: string;

  created_at: string;

  updated_at: string;
}


export interface MeetingParticipantPublic {
  id: string;

  meeting_id: string;

  employee_id: string;

  participant_role: MeetingParticipantRole;

  status: MeetingParticipantStatus;

  created_at: string;

  updated_at: string;
}


export interface MeetingCreateRequest {
  title: string;

  description?: string | null;

  meeting_type?: MeetingType;

  scheduled_start_at: string;

  scheduled_end_at?: string | null;

  location?: string | null;

  participant_employee_ids?: string[];
}


export interface MeetingUpdateRequest {
  title?: string | null;

  description?: string | null;

  meeting_type?: MeetingType | null;

  scheduled_start_at?: string | null;

  scheduled_end_at?: string | null;

  location?: string | null;
}


export interface MeetingListResponse {
  meetings?: MeetingPublic[];

  total: number;
}


export interface MeetingDetailResponse {
  meeting: MeetingPublic;

  participants?: MeetingParticipantPublic[];
}


export interface MeetingResponse {
  message: string;

  meeting: MeetingPublic;
}


export interface MeetingParticipantAddRequest {
  employee_id: string;

  participant_role?: MeetingParticipantRole;
}


export interface MeetingParticipantStatusRequest {
  status: MeetingParticipantStatus;
}


export interface MeetingParticipantResponse {
  message: string;

  participant: MeetingParticipantPublic;
}


export interface MeetingInvitationPublic {
  meeting_id: string;

  title: string;

  meeting_type: MeetingType;

  meeting_status: MeetingStatus;

  scheduled_start_at: string;

  scheduled_end_at: string | null;

  participant_status: MeetingParticipantStatus;
}


export interface MeetingInvitationListResponse {
  invitations?: MeetingInvitationPublic[];

  total: number;
}


export interface MeetingSelfResponseRequest {
  status: MeetingParticipantStatus;
}


export interface MeetingSelfResponseResult {
  meeting_id: string;

  employee_id: string;

  status: MeetingParticipantStatus;
}


export interface MeetingSelfResponse {
  message: string;

  participant: MeetingSelfResponseResult;
}