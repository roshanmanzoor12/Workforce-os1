import {
  api,
} from "@/lib/api/client";

import type {
  WorkspaceChannelMessage,
} from "@/types/channels";


export interface CreateChannelMessageRequest {
  content: string;
}


export interface UpdateChannelMessageRequest {
  content: string;
}


export const channelMessagesService = {
  list(
    channelId: string,
    limit = 100,
  ) {
    return api.get<
      WorkspaceChannelMessage[]
    >(
      `/workspace-channels/${channelId}/messages`,
      {
        query: {
          limit,
        },
      },
    );
  },


  create(
    channelId: string,
    request: CreateChannelMessageRequest,
  ) {
    return api.post<
      WorkspaceChannelMessage
    >(
      `/workspace-channels/${channelId}/messages`,
      request,
    );
  },


  update(
    channelId: string,
    messageId: string,
    request: UpdateChannelMessageRequest,
  ) {
    return api.patch<
      WorkspaceChannelMessage
    >(
      `/workspace-channels/${channelId}/messages/${messageId}`,
      request,
    );
  },


  remove(
    channelId: string,
    messageId: string,
  ) {
    return api.delete<void>(
      `/workspace-channels/${channelId}/messages/${messageId}`,
    );
  },
};