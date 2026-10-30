"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

export default function MessageConversationRoute() {
  const router = useRouter();
  const { conversationId } = useParams<{
    conversationId: string;
  }>();

  useEffect(() => {
    if (conversationId) {
      router.replace(
        `/messages?conversation=${encodeURIComponent(conversationId)}`,
      );
    }
  }, [conversationId, router]);

  return <p role="status">Opening conversation…</p>;
}