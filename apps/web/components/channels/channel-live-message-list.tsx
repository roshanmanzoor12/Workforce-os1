"use client";

import {
  useEffect,
  useRef,
} from "react";

import {
  ChannelMessageItem,
} from "@/components/channels/channel-message-item";

import type {
  WorkspaceChannelMessage,
} from "@/types/channels";


interface ChannelLiveMessageListProps {
  channelId: string;

  currentUserId?:
    | string
    | null;

  messages:
    WorkspaceChannelMessage[];

  loading?: boolean;

  onVisibleLatest?:
    (
      message:
        WorkspaceChannelMessage,
    ) => void;
}


export function ChannelLiveMessageList({
  channelId,
  currentUserId = null,
  messages,
  loading = false,
  onVisibleLatest,
}: ChannelLiveMessageListProps) {
  const bottomRef =
    useRef<
      HTMLDivElement | null
    >(
      null,
    );


  const lastMessage =
    messages.length > 0
      ? messages[
          messages.length - 1
        ]
      : undefined;


  useEffect(
    () => {
      bottomRef.current
        ?.scrollIntoView({
          block:
            "end",

          behavior:
            "smooth",
        });


      if (
        lastMessage
      ) {
        onVisibleLatest?.(
          lastMessage,
        );
      }
    },
    [
      lastMessage,
      onVisibleLatest,
    ],
  );


  if (
    loading
  ) {
    return (
      <div
        className="
          flex
          flex-1
          items-center
          justify-center
          p-8
          text-sm
          text-muted-foreground
        "
      >
        Loading messages...
      </div>
    );
  }


  if (
    messages.length === 0
  ) {
    return (
      <div
        className="
          flex
          flex-1
          items-center
          justify-center
          p-8
          text-center
          text-sm
          text-muted-foreground
        "
      >
        No messages yet.
      </div>
    );
  }


  return (
    <div
      className="
        flex-1
        overflow-y-auto
        px-4
        py-3
      "
    >
      <div
        className="
          grid
          gap-2
        "
      >
        {messages.map(
          (
            message,
          ) => (
            <ChannelMessageItem
              key={
                message.id
              }
              channelId={
                channelId
              }
              message={
                message
              }
              currentUserId={
                currentUserId
              }
            />
          ),
        )}
      </div>


      <div
        ref={
          bottomRef
        }
      />
    </div>
  );
}
