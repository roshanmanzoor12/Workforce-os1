
"use client";

import { useEffect, useState } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
import { chatFeaturesService } from "@/services/chat-features.service";
import { PersonalChatRealtimeClient } from "@/lib/realtime/personal-chat-realtime-client";
import type { ConversationFeatureSummary } from "@/types/chat-features";
import {
  CHAT_INBOX_EVENT,
  CHAT_LIVE_EVENT,
  CHAT_READ_EVENT,
  getChatInbox,
  publishChatInbox,
  setChatOwner,
} from "@/lib/chat-live-events";

export function useChatInbox(userId: string | undefined) {
  const [value, setValue] = useState<{
    owner: string;
    items: ConversationFeatureSummary[];
  } | null>(null);

  useEffect(() => {
    if (!userId) {
      setValue(null);
      return;
    }

    const cached = getChatInbox(userId);

    if (cached) {
      setValue({ owner: userId, items: cached });
    }

    function update(event: Event) {
      const detail = (
        event as CustomEvent<{
          owner: string;
          items: ConversationFeatureSummary[];
        }>
      ).detail;

      if (detail.owner === userId) setValue(detail);
    }

    window.addEventListener(CHAT_INBOX_EVENT, update);

    return () => {
      window.removeEventListener(CHAT_INBOX_EVENT, update);
    };
  }, [userId]);

  return value && value.owner === userId
    ? value.items
    : undefined;
}

export function ChatLiveSync() {
  const { user, mode } = useWorkspace();
  const userId = user?.id;
  const verified = user?.is_email_verified;

  useEffect(() => {
    if (!userId || !verified || mode !== "personal") {
      setChatOwner(null);
      return;
    }

    const owner = userId;
    setChatOwner(owner);

    let stopped = false;
    let running = false;
    let queued = false;
    let version = 0;

    async function refresh() {
      queued = true;

      if (running || stopped) return;

      running = true;

      try {
        while (queued && !stopped) {
          queued = false;
          const requestVersion = version;
          const items =
            await chatFeaturesService.listConversationFeatures();

          if (!stopped && requestVersion === version) {
            publishChatInbox(owner, items);
          } else if (!stopped) {
            queued = true;
          }
        }
      } catch {
        // Reconnect/focus retries while preserving the current UI.
      } finally {
        running = false;
      }
    }

    function read(event: Event) {
      const detail = (
        event as CustomEvent<{
          owner: string;
          summary: ConversationFeatureSummary;
        }>
      ).detail;

      if (detail.owner !== owner || stopped) return;

      version += 1;

      const current = getChatInbox(owner) ?? [];

      publishChatInbox(owner, [
        ...current.filter(
          item =>
            item.conversation_id !== detail.summary.conversation_id,
        ),
        detail.summary,
      ]);

      void refresh();
    }

    const client = new PersonalChatRealtimeClient({
      onMessages: () => {},

      onStateChange: state => {
        if (state === "connected") void refresh();
      },

      onEvent: event => {
        const type = String(
          event.event_type ?? event.event ?? "",
        ).toLowerCase();

        if (!/message|member|conversation/.test(type)) return;

        window.dispatchEvent(
          new CustomEvent(CHAT_LIVE_EVENT, {
            detail: { owner, event },
          }),
        );

        void refresh();
      },
    });

    function resume() {
      if (document.hidden) return;

      void client.connect();
      void refresh();
    }

    window.addEventListener(CHAT_READ_EVENT, read);
    window.addEventListener("focus", resume);
    window.addEventListener("online", resume);
    document.addEventListener("visibilitychange", resume);

    void client.connect();
    void refresh();

    return () => {
      stopped = true;
      client.disconnect();

      window.removeEventListener(CHAT_READ_EVENT, read);
      window.removeEventListener("focus", resume);
      window.removeEventListener("online", resume);
      document.removeEventListener("visibilitychange", resume);

      setChatOwner(null);
    };
  }, [userId, verified, mode]);

  return null;
}
