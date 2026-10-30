"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

export default function GroupConversationRoute() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();

  useEffect(() => {
    if (id) {
      router.replace(
        `/messages?conversation=${encodeURIComponent(id)}`,
      );
    }
  }, [id, router]);

  return <p role="status">Opening group…</p>;
}