"use client";

import type {
  ReactNode,
} from "react";

import {
  ChannelUnreadProvider,
} from "@/contexts/channel-unread-context";


interface ChannelUnreadWorkspaceProviderProps {
  workspaceId:
    | string
    | null;

  children:
    ReactNode;
}


export function ChannelUnreadWorkspaceProvider({
  workspaceId,
  children,
}: ChannelUnreadWorkspaceProviderProps) {
  return (
    <ChannelUnreadProvider
      workspaceId={
        workspaceId
      }
    >
      {children}
    </ChannelUnreadProvider>
  );
}