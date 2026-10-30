import type { ChatMessagePublic } from "@/types/social-chat";

export interface FeatureMessage extends ChatMessagePublic {
  client_message_id: string | null;
  reply_to_message_id: string | null;
  reactions: Record<string, number>;
  pinned: boolean;
  delivered_at: string | null;
  read_at: string | null;
}

export interface ConversationFeatureSummary {
  conversation_id: string;
  unread_count: number;
  pinned: boolean;
  muted: boolean;
  archived: boolean;
  last_read_at: string | null;
}

export interface DeliveryState {
  message_id: string;
  user_id: string;
  delivered_at: string;
  read_at: string | null;
}
