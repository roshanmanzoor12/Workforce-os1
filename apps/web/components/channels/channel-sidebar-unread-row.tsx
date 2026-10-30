"use client";

import {
  Hash,
  Megaphone,
  Volume2,
} from "lucide-react";

import {
  ChannelUnreadBadge,
} from "@/components/channels/channel-unread-badge";


export interface ChannelSidebarUnreadRowProps {
  id: string;

  name: string;

  type:
    | "text"
    | "announcement"
    | "voice";

  active?: boolean;

  unreadCount?: number;

  connectedVoice?: boolean;

  onSelect:
    (
      channelId: string,
    ) => void;
}


export function ChannelSidebarUnreadRow({
  id,
  name,
  type,
  active = false,
  unreadCount = 0,
  connectedVoice = false,
  onSelect,
}: ChannelSidebarUnreadRowProps) {
  const Icon =
    type === "voice"
      ? Volume2
      : type === "announcement"
        ? Megaphone
        : Hash;


  const hasUnread =
    unreadCount > 0;


  return (
    <button
      type="button"
      onClick={() => {
        onSelect(
          id,
        );
      }}
      className={`
        flex
        w-full
        items-center
        gap-2
        rounded-lg
        px-2.5
        py-2
        text-left
        text-sm
        transition
        ${
          active
            ? "bg-muted font-semibold"
            : (
                hasUnread
                  ? "font-semibold hover:bg-muted/60"
                  : "text-muted-foreground hover:bg-muted/60"
              )
        }
      `}
    >
      <Icon
        size={16}
        className="
          shrink-0
        "
      />


      <span
        className="
          min-w-0
          flex-1
          truncate
        "
      >
        {name}
      </span>


      {connectedVoice ? (
        <span
          title="Connected"
          aria-label="Voice connected"
          className="
            h-2
            w-2
            shrink-0
            rounded-full
            bg-emerald-500
          "
        />
      ) : null}


      <ChannelUnreadBadge
        count={
          unreadCount
        }
      />
    </button>
  );
}