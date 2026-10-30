"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  ChannelLiveMessageList,
} from "@/components/channels/channel-live-message-list";

import {
  ChannelMessageComposer,
} from "@/components/channels/channel-message-composer";

import {
  ChannelRealtimeStatus,
} from "@/components/channels/channel-realtime-status";

import {
  ChannelTypingIndicator,
} from "@/components/channels/channel-typing-indicator";

import {
  useChannelReadState,
} from "@/hooks/use-channel-read-state";

import {
  useChannelRealtime,
} from "@/hooks/use-channel-realtime";

import {
  channelMessagesService,
} from "@/services/channel-messages.service";

import type {
  WorkspaceChannelMessage,
} from "@/types/channels";


interface ChannelRealtimeRoomProps {
  workspaceId: string;

  channelId: string;

  channelName: string;

  currentUserId?:
    | string
    | null;
}


export function ChannelRealtimeRoom({
  workspaceId,
  channelId,
  channelName,
  currentUserId = null,
}: ChannelRealtimeRoomProps) {
  const [
    initialMessages,
    setInitialMessages,
  ] =
    useState<
      WorkspaceChannelMessage[]
    >(
      [],
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    sending,
    setSending,
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


  const {
    connectionState,

    messages,

    typingUserIds,

    typingStart,

    typingStop,

    resume,
  } =
    useChannelRealtime({
      workspaceId,
      channelId,
      initialMessages,
    });


  const {
    markMessageRead,
    markAllRead,
  } =
    useChannelReadState({
      channelId,
    });


  const loadMessages =
    useCallback(
      async () => {
        try {
          setLoading(
            true,
          );

          setError(
            null,
          );


          const result =
            await channelMessagesService.list(
              channelId,
              100,
            );


          setInitialMessages(
            result,
          );


          const latest =
            result[
              result.length - 1
            ];


          if (
            latest
          ) {
            await markMessageRead(
              latest.id,
            );

          } else {
            await markAllRead();
          }

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : (
                  "Unable to load channel messages."
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
        markMessageRead,
        markAllRead,
      ],
    );


  useEffect(
    () => {
      void loadMessages();
    },
    [
      loadMessages,
    ],
  );


  /*
   * Realtime replay is requested whenever
   * the socket returns to connected state.
   *
   * Backend sequence replay remains the
   * authority for missed committed events.
   */
  useEffect(
    () => {
      if (
        connectionState
        !== "connected"
      ) {
        return;
      }


      void resume();
    },
    [
      connectionState,
      resume,
    ],
  );


  async function sendMessage(
    content: string,
  ): Promise<void> {
    try {
      setSending(
        true,
      );

      setError(
        null,
      );


      await channelMessagesService.create(
        channelId,
        {
          content,
        },
      );


      /*
       * Do not optimistically insert the message.
       *
       * The committed backend event is delivered
       * through realtime. This prevents a REST
       * response + socket event from producing
       * duplicate rows in the room.
       */

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : (
              "Unable to send message."
            ),
      );

      throw cause;

    } finally {
      setSending(
        false,
      );
    }
  }


  return (
    <section
      className="
        flex
        h-full
        min-h-0
        flex-col
        bg-background
      "
    >
      <header
        className="
          flex
          items-center
          justify-between
          gap-3
          border-b
          px-4
          py-3
        "
      >
        <div
          className="
            min-w-0
          "
        >
          <div
            className="
              truncate
              font-semibold
            "
          >
            #
            {channelName}
          </div>

          <div
            className="
              text-xs
              text-muted-foreground
            "
          >
            Live workspace channel
          </div>
        </div>


        <ChannelRealtimeStatus
          state={
            connectionState
          }
        />
      </header>


      {error ? (
        <div
          className="
            border-b
            bg-destructive/5
            px-4
            py-2
            text-xs
            text-destructive
          "
        >
          {error}
        </div>
      ) : null}


      <ChannelLiveMessageList
        channelId={
          channelId
        }
        currentUserId={
          currentUserId
        }
        messages={
          messages
        }
        loading={
          loading
        }
        onVisibleLatest={(
          message,
        ) => {
          void markMessageRead(
            message.id,
          );
        }}
      />


      <div
        className="
          px-4
        "
      >
        <ChannelTypingIndicator
          typingUserIds={
            typingUserIds
          }
          currentUserId={
            currentUserId
          }
        />
      </div>


      <ChannelMessageComposer
        disabled={
          loading
        }
        submitting={
          sending
        }
        onSend={
          sendMessage
        }
        onTypingStart={
          typingStart
        }
        onTypingStop={
          typingStop
        }
      />
    </section>
  );
}