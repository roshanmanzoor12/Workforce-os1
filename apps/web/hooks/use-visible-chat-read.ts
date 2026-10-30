
"use client";

import {
  useEffect,
  useRef,
  type RefObject,
} from "react";
import { chatFeaturesService } from "@/services/chat-features.service";
import type { ChatMessagePublic } from "@/types/social-chat";

export function useVisibleChatRead(
  conversationId: string | null,
  userId: string | undefined,
  messages: ChatMessagePublic[],
  viewport: RefObject<HTMLDivElement | null>,
  blocked = false,
) {
  const hasMessages = messages.length > 0;
  const latest = useRef({ messages, blocked });

  latest.current = { messages, blocked };

  const wake = useRef<() => void>(() => {});

  useEffect(() => {
    if (!conversationId || !userId) return;

    const id = conversationId;
    const owner = userId;

    let stopped = false;
    let pending = false;
    let acknowledged = "";
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function check() {
      const element = viewport.current;

      if (
        stopped ||
        pending ||
        latest.current.blocked ||
        document.hidden ||
        !document.hasFocus() ||
        !element?.getClientRects().length
      ) {
        return;
      }

      if (
        element.scrollHeight -
          element.scrollTop -
          element.clientHeight >
        60
      ) {
        return;
      }

      const message = [...latest.current.messages]
        .reverse()
        .find(
          item =>
            item.sender_user_id &&
            item.sender_user_id !== owner &&
            !item.deleted_at,
        );

      if (!message || message.id === acknowledged) return;

      pending = true;
      let success = false;

      try {
        await chatFeaturesService.markReadThrough(
          id,
          message.id,
        );

        if (!stopped) {
          acknowledged = message.id;
          success = true;
        }
      } catch {
        if (!stopped) {
          timer = setTimeout(() => void check(), 2000);
        }
      } finally {
        pending = false;

        if (!stopped && success) void check();
      }
    }

    const trigger = () => {
      void check();
    };

    wake.current = trigger;

    const element = viewport.current;

    element?.addEventListener("scroll", trigger, {
      passive: true,
    });

    window.addEventListener("focus", trigger);
    document.addEventListener("visibilitychange", trigger);

    const observer = new ResizeObserver(trigger);

    if (element) observer.observe(element);

    trigger();

    return () => {
      stopped = true;
      clearTimeout(timer);

      element?.removeEventListener("scroll", trigger);
      window.removeEventListener("focus", trigger);
      document.removeEventListener(
        "visibilitychange",
        trigger,
      );
      observer.disconnect();

      if (wake.current === trigger) {
        wake.current = () => {};
      }
    };
  }, [
    conversationId,
    userId,
    viewport,
    hasMessages,
  ]);

  useEffect(() => {
    wake.current();
  }, [messages, blocked]);
}
