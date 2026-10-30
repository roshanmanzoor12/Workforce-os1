import type {
  ChannelRealtimeEvent,
} from "@/types/channel-realtime";

import type {
  WorkspaceChannelMessage,
} from "@/types/channels";


export interface ChannelRealtimeViewState {
  messages:
    WorkspaceChannelMessage[];

  typingUserIds:
    string[];

  presenceByUserId:
    Record<
      string,
      "online" | "idle" | "offline"
    >;

  lastSequence:
    number;
}


type RealtimeMessagePayload = {
  id:
    string;

  channel_id:
    string;

  sender_user_id:
    string | null;

  message_type:
    "text" | "system";

  content:
    string;

  edited_at:
    string | null;

  deleted_at:
    string | null;

  created_at:
    string;
};


type PresenceState =
  | "online"
  | "idle"
  | "offline";


function asRecord(
  value:
    unknown,
): Record<string, unknown> {
  if (
    value
    && typeof value === "object"
    && !Array.isArray(value)
  ) {
    return value as Record<
      string,
      unknown
    >;
  }

  return {};
}


function stringValue(
  value:
    unknown,
): string {
  return (
    typeof value === "string"
      ? value
      : ""
  );
}


function nullableStringValue(
  value:
    unknown,
): string | null {
  return (
    typeof value === "string"
      ? value
      : null
  );
}


function presenceValue(
  value:
    unknown,
): PresenceState | null {
  if (
    value === "online"
    || value === "idle"
    || value === "offline"
  ) {
    return value;
  }

  return null;
}


function messageFromPayload(
  value:
    unknown,
): WorkspaceChannelMessage | null {
  const payload =
    asRecord(
      value,
    );


  const id =
    stringValue(
      payload["id"],
    );

  const channelId =
    stringValue(
      payload["channel_id"],
    );

  const content =
    stringValue(
      payload["content"],
    );

  const createdAt =
    stringValue(
      payload["created_at"],
    );


  const rawMessageType =
    payload["message_type"];

  const messageType =
    rawMessageType === "system"
      ? "system"
      : "text";


  if (
    !id
    || !channelId
    || !createdAt
  ) {
    return null;
  }


  const message:
    RealtimeMessagePayload = {
      id,

      channel_id:
        channelId,

      sender_user_id:
        nullableStringValue(
          payload[
            "sender_user_id"
          ],
        ),

      message_type:
        messageType,

      content,

      edited_at:
        nullableStringValue(
          payload[
            "edited_at"
          ],
        ),

      deleted_at:
        nullableStringValue(
          payload[
            "deleted_at"
          ],
        ),

      created_at:
        createdAt,
    };


  return message;
}


function removeMessage(
  messages:
    WorkspaceChannelMessage[],

  messageId:
    string,
): WorkspaceChannelMessage[] {
  return messages.filter(
    (message) =>
      message.id
      !== messageId,
  );
}


function eventUserId(
  event:
    ChannelRealtimeEvent,
): string {
  const payload =
    asRecord(
      event.payload,
    );

  const payloadUserId =
    stringValue(
      payload["user_id"],
    );


  if (payloadUserId) {
    return payloadUserId;
  }


  if (
    typeof event.actor_user_id
    === "string"
  ) {
    return event.actor_user_id;
  }


  return "";
}


export function reduceChannelRealtimeEvent(
  state:
    ChannelRealtimeViewState,

  event:
    ChannelRealtimeEvent,
): ChannelRealtimeViewState {
  const nextSequence =
    Math.max(
      state.lastSequence,
      event.sequence,
    );


  // =====================================================
  // MESSAGE CREATED
  // =====================================================

  if (
    event.event_type
    === "channel.message.created"
  ) {
    const message =
      messageFromPayload(
        event.payload,
      );


    if (!message) {
      return {
        ...state,

        lastSequence:
          nextSequence,
      };
    }


    return {
      ...state,

      lastSequence:
        nextSequence,

      messages: [
        ...removeMessage(
          state.messages,
          message.id,
        ),

        message,
      ],
    };
  }


  // =====================================================
  // MESSAGE UPDATED
  // =====================================================

  if (
    event.event_type
    === "channel.message.updated"
  ) {
    const message =
      messageFromPayload(
        event.payload,
      );


    if (!message) {
      return {
        ...state,

        lastSequence:
          nextSequence,
      };
    }


    const exists =
      state.messages.some(
        (item) =>
          item.id
          === message.id,
      );


    return {
      ...state,

      lastSequence:
        nextSequence,

      messages:
        exists
          ? state.messages.map(
              (item) =>
                item.id
                === message.id
                  ? message
                  : item,
            )
          : [
              ...state.messages,
              message,
            ],
    };
  }


  // =====================================================
  // MESSAGE DELETED
  // =====================================================

  if (
    event.event_type
    === "channel.message.deleted"
  ) {
    const payload =
      asRecord(
        event.payload,
      );

    const messageId =
      stringValue(
        payload["id"],
      );


    if (!messageId) {
      return {
        ...state,

        lastSequence:
          nextSequence,
      };
    }


    return {
      ...state,

      lastSequence:
        nextSequence,

      messages:
        removeMessage(
          state.messages,
          messageId,
        ),
    };
  }


  // =====================================================
  // TYPING STARTED
  // =====================================================

  if (
    event.event_type
    === "channel.typing.started"
  ) {
    const userId =
      eventUserId(
        event,
      );


    if (!userId) {
      return {
        ...state,

        lastSequence:
          nextSequence,
      };
    }


    return {
      ...state,

      lastSequence:
        nextSequence,

      typingUserIds:
        Array.from(
          new Set([
            ...state.typingUserIds,
            userId,
          ]),
        ),
    };
  }


  // =====================================================
  // TYPING STOPPED
  // =====================================================

  if (
    event.event_type
    === "channel.typing.stopped"
  ) {
    const userId =
      eventUserId(
        event,
      );


    if (!userId) {
      return {
        ...state,

        lastSequence:
          nextSequence,
      };
    }


    return {
      ...state,

      lastSequence:
        nextSequence,

      typingUserIds:
        state.typingUserIds.filter(
          (item) =>
            item !== userId,
        ),
    };
  }


  // =====================================================
  // PRESENCE UPDATED
  // =====================================================

  if (
    event.event_type
    === "channel.presence.updated"
  ) {
    const payload =
      asRecord(
        event.payload,
      );


    const payloadUserId =
      stringValue(
        payload["user_id"],
      );


    const userId =
      payloadUserId
      || (
        typeof event.actor_user_id
        === "string"
          ? event.actor_user_id
          : ""
      );


    const presence =
      presenceValue(
        payload["state"],
      );


    if (
      !userId
      || !presence
    ) {
      return {
        ...state,

        lastSequence:
          nextSequence,
      };
    }


    return {
      ...state,

      lastSequence:
        nextSequence,

      presenceByUserId: {
        ...state.presenceByUserId,

        [userId]:
          presence,
      },
    };
  }


  // =====================================================
  // OTHER EVENTS
  // =====================================================

  return {
    ...state,

    lastSequence:
      nextSequence,
  };
}
