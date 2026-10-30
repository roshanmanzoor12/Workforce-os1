import { api } from "@/lib/api/client";
import { chatFeaturesService } from "@/services/chat-features.service";

import type {
  ChatMessagePagePublic,
  ChatMessagePublic,
  ConversationMemberPublic,
  ConversationPublic,
  FriendUserPublic,
  FriendshipListResponse,
  FriendshipPublic,
  FriendshipStatus,
  GroupConversationCreateRequest,
  MessageReceiptPublic,
  PresencePublic,
  PresenceStatus,
  RealtimeActionResponse,
  TypingUsersResponse,
  WebSocketTicketResponse,
} from "@/types/social-chat";

interface ConversationPreferencePatch {
  pinned?: boolean | null;
  muted?: boolean | null;
  archived?: boolean | null;
}

interface ConversationFeatureSummary {
  conversation_id: string;
  unread_count: number;
  pinned: boolean;
  muted: boolean;
  archived: boolean;
  last_read_at: string | null;
}

interface CreateCallSessionRequest {
  conversation_id: string;
  call_type: "voice" | "video" | "screen";
  invited_user_ids?: string[];
}

interface CallSessionResponse {
  id: string;
  scope: "CONVERSATION" | "CHANNEL";
  conversation_id: string | null;
  channel_id: string | null;
  started_by_user_id: string;
  kind: "VOICE" | "VIDEO";
  status: "RINGING" | "ACTIVE" | "ENDED" | "CANCELLED";
  created_at: string;
  started_at: string | null;
  ended_at: string | null;

  /*
   * Kept optional for compatibility with callers.
   * The documented /calls response does not supply a join URL.
   */
  join_url?: string | null;
}

type MessageContentInput =
  | string
  | {
      content: string;
    };

/* Friends */

async function listFriends(
  status?: FriendshipStatus | null,
): Promise<FriendshipListResponse> {
  return api.get<FriendshipListResponse>(
    "/friends",
    {
      query: {
        status: status ?? undefined,
      },
    },
  );
}

async function lookupFriend(
  identifier: string,
): Promise<FriendUserPublic> {
  const normalizedIdentifier = identifier
    .trim()
    .replace(/^@/, "");

  if (!normalizedIdentifier) {
    throw new Error("Enter a username or account ID.");
  }

  return api.get<FriendUserPublic>(
    "/friends/lookup",
    {
      query: {
        identifier: normalizedIdentifier,
      },
    },
  );
}

async function sendFriendRequest(
  targetUserId: string,
): Promise<FriendshipPublic> {
  return api.post<FriendshipPublic>(
    `/friends/requests/${targetUserId}`,
    {},
  );
}

async function acceptFriendRequest(
  friendshipId: string,
): Promise<FriendshipPublic> {
  return api.post<FriendshipPublic>(
    `/friends/requests/${friendshipId}/accept`,
    {},
  );
}

async function rejectFriendRequest(
  friendshipId: string,
): Promise<void> {
  await api.delete<void>(
    `/friends/requests/${friendshipId}`,
  );
}

async function blockUser(
  targetUserId: string,
): Promise<FriendshipPublic> {
  return api.post<FriendshipPublic>(
    `/friends/blocks/${targetUserId}`,
    {},
  );
}

async function unblockUser(
  targetUserId: string,
): Promise<void> {
  await api.delete<void>(
    `/friends/blocks/${targetUserId}`,
  );
}

/* Conversations */

async function listConversations(): Promise<
  ConversationPublic[]
> {
  return api.get<ConversationPublic[]>(
    "/chat/conversations",
  );
}

async function createOrGetDirect(
  targetUserId: string,
): Promise<ConversationPublic> {
  return api.post<ConversationPublic>(
    "/chat/direct",
    {
      target_user_id: targetUserId,
    },
  );
}

async function createGroup(
  payload: GroupConversationCreateRequest,
): Promise<ConversationPublic> {
  return api.post<ConversationPublic>(
    "/chat/groups",
    payload,
  );
}

async function addGroupMember(
  conversationId: string,
  targetUserId: string,
): Promise<ConversationMemberPublic> {
  return api.post<ConversationMemberPublic>(
    `/chat/${conversationId}/members/${targetUserId}`,
    {},
  );
}

async function removeGroupMember(
  conversationId: string,
  targetUserId: string,
): Promise<void> {
  await api.delete<void>(
    `/chat/${conversationId}/members/${targetUserId}`,
  );
}

async function updatePreferences(
  conversationId: string,
  payload: ConversationPreferencePatch,
): Promise<ConversationFeatureSummary> {
  return api.patch<ConversationFeatureSummary>(
    `/chat/${conversationId}/preferences`,
    payload,
  );
}

/* Messages */

async function listMessages(
  conversationId: string,
  limit = 100,
): Promise<ChatMessagePublic[]> {
  return api.get<ChatMessagePublic[]>(
    `/chat/${conversationId}/messages`,
    {
      query: {
        limit,
      },
    },
  );
}

/*
 * Preserve listMessages and expose the name used by Groups.
 */
async function getMessages(
  conversationId: string,
  limit = 100,
): Promise<ChatMessagePublic[]> {
  return listMessages(conversationId, limit);
}

