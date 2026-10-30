import {
  api,
} from "@/lib/api/client";

import type {
  AttachmentBindResponse,
  AttachmentCompleteRequest,
  AttachmentDownloadResponse,
  AttachmentPlanLimitResponse,
  AttachmentPrepareRequest,
  AttachmentPrepareResponse,
  AttachmentResponse,
  MessageAttachmentsResponse,
  UploadAttachmentResult,
} from "@/types/attachments";


function getContentType(
  file: File,
): string {
  const value =
    file.type.trim();


  if (
    value
  ) {
    return value;
  }


  return "application/octet-stream";
}


async function limits(): Promise<AttachmentPlanLimitResponse> {
  return api.get<AttachmentPlanLimitResponse>(
    "/attachments/limits",
  );
}


async function prepare(
  payload: AttachmentPrepareRequest,
): Promise<AttachmentPrepareResponse> {
  return api.post<AttachmentPrepareResponse>(
    "/attachments/prepare",
    payload,
  );
}


async function complete(
  attachmentId: string,

  payload: AttachmentCompleteRequest = {},
): Promise<AttachmentResponse> {
  return api.post<AttachmentResponse>(
    `/attachments/${attachmentId}/complete`,
    payload,
  );
}


async function get(
  attachmentId: string,
): Promise<AttachmentResponse> {
  return api.get<AttachmentResponse>(
    `/attachments/${attachmentId}`,
  );
}


async function remove(
  attachmentId: string,
): Promise<void> {
  await api.delete<void>(
    `/attachments/${attachmentId}`,
  );
}


async function createDownload(
  attachmentId: string,
): Promise<AttachmentDownloadResponse> {
  return api.post<AttachmentDownloadResponse>(
    `/attachments/${attachmentId}/download`,
    {},
  );
}


async function uploadRawFile(
  prepared: AttachmentPrepareResponse,

  file: File,
): Promise<void> {
  const response =
    await fetch(
      prepared.upload_url,
      {
        method:
          prepared.upload_method ??
          "PUT",

        headers: {
          "Content-Type":
            getContentType(
              file,
            ),
        },

        body:
          file,
      },
    );


  if (
    !response.ok
  ) {
    throw new Error(
      `File upload failed (${response.status}).`,
    );
  }
}


async function uploadConversationFile(
  conversationId: string,

  file: File,
): Promise<UploadAttachmentResult> {
  if (
    !conversationId
  ) {
    throw new Error(
      "Conversation ID is required.",
    );
  }


  if (
    file.size <=
    0
  ) {
    throw new Error(
      "Empty files cannot be uploaded.",
    );
  }


  const prepared =
    await prepare({
      scope:
        "CONVERSATION",

      conversation_id:
        conversationId,

      channel_id:
        null,

      filename:
        file.name,

      content_type:
        getContentType(
          file,
        ),

      size_bytes:
        file.size,
    });


  if (
    file.size >
    prepared.max_size_bytes
  ) {
    try {
      await remove(
        prepared.attachment_id,
      );
    } catch {
      // Best-effort cleanup.
    }


    throw new Error(
      "File exceeds the maximum attachment size.",
    );
  }


  try {
    await uploadRawFile(
      prepared,
      file,
    );


    const attachment =
      await complete(
        prepared.attachment_id,
        {
          checksum_sha256:
            null,
        },
      );


    return {
      attachment_id:
        prepared.attachment_id,

      attachment,
    };

  } catch (
    error
  ) {
    try {
      await remove(
        prepared.attachment_id,
      );
    } catch {
      // Best-effort cleanup.
    }


    throw error;
  }
}


async function uploadChannelFile(
  channelId: string,

  file: File,
): Promise<UploadAttachmentResult> {
  if (
    !channelId
  ) {
    throw new Error(
      "Channel ID is required.",
    );
  }


  if (
    file.size <=
    0
  ) {
    throw new Error(
      "Empty files cannot be uploaded.",
    );
  }


  const prepared =
    await prepare({
      scope:
        "CHANNEL",

      conversation_id:
        null,

      channel_id:
        channelId,

      filename:
        file.name,

      content_type:
        getContentType(
          file,
        ),

      size_bytes:
        file.size,
    });


  if (
    file.size >
    prepared.max_size_bytes
  ) {
    try {
      await remove(
        prepared.attachment_id,
      );
    } catch {
      // Best-effort cleanup.
    }


    throw new Error(
      "File exceeds the maximum attachment size.",
    );
  }


  try {
    await uploadRawFile(
      prepared,
      file,
    );


    const attachment =
      await complete(
        prepared.attachment_id,
        {
          checksum_sha256:
            null,
        },
      );


    return {
      attachment_id:
        prepared.attachment_id,

      attachment,
    };

  } catch (
    error
  ) {
    try {
      await remove(
        prepared.attachment_id,
      );
    } catch {
      // Best-effort cleanup.
    }


    throw error;
  }
}


async function bindConversationAttachments(
  conversationId: string,

  messageId: string,

  attachmentIds: string[],
): Promise<AttachmentBindResponse> {
  if (
    attachmentIds.length <
    1
  ) {
    throw new Error(
      "At least one attachment is required.",
    );
  }


  if (
    attachmentIds.length >
    10
  ) {
    throw new Error(
      "A maximum of 10 attachments can be bound to one message.",
    );
  }


  return api.post<AttachmentBindResponse>(
    `/chat/${conversationId}/messages/${messageId}/attachments`,
    {
      attachment_ids:
        attachmentIds,
    },
  );
}


async function listConversationAttachments(
  conversationId: string,

  messageId: string,
): Promise<MessageAttachmentsResponse> {
  return api.get<MessageAttachmentsResponse>(
    `/chat/${conversationId}/messages/${messageId}/attachments`,
  );
}


async function bindChannelAttachments(
  channelId: string,

  messageId: string,

  attachmentIds: string[],
): Promise<AttachmentBindResponse> {
  if (
    attachmentIds.length <
    1
  ) {
    throw new Error(
      "At least one attachment is required.",
    );
  }


  if (
    attachmentIds.length >
    10
  ) {
    throw new Error(
      "A maximum of 10 attachments can be bound to one message.",
    );
  }


  return api.post<AttachmentBindResponse>(
    `/workspace-channels/${channelId}/messages/${messageId}/attachments`,
    {
      attachment_ids:
        attachmentIds,
    },
  );
}


async function listChannelAttachments(
  channelId: string,

  messageId: string,
): Promise<MessageAttachmentsResponse> {
  return api.get<MessageAttachmentsResponse>(
    `/workspace-channels/${channelId}/messages/${messageId}/attachments`,
  );
}


async function openDownload(
  attachmentId: string,
): Promise<void> {
  const response = await createDownload(
    attachmentId,
  );

  const link = document.createElement("a");

  link.href = response.download_url;
  link.style.display = "none";
  link.setAttribute("download", "");

  document.body.appendChild(link);
  link.click();
  link.remove();
}


export const attachmentsService = {
  limits,

  prepare,

  complete,

  get,

  remove,

  createDownload,

  uploadConversationFile,

  uploadChannelFile,

  bindConversationAttachments,

  listConversationAttachments,

  bindChannelAttachments,

  listChannelAttachments,

  openDownload,
};