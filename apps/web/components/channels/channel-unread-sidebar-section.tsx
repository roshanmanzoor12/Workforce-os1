"use client";

import {
  useChannelUnread,
} from "@/contexts/channel-unread-context";

import {
  ChannelSidebarUnreadRow,
} from "@/components/channels/channel-sidebar-unread-row";

import type {
  WorkspaceChannel,
} from "@/types/channels";


interface ChannelUnreadSidebarSectionProps {
  channels:
    WorkspaceChannel[];

  selectedChannelId:
    | string
    | null;

  connectedVoiceChannelId?:
    | string
    | null;

  onSelect:
    (
      channelId: string,
    ) => void;
}


export function ChannelUnreadSidebarSection({
  channels,
  selectedChannelId,
  connectedVoiceChannelId = null,
  onSelect,
}: ChannelUnreadSidebarSectionProps) {
  const {
    unreadByChannel,
  } =
    useChannelUnread();


  return (
    <div
      className="
        grid
        gap-1
      "
    >
      {channels.map(
        (
          channel,
        ) => (
          <ChannelSidebarUnreadRow
            key={
              channel.id
            }
            id={
              channel.id
            }
            name={
              channel.name
            }
            type={
              channel.channel_type
            }
            active={
              selectedChannelId
              === channel.id
            }
            connectedVoice={
              connectedVoiceChannelId
              === channel.id
            }
            unreadCount={
              unreadByChannel[
                channel.id
              ] ?? 0
            }
            onSelect={
              onSelect
            }
          />
        ),
      )}
    </div>
  );
}