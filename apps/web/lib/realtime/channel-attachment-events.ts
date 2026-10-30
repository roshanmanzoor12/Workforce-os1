export const CHANNEL_ATTACHMENT_BOUND_EVENT =
  "workforce:channel-attachment-bound";


export interface ChannelAttachmentBoundPayload {
  channel_id: string;

  message_id: string;

  attachment_ids: string[];

  sequence?: number;
}


function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null
  );
}


function stringValue(
  value: unknown,
): string | null {
  if (
    typeof value !== "string"
  ) {
    return null;
  }


  const normalized =
    value.trim();


  return normalized
    ? normalized
    : null;
}


function stringArray(
  value: unknown,
): string[] {
  if (
    !Array.isArray(
      value,
    )
  ) {
    return [];
  }


  return value
    .filter(
      (
        item,
      ): item is string =>
        typeof item === "string",
    )
    .map(
      (item) =>
        item.trim(),
    )
    .filter(
      Boolean,
    );
}


function numberValue(
  value: unknown,
): number | undefined {
  if (
    typeof value !== "number" ||
    !Number.isFinite(
      value,
    )
  ) {
    return undefined;
  }


  return value;
}


export function parseChannelAttachmentBoundEvent(
  event: unknown,
): ChannelAttachmentBoundPayload | null {
  if (
    !isRecord(
      event,
    )
  ) {
    return null;
  }


  const eventType =
    stringValue(
      event.event_type,
    );


  if (
    eventType !==
    "channel.attachment.bound"
  ) {
    return null;
  }


  if (
    !isRecord(
      event.payload,
    )
  ) {
    return null;
  }


  const channelId =
    stringValue(
      event.payload.channel_id,
    );


  const messageId =
    stringValue(
      event.payload.message_id,
    );


  if (
    !channelId ||
    !messageId
  ) {
    return null;
  }


  return {
    channel_id:
      channelId,

    message_id:
      messageId,

    attachment_ids:
      stringArray(
        event.payload
          .attachment_ids,
      ),

    sequence:
      numberValue(
        event.sequence,
      ),
  };
}


export function publishChannelAttachmentBoundEvent(
  payload: ChannelAttachmentBoundPayload,
): void {
  if (
    typeof window ===
    "undefined"
  ) {
    return;
  }


  window.dispatchEvent(
    new CustomEvent<ChannelAttachmentBoundPayload>(
      CHANNEL_ATTACHMENT_BOUND_EVENT,
      {
        detail:
          payload,
      },
    ),
  );
}


export function forwardChannelAttachmentRealtimeEvent(
  event: unknown,
): boolean {
  const payload =
    parseChannelAttachmentBoundEvent(
      event,
    );


  if (
    payload === null
  ) {
    return false;
  }


  publishChannelAttachmentBoundEvent(
    payload,
  );


  return true;
}


export function subscribeToChannelAttachmentBound(
  listener: (
    payload: ChannelAttachmentBoundPayload,
  ) => void,
): () => void {
  if (
    typeof window ===
    "undefined"
  ) {
    return () => {};
  }


  const handler = (
    event: Event,
  ) => {
    if (
      !(
        event instanceof
        CustomEvent
      )
    ) {
      return;
    }


    const payload =
      event.detail as
        | ChannelAttachmentBoundPayload
        | undefined;


    if (
      !payload
    ) {
      return;
    }


    listener(
      payload,
    );
  };


  window.addEventListener(
    CHANNEL_ATTACHMENT_BOUND_EVENT,
    handler,
  );


  return () => {
    window.removeEventListener(
      CHANNEL_ATTACHMENT_BOUND_EVENT,
      handler,
    );
  };
}