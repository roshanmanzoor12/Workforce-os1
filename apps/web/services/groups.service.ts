import { api } from "@/lib/api/client";

export type GroupsRequest = (
  path: string,
  init?: RequestInit,
) => Promise<unknown>;

let authenticatedRequest: GroupsRequest | null = (
  path,
  init,
) => api.request<unknown>(
  path.replace(/^\/api\/v1(?=\/|$)/, ""),
  init,
);

/**
 * Call once from your existing authenticated API-client module.
 *
 * The supplied function must:
 * - prepend the existing backend base URL;
 * - attach the current bearer token;
 * - preserve your token-refresh behavior;
 * - return parsed JSON;
 * - reject unsuccessful responses;
 * - support RequestInit.signal;
 * - handle empty/204 responses.
 *
 * Paths below already include /api/v1.
 */
export function configureGroupsRequest(request: GroupsRequest) {
  authenticatedRequest = request;
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  if (!authenticatedRequest) {
    throw new Error(
      "Groups authentication is not connected. Configure groups.service.ts with your existing authenticated HTTP client.",
    );
  }

  return (await authenticatedRequest(path, init)) as T;
}

function json(method: string, body?: unknown): RequestInit {
  return {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  };
}

function query(values: Record<string, string | number | undefined>) {
  const result = new URLSearchParams();

  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      result.set(key, String(value));
    }
  });

  const suffix = result.toString();

  return suffix ? `?${suffix}` : "";
}

export type Person = {
  user_id: string;
  name: string;
  avatar_url: string | null;
  online: boolean;
};

export type GroupMember = Person & {
  role: "owner" | "admin" | "member";
  joined_at: string;
};

export type GroupPreferences = {
  pinned: boolean;
  muted: boolean;
  archived: boolean;
  unread_count: number;
};

export type GroupRow = {
  id: string;
  name: string;
  description: string;
  created_by_user_id: string;
  creator_name: string;
  member_count: number;
  online_count: number;
  last_activity_at: string | null;
  avatar_members: Person[];
  preferences: GroupPreferences;
};

export type GroupDetail = GroupRow & {
  members: GroupMember[];
  shared_file_count: number;

  permissions: {
    can_edit_group: boolean;
    can_add_members: boolean;
    can_remove_members: boolean;
    can_manage_roles: boolean;
    can_leave: boolean;
  };
};

export type GroupSummary = {
  active_group_count: number;
  unread_message_count: number;
  online_member_count: number;
};

export type Attachment = {
  attachment_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  kind: "IMAGE" | "VIDEO" | "AUDIO" | "FILE";
  duration_ms?: number | null;
};

export type GroupMessage = {
  id: string;
  conversation_id: string;
  sender_user_id: string | null;
  sender: Person | null;
  content: string;
  message_type: "text" | "system" | "voice";
  created_at: string;
  edited_at: string | null;
  deleted_at: string | null;
  reply_to_message_id: string | null;

  reply: {
    id: string;
    sender_name: string;
    content: string;
  } | null;

  attachments: Attachment[];
  reactions: Record<string, number>;
  my_reactions: string[];
  pinned: boolean;

  /**
   * Explicit group receipt semantics.
   * Never infer a blue double check from ownership alone.
   */
  receipt_state: "sent" | "delivered" | "read";
};

export type Page<T> = {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
};

export type ComposeMessage = {
  client_message_id: string;
  content: string;
  reply_to_message_id: string | null;
  attachment_ids: string[];
  message_type: "text" | "voice";
  duration_ms: number | null;
};

export type CallParticipant = {
  user_id: string;
  state: "INVITED" | "JOINED" | "LEFT" | "DECLINED";
  microphone_enabled: boolean;
  camera_enabled: boolean;
  screen_share_state: string;
};

export type GroupCall = {
  id: string;
  conversation_id: string | null;
  started_by_user_id: string;
  kind: "VOICE" | "VIDEO";
  status: string;
  participants: CallParticipant[];
};

export type CallSignal = {
  id: string;
  sender_user_id: string;
  signal_type: "OFFER" | "ANSWER" | "ICE_CANDIDATE";
  payload: {
    media_slots?: Record<string, "microphone" | "camera" | "screen">;
    description?: RTCSessionDescriptionInit;
    candidate?: RTCIceCandidateInit;
  };
};

const chat = (id: string) =>
  `/api/v1/chat/${encodeURIComponent(id)}`;

const call = (id: string) =>
  `/api/v1/calls/${encodeURIComponent(id)}`;

