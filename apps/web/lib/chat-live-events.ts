
import type { ConversationFeatureSummary } from "@/types/chat-features";

export const CHAT_LIVE_EVENT = "workforce:chat-live";
export const CHAT_READ_EVENT = "workforce:chat-read";
export const CHAT_INBOX_EVENT = "workforce:chat-inbox";

let owner: string | null = null;
let snapshot: ConversationFeatureSummary[] | undefined;

export function setChatOwner(value: string | null) {
  if (owner !== value) snapshot = undefined;
  owner = value;
}

export function getChatOwner() {
  return owner;
}

export function getChatInbox(userId: string) {
  return owner === userId ? snapshot : undefined;
}

export function publishChatInbox(
  userId: string,
  items: ConversationFeatureSummary[],
) {
  if (owner !== userId) return;

  snapshot = items;

  window.dispatchEvent(
    new CustomEvent(CHAT_INBOX_EVENT, {
      detail: { owner: userId, items },
    }),
  );
}

export function publishChatRead(
  userId: string | null,
  summary: ConversationFeatureSummary,
) {
  if (!userId || owner !== userId) return;

  window.dispatchEvent(
    new CustomEvent(CHAT_READ_EVENT, {
      detail: { owner: userId, summary },
    }),
  );
}
