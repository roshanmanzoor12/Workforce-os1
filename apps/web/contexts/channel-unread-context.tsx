"use client";

import {
  createContext,
  useContext,
  type ReactNode,
} from "react";

import {
  useWorkspaceChannelUnread,
} from "@/hooks/use-workspace-channel-unread";


interface ChannelUnreadContextValue {
  totalUnread: number;

  unreadByChannel:
    Record<
      string,
      number
    >;

  loading: boolean;

  error:
    | string
    | null;

  refresh:
    () => Promise<void>;

  setChannelUnread:
    (
      channelId: string,
      unreadCount: number,
    ) => void;
}


const ChannelUnreadContext =
  createContext<
    ChannelUnreadContextValue | null
  >(
    null,
  );


interface ChannelUnreadProviderProps {
  workspaceId:
    | string
    | null;

  children:
    ReactNode;
}


export function ChannelUnreadProvider({
  workspaceId,
  children,
}: ChannelUnreadProviderProps) {
  const {
    totalUnread,
    unreadByChannel,
    loading,
    error,
    refresh,
    setChannelUnread,
  } =
    useWorkspaceChannelUnread({
      workspaceId,
      enabled:
        Boolean(
          workspaceId,
        ),
    });


  return (
    <ChannelUnreadContext.Provider
      value={{
        totalUnread,
        unreadByChannel,
        loading,
        error,
        refresh,
        setChannelUnread,
      }}
    >
      {children}
    </ChannelUnreadContext.Provider>
  );
}


export function useChannelUnread() {
  const context =
    useContext(
      ChannelUnreadContext,
    );


  if (
    !context
  ) {
    throw new Error(
      "useChannelUnread must be used inside ChannelUnreadProvider.",
    );
  }


  return context;
}