async function listMessagePage(
  conversationId: string,
  cursor?: string | null,
  limit = 50,
): Promise<ChatMessagePagePublic> {
  return api.get<ChatMessagePagePublic>(
    `/chat/${conversationId}/messages-page`,
    {
      query: {
        cursor: cursor ?? undefined,
        limit,
      },
    },
  );
}

/*
 * Existing callers can continue passing a string.
 * Groups can also pass { content }.
 * Both produce the existing backend payload.
 */
async function sendMessage(
  conversationId: string,
  input: MessageContentInput,
): Promise<ChatMessagePublic> {
  const content =
    typeof input === "string"
      ? input
      : input.content;

  return api.post<ChatMessagePublic>(
    `/chat/${conversationId}/messages`,
    {
      content,
    },
  );
}

async function editMessage(
  conversationId: string,
  messageId: string,
  content: string,
): Promise<ChatMessagePublic> {
  return api.patch<ChatMessagePublic>(
    `/chat/${conversationId}/messages/${messageId}`,
    {
      content,
    },
  );
}

async function deleteMessage(
  conversationId: string,
  messageId: string,
): Promise<ChatMessagePublic> {
  return api.delete<ChatMessagePublic>(
    `/chat/${conversationId}/messages/${messageId}`,
  );
}

async function markRead(
  conversationId: string,
  messageId: string,
): Promise<MessageReceiptPublic> {
  return api.post<MessageReceiptPublic>(
    `/chat/${conversationId}/read/${messageId}`,
    {},
  );
}

/*
 * Compatibility name used by Groups.
 * Retains the existing backend read-receipt operation.
 */
async function markReadThrough(
  conversationId: string,
  messageId: string,
): Promise<ConversationFeatureSummary> {
  return chatFeaturesService.markReadThrough(conversationId, messageId);
}

async function listReadReceipts(
  conversationId: string,
  messageId: string,
): Promise<MessageReceiptPublic[]> {
  return api.get<MessageReceiptPublic[]>(
    `/chat/${conversationId}/read-receipts/${messageId}`,
  );
}

async function addReaction(
  conversationId: string,
  messageId: string,
  emoji: string,
): Promise<void> {
  await api.put<void>(
    `/chat/${conversationId}/messages/${messageId}/reactions`,
    {
      emoji,
    },
  );
}

async function removeReaction(
  conversationId: string,
  messageId: string,
  emoji: string,
): Promise<void> {
  await api.delete<void>(
    `/chat/${conversationId}/messages/${messageId}/reactions/${encodeURIComponent(emoji)}`,
  );
}

/* Calls */

async function createCallSession(
  payload: CreateCallSessionRequest,
): Promise<CallSessionResponse> {
  /*
   * Screen sharing is a media action inside a call.
   * It is not a third backend call kind.
   */
  if (payload.call_type === "screen") {
    throw new Error(
      "Start or join a voice/video call, then use its Share Screen control.",
    );
  }

  return api.post<CallSessionResponse>(
    "/calls",
    {
      scope: "CONVERSATION",
      kind:
        payload.call_type === "video"
          ? "VIDEO"
          : "VOICE",
      conversation_id: payload.conversation_id,
      ...(payload.invited_user_ids
        ? {
            invited_user_ids: payload.invited_user_ids,
          }
        : {}),
    },
  );
}

/* Presence */

async function updatePresence(
  status: PresenceStatus,
): Promise<PresencePublic> {
  return api.put<PresencePublic>(
    "/chat/presence",
    {
      status,
    },
  );
}

async function getPresence(
  userId: string,
): Promise<PresencePublic> {
  return api.get<PresencePublic>(
    `/chat/presence/${userId}`,
  );
}

/* Typing and realtime */

async function startTyping(
  conversationId: string,
): Promise<RealtimeActionResponse> {
  return api.post<RealtimeActionResponse>(
    `/chat/realtime/typing/${conversationId}/start`,
    {},
  );
}

async function stopTyping(
  conversationId: string,
): Promise<RealtimeActionResponse> {
  return api.post<RealtimeActionResponse>(
    `/chat/realtime/typing/${conversationId}/stop`,
    {},
  );
}

async function listTypingUsers(
  conversationId: string,
): Promise<TypingUsersResponse> {
  return api.get<TypingUsersResponse>(
    `/chat/realtime/typing/${conversationId}`,
  );
}

async function createRealtimeTicket(): Promise<
  WebSocketTicketResponse
> {
  return api.post<WebSocketTicketResponse>(
    "/chat/realtime/ticket",
    {},
  );
}

async function realtimeHeartbeat(): Promise<unknown> {
  return api.post<unknown>(
    "/chat/realtime/heartbeat",
    {},
  );
}

/*
 * All original methods remain exported.
 * Additional methods support the existing Groups page.
 */
export const socialChatService = {
  listFriends,
  lookupFriend,
  sendFriendRequest,
  acceptFriendRequest,
  rejectFriendRequest,
  blockUser,
  unblockUser,

  listConversations,
  createOrGetDirect,
  createGroup,
  addGroupMember,
  removeGroupMember,
  updatePreferences,

  listMessages,
  getMessages,
  listMessagePage,
  sendMessage,
  editMessage,
  deleteMessage,
  markRead,
  markReadThrough,
  listReadReceipts,
  addReaction,
  removeReaction,

  createCallSession,

  updatePresence,
  getPresence,

  startTyping,
  stopTyping,
  listTypingUsers,
  createRealtimeTicket,
  realtimeHeartbeat,
};