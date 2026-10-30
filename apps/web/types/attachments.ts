export type AttachmentScope =
  | "CONVERSATION"
  | "CHANNEL";


export type AttachmentKind =
  | "IMAGE"
  | "VIDEO"
  | "AUDIO"
  | "FILE";


export type AttachmentStatus =
  | "PENDING"
  | "READY"
  | "DELETED"
  | "FAILED";


export interface AttachmentPlanLimitResponse {
  plan: string;

  max_size_bytes: number;

  max_size_mb: number;
}


export type AttachmentPlanLimit =
  AttachmentPlanLimitResponse;


export interface AttachmentPrepareRequest {
  scope: AttachmentScope;

  conversation_id?:
    | string
    | null;

  channel_id?:
    | string
    | null;

  filename: string;

  content_type: string;

  size_bytes: number;
}


export type AttachmentPreparePayload =
  AttachmentPrepareRequest;


export interface AttachmentPrepareResponse {
  attachment_id: string;

  upload_url: string;

  upload_method: string;

  expires_in_seconds: number;

  max_size_bytes: number;
}


export interface AttachmentCompleteRequest {
  checksum_sha256?:
    | string
    | null;
}


export interface AttachmentResponse {
  id: string;

  owner_user_id: string;

  scope: AttachmentScope;

  conversation_id:
    | string
    | null;

  channel_id:
    | string
    | null;

  message_id:
    | string
    | null;

  kind: AttachmentKind;

  status: AttachmentStatus;

  original_filename: string;

  content_type: string;

  size_bytes: number;

  created_at: string;

  ready_at:
    | string
    | null;
}


export type Attachment =
  AttachmentResponse;


export interface BoundAttachmentResponse {
  attachment_id: string;

  message_id: string;

  scope: AttachmentScope;

  conversation_id:
    | string
    | null;

  channel_id:
    | string
    | null;

  kind: AttachmentKind;

  filename: string;

  content_type: string;

  size_bytes: number;

  ready_at:
    | string
    | null;
}


export type BoundAttachment =
  BoundAttachmentResponse;


export interface AttachmentBindRequest {
  attachment_ids: string[];
}


export interface AttachmentBindResponse {
  message_id: string;

  attachments:
    BoundAttachmentResponse[];
}


export interface MessageAttachmentsResponse {
  message_id: string;

  attachments:
    BoundAttachmentResponse[];
}


export interface AttachmentDownloadResponse {
  attachment_id: string;

  download_url: string;

  expires_in_seconds: number;
}


export interface UploadAttachmentResult {
  attachment_id: string;

  attachment:
    AttachmentResponse;
}


export interface PreparedChannelAttachment {
  attachment:
    AttachmentResponse;

  file: File;
}


export interface PreparedConversationAttachment {
  attachment:
    AttachmentResponse;

  file: File;
}