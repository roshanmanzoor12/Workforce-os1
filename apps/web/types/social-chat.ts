export type ConversationType =
  | "direct"
  | "group";


export type ConversationMemberRole =
  | "owner"
  | "admin"
  | "member";


export type ChatMessageType =
  | "text"
  | "system";


export type FriendshipStatus =
  | "pending"
  | "accepted"
  | "blocked";


export type PresenceStatus =
  | "online"
  | "idle"
  | "dnd"
  | "offline";


export interface ConversationPublic {
  id: string;

  conversation_type: ConversationType;

  name: string | null;

  created_by_user_id: string;

  is_active: boolean;

  created_at: string;

  updated_at: string;
}


export interface ConversationMemberPublic {
  user_id: string;

  role: ConversationMemberRole;

  joined_at: string;

  left_at: string | null;
}


export interface DirectConversationCreateRequest {
  target_user_id: string;
}


export interface GroupConversationCreateRequest {
  name: string;

  member_user_ids: string[];
}


export interface ChatMessagePublic {
  id: string;

  conversation_id: string;

  sender_user_id: string | null;

  message_type: ChatMessageType;

  content: string;

  edited_at: string | null;

  deleted_at: string | null;

  created_at: string;
}


export interface ChatMessagePagePublic {
  items: ChatMessagePublic[];

  next_cursor: string | null;

  has_more: boolean;
}


export interface MessageCreateRequest {
  content: string;
}


export interface MessageEditRequest {
  content: string;
}


export interface MessageReceiptPublic {
  message_id: string;

  user_id: string;

  read_at: string;
}


export interface FriendshipPublic {
  id: string;

  user_low_id: string;

  user_high_id: string;

  requested_by_user_id: string;

  status: FriendshipStatus;

  created_at: string;

  updated_at: string;

  accepted_at: string | null;

  blocked_at: string | null;
}

export interface FriendUserPublic {
  id: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  avatar_url: string | null;
}

export interface FriendshipListResponse {
  items: FriendshipPublic[];
}


export interface PresencePublic {
  user_id: string;

  status: PresenceStatus;

  last_seen_at: string;

  updated_at: string;
}


export interface PresenceUpdateRequest {
  status: PresenceStatus;
}


export interface TypingUsersResponse {
  user_ids?: string[];
}


export interface RealtimeActionResponse {
  success?: boolean;

  message?: string;
}


export interface WebSocketTicketResponse {
  ticket: string;

  expires_in_seconds: number;
}