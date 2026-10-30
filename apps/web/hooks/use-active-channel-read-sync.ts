"use client";

import {
  useCallback,
} from "react";

import {
  useChannelUnread,
} from "@/contexts/channel-unread-context";

import {
  channelReadStateService,
} from "@/services/channel-read-state.service";


interface UseActiveChannelReadSyncOptions {
  channelId:
    | string
    | null;
}


export function useActiveChannelReadSync({
  channelId,
}: UseActiveChannelReadSyncOptions) {
  const {
    setChannelUnread,
  } =
    useChannelUnread();


  const markRead =
    useCallback(
      async (
        messageId: string,
      ) => {
        if (
          !channelId
        ) {
          return;
        }


        const result =
          await channelReadStateService
            .markMessageRead(
              channelId,
              messageId,
            );


        setChannelUnread(
          channelId,
          result.unread_count,
        );
      },
      [
        channelId,
        setChannelUnread,
      ],
    );


  const markAllRead =
    useCallback(
      async () => {
        if (
          !channelId
        ) {
          return;
        }


        const result =
          await channelReadStateService
            .markAllRead(
              channelId,
            );


        setChannelUnread(
          channelId,
          result.unread_count,
        );
      },
      [
        channelId,
        setChannelUnread,
      ],
    );


  return {
    markRead,
    markAllRead,
  };
}