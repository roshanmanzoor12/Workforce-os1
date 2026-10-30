"use client";

import {
  useCallback,
} from "react";

import {
  useChannelUnread,
} from "@/contexts/channel-unread-context";

import type {
  ChannelRealtimeEvent,
} from "@/types/channel-realtime";


interface UseChannelUnreadRealtimeOptions {
  activeChannelId:
    | string
    | null;

  currentUserId:
    | string
    | null;
}


export function useChannelUnreadRealtime({
  activeChannelId,
  currentUserId,
}: UseChannelUnreadRealtimeOptions) {
  const {
    unreadByChannel,
    setChannelUnread,
    refresh,
  } =
    useChannelUnread();


  const onRealtimeEvent =
    useCallback(
      (
        event:
          ChannelRealtimeEvent,
      ) => {
        if (
          event.event_type
          !== "channel.message.created"
        ) {
          return;
        }


        if (
          currentUserId
          && event.actor_user_id
          === currentUserId
        ) {
          return;
        }


        if (
          event.channel_id
          === activeChannelId
        ) {
          setChannelUnread(
            event.channel_id,
            0,
          );

          return;
        }


        const current =
          unreadByChannel[
            event.channel_id
          ] ?? 0;


        setChannelUnread(
          event.channel_id,
          current + 1,
        );
      },
      [
        activeChannelId,
        currentUserId,
        unreadByChannel,
        setChannelUnread,
      ],
    );


  return {
    onRealtimeEvent,
    refreshUnread:
      refresh,
  };
}