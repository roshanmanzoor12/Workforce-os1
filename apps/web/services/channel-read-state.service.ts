import {
  api,
} from "@/lib/api/client";

import type {
  ChannelReadState,
  ChannelUnreadSummary,
  WorkspaceChannelUnreadListResponse,
} from "@/types/channel-read-state";


export const channelReadStateService = {
  getChannel(
    channelId: string,
  ) {
    return api.get<
      ChannelUnreadSummary
    >(
      `/workspace-channels/${channelId}/read-state`,
    );
  },


  listWorkspace(
    workspaceId: string,
  ) {
    return api.get<
      WorkspaceChannelUnreadListResponse
    >(
      `/workspace-channels/workspace/${workspaceId}/read-state`,
    );
  },


  markMessageRead(
    channelId: string,
    messageId: string,
  ) {
    return api.post<
      ChannelReadState
    >(
      `/workspace-channels/${channelId}/read/${messageId}`,
      {},
    );
  },


  markAllRead(
    channelId: string,
  ) {
    return api.post<
      ChannelReadState
    >(
      `/workspace-channels/${channelId}/read-all`,
      {},
    );
  },
};