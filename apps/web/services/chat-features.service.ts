import { api } from "@/lib/api/client";
import { getChatOwner, publishChatRead } from "@/lib/chat-live-events";
import type { ConversationFeatureSummary, DeliveryState, FeatureMessage } from "@/types/chat-features";

const newClientMessageId = () => crypto.randomUUID();

async function sendMessage(conversationId: string, content: string, options: { clientMessageId?: string; replyToMessageId?: string | null } = {}) {
  const clientMessageId = options.clientMessageId ?? newClientMessageId();
  return api.post<FeatureMessage>(`/chat/${conversationId}/messages/features`, {
    content, client_message_id: clientMessageId, reply_to_message_id: options.replyToMessageId ?? null,
  });
}
const listMessages = (conversationId: string) => api.get<FeatureMessage[]>(`/chat/${conversationId}/messages/features`);
const addReaction = (conversationId: string, messageId: string, emoji: string) => api.put<void>(`/chat/${conversationId}/messages/${messageId}/reactions`, { emoji });
const removeReaction = (conversationId: string, messageId: string, emoji: string) => api.delete<void>(`/chat/${conversationId}/messages/${messageId}/reactions/${encodeURIComponent(emoji)}`);
const pinMessage = (conversationId: string, messageId: string) => api.put<void>(`/chat/${conversationId}/messages/${messageId}/pin`);
const unpinMessage = (conversationId: string, messageId: string) => api.delete<void>(`/chat/${conversationId}/messages/${messageId}/pin`);
const setConversationPreference = (conversationId: string, patch: { pinned?: boolean; muted?: boolean; archived?: boolean }) => api.patch<ConversationFeatureSummary>(`/chat/${conversationId}/preferences`, patch);
const listConversationFeatures = () => api.get<ConversationFeatureSummary[]>("/chat/conversations/features");
const markDelivered = (conversationId: string, messageId: string) => api.post<DeliveryState>(`/chat/${conversationId}/messages/${messageId}/delivered`, {});
async function markReadThrough(
  conversationId: string,
  messageId: string,
): Promise<ConversationFeatureSummary> {
  const owner = getChatOwner();
  const summary = await api.post<ConversationFeatureSummary>(
    `/chat/${conversationId}/read-through/${messageId}`,
    {},
  );
  publishChatRead(owner, summary);
  return summary;
}

export const chatFeaturesService = { newClientMessageId, sendMessage, listMessages, addReaction, removeReaction, pinMessage, unpinMessage, setConversationPreference, listConversationFeatures, markDelivered, markReadThrough };