export const groupsService = {
  // PROPOSED: enriched, paginated group list.
  listGroups(cursor?: string, signal?: AbortSignal) {
    return request<Page<GroupRow>>(
      `/api/v1/chat/groups${query({ cursor, limit: 100 })}`,
      { signal },
    );
  },

  // PROPOSED: authoritative aggregate counts.
  summary(signal?: AbortSignal) {
    return request<GroupSummary>(
      "/api/v1/chat/groups/summary",
      { signal },
    );
  },

  // PROPOSED: profiles, roles, permissions and totals.
  detail(id: string, signal?: AbortSignal) {
    return request<GroupDetail>(
      `${chat(id)}/group`,
      { signal },
    );
  },

  // PROPOSED: typed contact profiles for group invitations.
  contacts(signal?: AbortSignal) {
    return request<{ items: Person[] }>(
      "/api/v1/personal/social/contacts",
      { signal },
    );
  },

  // EXISTING.
  create(name: string, memberUserIds: string[]) {
    return request<{ id: string }>(
      "/api/v1/chat/groups",
      json("POST", {
        name,
        member_user_ids: memberUserIds,
      }),
    );
  },

  // PROPOSED.
  update(id: string, values: {
    name: string;
    description: string;
  }) {
    return request<GroupDetail>(
      `${chat(id)}/group`,
      json("PATCH", values),
    );
  },

  // EXISTING.
  preferences(
    id: string,
    values: Partial<Pick<
      GroupPreferences,
      "pinned" | "muted" | "archived"
    >>,
  ) {
    return request<GroupPreferences & { conversation_id: string }>(
      `${chat(id)}/preferences`,
      json("PATCH", values),
    );
  },

  // EXISTING.
  addMember(id: string, userId: string) {
    return request(
      `${chat(id)}/members/${encodeURIComponent(userId)}`,
      json("POST"),
    );
  },

  // EXISTING.
  removeMember(id: string, userId: string) {
    return request(
      `${chat(id)}/members/${encodeURIComponent(userId)}`,
      json("DELETE"),
    );
  },

  // PROPOSED.
  updateRole(
    id: string,
    userId: string,
    role: "admin" | "member",
  ) {
    return request(
      `${chat(id)}/members/${encodeURIComponent(userId)}/role`,
      json("PATCH", { role }),
    );
  },

  // PROPOSED: explicit leave/ownership rules.
  leave(id: string) {
    return request(`${chat(id)}/leave`, json("POST"));
  },

  // PROPOSED: rich cursor pagination.
  messages(
    id: string,
    cursor?: string,
    signal?: AbortSignal,
  ) {
    return request<Page<GroupMessage>>(
      `${chat(id)}/messages/features-page${query({
        cursor,
        limit: 50,
      })}`,
      { signal },
    );
  },

  /**
   * PROPOSED: atomic, idempotent message + attachment publication.
   * This prevents duplicate messages when attachment binding fails.
   */
  compose(id: string, values: ComposeMessage) {
    return request<GroupMessage>(
      `${chat(id)}/messages/compose`,
      json("POST", values),
    );
  },

  // EXISTING.
  editMessage(id: string, messageId: string, content: string) {
    return request(
      `${chat(id)}/messages/${encodeURIComponent(messageId)}`,
      json("PATCH", { content }),
    );
  },

  // EXISTING.
  deleteMessage(id: string, messageId: string) {
    return request(
      `${chat(id)}/messages/${encodeURIComponent(messageId)}`,
      json("DELETE"),
    );
  },

  // EXISTING.
  reaction(
    id: string,
    messageId: string,
    emoji: string,
    remove: boolean,
  ) {
    const path =
      `${chat(id)}/messages/${encodeURIComponent(messageId)}/reactions`;

    return remove
      ? request(`${path}/${encodeURIComponent(emoji)}`, json("DELETE"))
      : request(path, json("PUT", { emoji }));
  },

  // EXISTING.
  pinMessage(id: string, messageId: string, pinned: boolean) {
    return request(
      `${chat(id)}/messages/${encodeURIComponent(messageId)}/pin`,
      json(pinned ? "PUT" : "DELETE"),
    );
  },

  // EXISTING.
  readThrough(id: string, messageId: string) {
    return request(
      `${chat(id)}/read-through/${encodeURIComponent(messageId)}`,
      json("POST"),
    );
  },

  // PROPOSED: searches complete history, not only loaded messages.
  searchMessages(
    id: string,
    search: string,
    cursor?: string,
    signal?: AbortSignal,
  ) {
    return request<Page<GroupMessage>>(
      `${chat(id)}/messages/search${query({
        query: search,
        cursor,
        limit: 30,
      })}`,
      { signal },
    );
  },

  // EXISTING.
  typing(id: string, signal?: AbortSignal) {
    return request<{ user_ids: string[] }>(
      `/api/v1/chat/realtime/typing/${encodeURIComponent(id)}`,
      { signal },
    );
  },

  // EXISTING.
  setTyping(id: string, typing: boolean) {
    return request(
      `/api/v1/chat/realtime/typing/${encodeURIComponent(id)}/${
        typing ? "start" : "stop"
      }`,
      json("POST"),
    );
  },

  // PROPOSED: complete group file listing.
  files(id: string, cursor?: string, signal?: AbortSignal) {
    return request<Page<Attachment>>(
      `${chat(id)}/shared-files${query({ cursor, limit: 50 })}`,
      { signal },
    );
  },

  // EXISTING attachment APIs.
  async upload(
    conversationId: string,
    file: File,
  ): Promise<Attachment> {
    const limits = await request<{ max_size_bytes: number }>(
      "/api/v1/attachments/limits",
    );

    if (!file.size) {
      throw new Error("Empty files cannot be uploaded.");
    }

    if (file.size > limits.max_size_bytes) {
      throw new Error(
        `${file.name} exceeds your plan’s upload limit.`,
      );
    }

    const contentType =
      file.type || "application/octet-stream";

    const prepared = await request<{
      attachment_id: string;
      upload_url: string;
      upload_method: string;
      max_size_bytes: number;
    }>(
      "/api/v1/attachments/prepare",
      json("POST", {
        scope: "CONVERSATION",
        conversation_id: conversationId,
        filename: file.name,
        content_type: contentType,
        size_bytes: file.size,
      }),
    );

    if (file.size > prepared.max_size_bytes) {
      throw new Error("The upload exceeds the returned file limit.");
    }

    // Signed storage URL: do not attach the application's bearer token.
    const uploaded = await fetch(prepared.upload_url, {
      method: prepared.upload_method || "PUT",
      headers: { "Content-Type": contentType },
      body: file,
      credentials: "omit",
    });

    if (!uploaded.ok) {
      throw new Error(`Upload failed for ${file.name}. Please retry.`);
    }

    const completed = await request<{
      id: string;
      original_filename: string;
      content_type: string;
      size_bytes: number;
      kind: Attachment["kind"];
    }>(
      `/api/v1/attachments/${encodeURIComponent(
        prepared.attachment_id,
      )}/complete`,
      json("POST", {}),
    );

    return {
      attachment_id: completed.id,
      filename: completed.original_filename,
      content_type: completed.content_type,
      size_bytes: completed.size_bytes,
      kind: completed.kind,
    };
  },

  // EXISTING.
  download(attachmentId: string) {
    return request<{ download_url: string }>(
      `/api/v1/attachments/${encodeURIComponent(
        attachmentId,
      )}/download`,
      json("POST"),
    );
  },

  // EXISTING.
  deleteAttachment(attachmentId: string) {
    return request(
      `/api/v1/attachments/${encodeURIComponent(attachmentId)}`,
      json("DELETE"),
    );
  },

  // EXISTING.
  createCall(
    conversationId: string,
    kind: "VOICE" | "VIDEO",
    invitedUserIds: string[],
  ) {
    return request<GroupCall>(
      "/api/v1/calls",
      json("POST", {
        scope: "CONVERSATION",
        kind,
        conversation_id: conversationId,
        invited_user_ids: invitedUserIds,
      }),
    );
  },

  // PROPOSED: recover/discover active and invited calls.
  activeCalls(signal?: AbortSignal) {
    return request<{ items: GroupCall[] }>(
      "/api/v1/calls/active",
      { signal },
    );
  },

  // PROPOSED: authenticated, temporary ICE/TURN configuration.
  iceConfig() {
    return request<{ ice_servers: RTCIceServer[] }>(
      "/api/v1/calls/ice-config",
    );
  },

  // EXISTING.
  getCall(id: string) {
    return request<GroupCall>(call(id));
  },

  // EXISTING.
  joinCall(id: string) {
    return request(`${call(id)}/join`, json("POST"));
  },

  // EXISTING.
  leaveCall(id: string) {
    return request(`${call(id)}/leave`, json("POST"));
  },

  // EXISTING.
  endCall(id: string) {
    return request(`${call(id)}/end`, json("POST"));
  },

  // EXISTING.
  declineCall(id: string) {
    return request(`${call(id)}/decline`, json("POST"));
  },

  // EXISTING.
  heartbeat(id: string, connectionId: string) {
    return request(
      `${call(id)}/heartbeat`,
      json("POST", { connection_id: connectionId }),
    );
  },

  // EXISTING.
  mediaState(id: string, microphone: boolean, camera: boolean) {
    return request(
      `${call(id)}/media-state`,
      json("PATCH", {
        microphone_enabled: microphone,
        camera_enabled: camera,
      }),
    );
  },

  // EXISTING.
  screenState(id: string, sharing: boolean) {
    return request(
      `${call(id)}/screen-share/${sharing ? "start" : "stop"}`,
      json("POST"),
    );
  },

  // EXISTING: sending signals.
  signal(
    id: string,
    targetUserId: string,
    signalType: CallSignal["signal_type"],
    payload: CallSignal["payload"],
  ) {
    return request(
      `${call(id)}/signal`,
      json("POST", {
        target_user_id: targetUserId,
        signal_type: signalType,
        payload,
      }),
    );
  },

  /**
   * PROPOSED: receiving signals.
   *
   * This is an explicit REST inbox alternative to the unprovided
   * WebSocket contract. Do not add it if your existing realtime
   * transport already delivers these events; adapt that transport.
   */
  signals(id: string, cursor?: string, signal?: AbortSignal) {
    return request<{
      items: CallSignal[];
      next_cursor: string | null;
    }>(
      `${call(id)}/signals${query({ cursor })}`,
      { signal },
    );
  },
};