"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  channelReadStateService,
} from "@/services/channel-read-state.service";

import type {
  WorkspaceChannelUnreadListResponse,
} from "@/types/channel-read-state";


interface UseWorkspaceChannelUnreadOptions {
  workspaceId:
    | string
    | null;

  enabled?: boolean;
}


export function useWorkspaceChannelUnread({
  workspaceId,
  enabled = true,
}: UseWorkspaceChannelUnreadOptions) {
  const [
    data,
    setData,
  ] =
    useState<
      WorkspaceChannelUnreadListResponse | null
    >(
      null,
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(
      null,
    );


  const refresh =
    useCallback(
      async () => {
        if (
          !workspaceId
          || !enabled
        ) {
          setData(
            null,
          );

          return;
        }


        try {
          setLoading(
            true,
          );

          setError(
            null,
          );


          const result =
            await channelReadStateService
              .listWorkspace(
                workspaceId,
              );


          setData(
            result,
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : (
                  "Unable to load unread channels."
                ),
          );

        } finally {
          setLoading(
            false,
          );
        }
      },
      [
        workspaceId,
        enabled,
      ],
    );


  useEffect(
    () => {
      void refresh();
    },
    [
      refresh,
    ],
  );


  const unreadByChannel =
    useMemo(
      () => {
        const map:
          Record<
            string,
            number
          > = {};


        for (
          const item
          of data?.channels
          ?? []
        ) {
          map[
            item.channel_id
          ] =
            item.unread_count;
        }


        return map;
      },
      [
        data,
      ],
    );


  const setChannelUnread =
    useCallback(
      (
        channelId: string,
        unreadCount: number,
      ) => {
        setData(
          (
            current,
          ) => {
            if (
              !current
            ) {
              return current;
            }


            const exists =
              current.channels
                .some(
                  (
                    item,
                  ) =>
                    item.channel_id
                    === channelId,
                );


            const channels =
              exists
                ? current.channels
                    .map(
                      (
                        item,
                      ) =>
                        item.channel_id
                        === channelId
                          ? {
                              ...item,

                              unread_count:
                                Math.max(
                                  0,
                                  unreadCount,
                                ),
                            }
                          : item,
                    )
                : [
                    ...current.channels,
                    {
                      channel_id:
                        channelId,

                      unread_count:
                        Math.max(
                          0,
                          unreadCount,
                        ),

                      last_read_message_id:
                        null,

                      last_read_at:
                        null,
                    },
                  ];


            const totalUnread =
              channels.reduce(
                (
                  total,
                  item,
                ) =>
                  total
                  + item.unread_count,
                0,
              );


            return {
              ...current,

              total_unread:
                totalUnread,

              channels,
            };
          },
        );
      },
      [],
    );


  return {
    data,
    loading,
    error,

    totalUnread:
      data?.total_unread
      ?? 0,

    unreadByChannel,

    refresh,
    setChannelUnread,
  };
}