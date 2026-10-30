import {
  api,
} from "@/lib/api/client";

import type {
  WorkspaceChannel,
  WorkspaceChannelCreatePayload,
  WorkspaceChannelMessage,
  WorkspaceChannelUpdatePayload,
} from "@/types/channels";


/* =========================================================
   CHANNELS
========================================================= */

async function list(
  workspaceId: string,
): Promise<WorkspaceChannel[]> {
  return api.get<WorkspaceChannel[]>(
    `/workspace-channels/workspace/${workspaceId}`,
  );
}


async function create(
  payload: WorkspaceChannelCreatePayload,
): Promise<WorkspaceChannel> {
  const name =
    payload.name.trim();


  if (
    !name
  ) {
    throw new Error(
      "Channel name is required.",
    );
  }


  return api.post<WorkspaceChannel>(
    "/workspace-channels",
    {
      workspace_id:
        payload.workspace_id,

      name,

      channel_type:
        payload.channel_type ??
        "text",
    },
  );
}


async function rename(
  channelId: string,

  payload: WorkspaceChannelUpdatePayload,
): Promise<WorkspaceChannel> {
  const name =
    payload.name.trim();


  if (
    !name
  ) {
    throw new Error(
      "Channel name is required.",
    );
  }


  return api.patch<WorkspaceChannel>(
    `/workspace-channels/${channelId}`,
    {
      name,
    },
  );
}


async function archive(
  channelId: string,
): Promise<void> {
  await api.delete<void>(
    `/workspace-channels/${channelId}`,
  );
}


/* =========================================================
   MESSAGES
========================================================= */

async function messages(
  channelId: string,

  limit =
    50,
): Promise<WorkspaceChannelMessage[]> {
  const normalizedLimit =
    Math.min(
      100,
      Math.max(
        1,
        limit,
      ),
    );


  return api.get<WorkspaceChannelMessage[]>(
    `/workspace-channels/${channelId}/messages`,
    {
      query: {
        limit:
          normalizedLimit,
      },
    },
  );
}


async function sendMessage(
  channelId: string,

  content: string,
): Promise<WorkspaceChannelMessage> {
  const normalized =
    content.trim();


  if (
    !normalized
  ) {
    throw new Error(
      "Message cannot be empty.",
    );
  }


  if (
    normalized.length >
    10000
  ) {
    throw new Error(
      "Message cannot exceed 10,000 characters.",
    );
  }


  return api.post<WorkspaceChannelMessage>(
    `/workspace-channels/${channelId}/messages`,
    {
      content:
        normalized,
    },
  );
}


/* =========================================================
   CONVENIENCE
========================================================= */

async function createTextChannel(
  workspaceId: string,

  name: string,
): Promise<WorkspaceChannel> {
  return create({
    workspace_id:
      workspaceId,

    name,

    channel_type:
      "text",
  });
}


async function createAnnouncementChannel(
  workspaceId: string,

  name: string,
): Promise<WorkspaceChannel> {
  return create({
    workspace_id:
      workspaceId,

    name,

    channel_type:
      "announcement",
  });
}


async function createVoiceChannel(
  workspaceId: string,

  name: string,
): Promise<WorkspaceChannel> {
  return create({
    workspace_id:
      workspaceId,

    name,

    channel_type:
      "voice",
  });
}


export const channelsService = {
  list,

  create,

  rename,

  archive,

  messages,

  sendMessage,

  createTextChannel,

  createAnnouncementChannel,

  createVoiceChannel,
};