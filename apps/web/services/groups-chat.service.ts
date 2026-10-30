import { api } from "@/lib/api/client";
import {
  socialChatService,
} from "@/services/social-chat.service";
import { chatFeaturesService } from "@/services/chat-features.service";
import { attachmentsService } from "@/services/attachments.service";

import type { ChatMessagePublic } from "@/types/social-chat";
import type { FeatureMessage } from "@/types/chat-features";
import type { BoundAttachmentResponse } from "@/types/attachments";

type GroupDetails = {
  current_user_id: string;
  description: string | null;
  avatar_url: string | null;
  can_manage: boolean;

  members: {
    user_id: string;
    name?: string | null;
    username?: string | null;
    avatar_url?: string | null;
    role: "owner" | "admin" | "member";
  }[];
};

type Message = ChatMessagePublic &
  Partial<Omit<FeatureMessage, keyof ChatMessagePublic>> & {
    attachments?: BoundAttachmentResponse[];
  };

const route = (id: string) =>
  `/chat/group-controls/${encodeURIComponent(id)}`;

const getGroupDetails = (id: string) =>
  api.get<GroupDetails>(route(id));

async function hydrate(
  id: string,
  message: Message,
): Promise<Message> {
  const result =
    await attachmentsService.listConversationAttachments(
      id,
      message.id,
    );

  return {
    ...message,
    attachments: result.attachments,
  };
}

async function listFeatureMessages(
  id: string,
): Promise<Message[]> {
  const items = await chatFeaturesService.listMessages(id);
  const result: Message[] = new Array(items.length);

  let cursor = 0;

  // Prevent a large burst of simultaneous attachment requests.
  await Promise.all(
    Array.from(
      { length: Math.min(4, items.length) },
      async () => {
        while (cursor < items.length) {
          const index = cursor++;
          const message = items[index];

          if (message === undefined) {
            throw new Error(
              "Message hydration index is out of range.",
            );
          }

          result[index] = await hydrate(
            id,
            message,
          );
        }
      },
    ),
  );

  return result;
}

async function listSharedFiles(
  id: string,
): Promise<BoundAttachmentResponse[]> {
  const result: BoundAttachmentResponse[] = [];

  for (let offset = 0; ; offset += 100) {
    const page = await api.get<BoundAttachmentResponse[]>(
      `${route(id)}/files`,
      {
        query: {
          offset,
          limit: 100,
        },
      },
    );

    result.push(...page);

    if (page.length < 100) {
      return result;
    }
  }
}

async function uploadMessageAttachment(
  id: string,
  file: File,
): Promise<Message> {
  const uploaded =
    await attachmentsService.uploadConversationFile(
      id,
      file,
    );

  // Create the message and bind the completed upload together.
  return api.post<Message>(
    `${route(id)}/attachment-messages`,
    {
      attachment_id: uploaded.attachment_id,
    },
  );
}

async function leaveGroup(id: string): Promise<void> {
  await api.post(
    `${route(id)}/leave`,
    {},
  );
}
export const groupsChatService = {
  ...socialChatService,

  getGroupDetails,
  listFeatureMessages,
  listSharedFiles,
  uploadMessageAttachment,
  leaveGroup,

  listConversationFeatures:
    chatFeaturesService.listConversationFeatures,

  markReadThrough:
    chatFeaturesService.markReadThrough,

  downloadAttachment:
    attachmentsService.createDownload,

  addMember:
    socialChatService.addGroupMember,

  removeMember:
    socialChatService.removeGroupMember,

  updateGroup: (
    id: string,
    body: {
      name: string;
      description: string;
    },
  ) =>
    api.patch<{ ok: boolean }>(
      route(id),
      body,
    ),

  updateMemberRole: (
    id: string,
    userId: string,
    role: "admin" | "member",
  ) =>
    api.patch<{ ok: boolean }>(
      `${route(id)}/members/${encodeURIComponent(userId)}/role`,
      { role },
    ),

  sendFeatureMessage: (
    id: string,
    body: {
      content: string;
      client_message_id: string;
      reply_to_message_id: string | null;
    },
  ): Promise<FeatureMessage> =>
    chatFeaturesService.sendMessage(
      id,
      body.content,
      {
        clientMessageId: body.client_message_id,
        replyToMessageId: body.reply_to_message_id,
      },
    ),

  setMessagePinned: (
    id: string,
    messageId: string,
    pinned: boolean,
  ) =>
    pinned
      ? chatFeaturesService.pinMessage(
          id,
          messageId,
        )
      : chatFeaturesService.unpinMessage(
          id,
          messageId,
        ),

  toggleReaction: (
    id: string,
    messageId: string,
    emoji: string,
  ): Promise<FeatureMessage> =>
    api.post<FeatureMessage>(
      `/chat/${encodeURIComponent(id)}/messages/${encodeURIComponent(messageId)}/reactions/toggle`,
      {
        emoji,
      },
    ),
};