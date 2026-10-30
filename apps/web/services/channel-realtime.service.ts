import {
  api,
} from "@/lib/api/client";

import type {
  ChannelRealtimeActionResponse,
  ChannelRealtimeEventPage,
  ChannelRealtimeResumeRequest,
  ChannelRealtimeTicketResponse,
} from "@/types/channel-realtime";


function basePath(
  workspaceId: string,
  channelId: string,
): string {
  return (
    `/workspaces/${workspaceId}` +
    `/channels/${channelId}` +
    "/realtime"
  );
}


export const channelRealtimeService = {
  createTicket(
    workspaceId: string,
    channelId: string,
  ) {
    return api.post<
      ChannelRealtimeTicketResponse
    >(
      `${basePath(
        workspaceId,
        channelId,
      )}/ticket`,
      {},
    );
  },


  resume(
    workspaceId: string,
    channelId: string,
    request: ChannelRealtimeResumeRequest,
  ) {
    return api.post<
      ChannelRealtimeEventPage
    >(
      `${basePath(
        workspaceId,
        channelId,
      )}/resume`,
      request,
    );
  },


  typingStart(
    workspaceId: string,
    channelId: string,
  ) {
    return api.post<
      ChannelRealtimeActionResponse
    >(
      `${basePath(
        workspaceId,
        channelId,
      )}/typing/start`,
      {},
    );
  },


  typingStop(
    workspaceId: string,
    channelId: string,
  ) {
    return api.post<
      ChannelRealtimeActionResponse
    >(
      `${basePath(
        workspaceId,
        channelId,
      )}/typing/stop`,
      {},
    );
  },


  heartbeat(
    workspaceId: string,
    channelId: string,
  ) {
    return api.post<
      ChannelRealtimeActionResponse
    >(
      `${basePath(
        workspaceId,
        channelId,
      )}/heartbeat`,
      {},
    );
  },
};