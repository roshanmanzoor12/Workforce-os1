"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  channelReadStateService,
} from "@/services/channel-read-state.service";

import type {
  ChannelUnreadSummary,
} from "@/types/channel-read-state";


interface UseChannelReadStateOptions {
  channelId:
    | string
    | null;

  enabled?: boolean;
}


export function useChannelReadState({
  channelId,
  enabled = true,
}: UseChannelReadStateOptions) {
  const [
    summary,
    setSummary,
  ] =
    useState<
      ChannelUnreadSummary | null
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
          !enabled
          || !channelId
        ) {
          setSummary(
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
              .getChannel(
                channelId,
              );


          setSummary(
            result,
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : (
                  "Unable to load channel read state."
                ),
          );

        } finally {
          setLoading(
            false,
          );
        }
      },
      [
        channelId,
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


  const markMessageRead =
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


        setSummary({
          channel_id:
            result.channel_id,

          unread_count:
            result.unread_count,

          last_read_message_id:
            result.last_read_message_id,

          last_read_at:
            result.last_read_at,
        });
      },
      [
        channelId,
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


        setSummary({
          channel_id:
            result.channel_id,

          unread_count:
            result.unread_count,

          last_read_message_id:
            result.last_read_message_id,

          last_read_at:
            result.last_read_at,
        });
      },
      [
        channelId,
      ],
    );


  return {
    summary,
    loading,
    error,
    refresh,
    markMessageRead,
    markAllRead,
  };
}