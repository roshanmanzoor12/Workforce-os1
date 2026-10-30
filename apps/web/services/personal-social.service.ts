import { api } from "@/lib/api/client";
import type { ChatMessagePagePublic, ConversationPublic, FriendshipPublic } from "@/types/social-chat";

export interface Person {
  id: string;
  username: string;
  name: string;
  avatar_url: string | null;
}
export interface PersonalFriend extends FriendshipPublic {
  person: Person;
  direction: "incoming" | "outgoing";
  blocked_by_me: boolean;
  presence: "online" | "idle" | "dnd" | "offline";
}
export interface PersonalConversation extends ConversationPublic {
  members: (Person & { role: "owner" | "admin" | "member" })[];
  can_message: boolean;
}
export type FriendAction = "accept" | "reject" | "cancel" | "remove" | "block" | "unblock";
export const personalSocialService = {
  lookup: (query: string) => api.get<Person>("/personal/social/people", { query: { query } }),
  friends: () => api.get<{ items: PersonalFriend[] }>("/personal/social/friends"),
  request: (identifier: string) => api.post<FriendshipPublic>("/personal/social/requests", { identifier }),
  action: (id: string, action: FriendAction) => api.post<{ success: boolean }>(`/personal/social/friends/${id}/${action}`, {}),
  conversations: () => api.get<PersonalConversation[]>("/personal/social/conversations"),
  messages: (id: string, cursor?: string | null) => api.get<ChatMessagePagePublic>(`/personal/social/conversations/${id}/messages`, { query: { cursor, limit: 50 } }),
};
export function conversationName(conversation: PersonalConversation, userId?: string) {
  return conversation.conversation_type === "group"
    ? conversation.name || "Group conversation"
    : conversation.members.find((member) => member.id !== userId)?.name || "Direct conversation";
}