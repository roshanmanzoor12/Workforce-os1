"use client";

import {
  Bell,
} from "lucide-react";

import {
  useChannelUnread,
} from "@/contexts/channel-unread-context";


export function ChannelUnreadSummary() {
  const {
    totalUnread,
    loading,
  } =
    useChannelUnread();


  if (
    loading
  ) {
    return null;
  }


  if (
    totalUnread <= 0
  ) {
    return null;
  }


  return (
    <div
      className="
        inline-flex
        items-center
        gap-1.5
        rounded-full
        border
        bg-muted/40
        px-2
        py-1
        text-xs
        font-medium
      "
      title={
        `${totalUnread} unread channel messages`
      }
    >
      <Bell
        size={13}
      />

      <span>
        {totalUnread}
      </span>
    </div>
  );
}