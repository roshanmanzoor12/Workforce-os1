"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  ChannelRealtimeClient,
} from "@/lib/realtime/channel-realtime-client";

import {
  reduceChannelRealtimeEvent,
  type ChannelRealtimeViewState,
} from "@/lib/realtime/channel-event-reducer";

import {
  observeChannelRealtimeEvent,
} from "@/lib/realtime/channel-realtime-event-observer";
import {
  channelRealtimeService,
} from "@/services/channel-realtime.service";

import type {
  ChannelRealtimeConnectionState,
  ChannelRealtimeEvent,
} from "@/types/channel-realtime";

import type {
  WorkspaceChannelMessage,
} from "@/types/channels";


interface UseChannelRealtimeOptions {
  workspaceId: string | null;
  channelId: string | null;
  initialMessages?: WorkspaceChannelMessage[];
}


export function useChannelRealtime({
  workspaceId,
  channelId,
  initialMessages = [],
}: UseChannelRealtimeOptions) {
  const clientRef =
    useRef<
      ChannelRealtimeClient | null
    >(null);

  const [
    connectionState,
    setConnectionState,
  ] =
    useState<
      ChannelRealtimeConnectionState
    >(
      "idle",
    );

  const [
    state,
    setState,
  ] =
    useState<
      ChannelRealtimeViewState
    >({
      messages: initialMessages,
      typingUserIds: [],
      presenceByUserId: {},
      lastSequence: 0,
    });


  const applyEvent =
    useCallback(
      (
        event:
          ChannelRealtimeEvent,
      ) => {
        observeChannelRealtimeEvent(
          event,
        );


        setState(
          (current) =>
            reduceChannelRealtimeEvent(
              current,
              event,
            ),
        );
      },
      [],
    );


  useEffect(
    () => {
      setState(
        (current) => ({
          ...current,
          messages:
            initialMessages,
        }),
      );
    },
    [
      initialMessages,
    ],
  );


  useEffect(
    () => {
      if (
        !workspaceId
        || !channelId
      ) {
        return;
      }

      const client =
        new ChannelRealtimeClient({
          workspaceId,
          channelId,
          onEvent: applyEvent,
          onStateChange:
            setConnectionState,
        });

      clientRef.current =
        client;

      void client.connect();

      return () => {
        client.disconnect();

        if (
          clientRef.current
          === client
        ) {
          clientRef.current =
            null;
        }
      };
    },
    [
      workspaceId,
      channelId,
      applyEvent,
    ],
  );


  const typingStart =
    useCallback(
      () => {
        clientRef.current
          ?.typingStart();
      },
      [],
    );


  const typingStop =
    useCallback(
      () => {
        clientRef.current
          ?.typingStop();
      },
      [],
    );


  const resume =
    useCallback(
      async () => {
        if (
          !workspaceId
          || !channelId
          || state.lastSequence
          <= 0
        ) {
          return;
        }

        const page =
          await channelRealtimeService
            .resume(
              workspaceId,
              channelId,
              {
                after_sequence:
                  state.lastSequence,
                limit: 200,
              },
            );

        for (
          const event
          of page.items
        ) {
          applyEvent(
            event,
          );
        }
      },
      [
        workspaceId,
        channelId,
        state.lastSequence,
        applyEvent,
      ],
    );


  return {
    connectionState,
    messages:
      state.messages,
    typingUserIds:
      state.typingUserIds,
    presenceByUserId:
      state.presenceByUserId,
    lastSequence:
      state.lastSequence,
    typingStart,
    typingStop,
    resume,
  };
}
